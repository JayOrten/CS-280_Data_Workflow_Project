from airflow import DAG
import logging as log
import pendulum
import requests
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from airflow.models import TaskInstance
import pandas as pd
import json
from google.cloud import storage
from gcsfs import GCSFileSystem
import os


from models.config import Session #You would import this from your config file
from models.users_model import User
from models.tweet_model import Tweet
from models.tweet_timeseries_model import Tweet_Timeseries
from models.user_timeseries_model import User_Timeseries
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float

def get_auth_header(my_bearer_token):
    return {"Authorization": f"Bearer {my_bearer_token}"}

def load_data_task_func(ti : TaskInstance, **kwargs):
    session = Session()

    # Get all user ids
    all_users = session.query(User).all()

    # get all tweets
    all_tweets = session.query(Tweet).all()

    user_ids = []
    tweet_ids = []

    for user in all_users:
        user_ids.append(user.user_id)

    for tweet in all_tweets:
        tweet_ids.append(tweet.tweet_id)

    ti.xcom_push("user_ids", user_ids)
    ti.xcom_push("tweet_ids", tweet_ids)

    session.close()

def call_api_task_func(ti : TaskInstance, **kwargs):
    user_ids = ti.xcom_pull(key="user_ids", task_ids="load_data_task")
    tweet_ids = ti.xcom_pull(key="tweet_ids", task_ids="load_data_task")

    # Pulls bearer token
    bearer_token = Variable.get("Bearer Token")

    # Create authentication header
    auth_header = get_auth_header(bearer_token)

    user_stats = []
    tweet_stats = []
    new_tweets = []

    # Get updated stats for each user
    user_params = {'user.fields':'public_metrics,profile_image_url,username,description,id'}
    for id in user_ids:
        api_url = f"https://api.twitter.com/2/users/{id}"
        request = requests.get(api_url, headers=auth_header, params=user_params).json()
        user_stats.append(request)
        log.info('user_stats request: ',request)

        # Retrieve the latest tweets for each user
        tweet_params = {'tweet.fields':'public_metrics,author_id,text'}
        api_url = f"https://api.twitter.com/2/users/{id}/tweets"
        request = requests.get(api_url, headers=auth_header, params=tweet_params).json()
        new_tweets.append(request)
        log.info('new_tweets request: ', request)


    # Retrieve every tweets updated stats
    tweet_params = {'tweet.fields':'public_metrics,author_id,text'}
    for id in tweet_ids:
        api_url = f"https://api.twitter.com/2/tweets/{id}"
        request = requests.get(api_url, headers=auth_header, params=tweet_params).json()
        tweet_stats.append(request)
        log.info('tweet_stats request: ', request)

    ti.xcom_push("user_stats", user_stats)
    ti.xcom_push("tweet_stats", tweet_stats)
    ti.xcom_push("new_tweets", new_tweets)



def transform_data_task_func(ti : TaskInstance, **kwargs):
    user_stats = ti.xcom_pull(key="user_stats", task_ids="call_api_task")
    tweet_stats = ti.xcom_pull(key="tweet_stats", task_ids="call_api_task")
    new_tweets = ti.xcom_pull(key="new_tweets", task_ids="call_api_task")
    print(user_stats)
    print(tweet_stats)
    print(new_tweets)

    # Transform user data
    user_requests_dta = []
    for item in user_stats:
        user_requests_dta.append([item])
        
    user_requests_df = pd.DataFrame(user_requests_dta, columns=['data'])

    user_requests_df = pd.json_normalize(json.loads(user_requests_df.to_json(orient='records')))

    # Drop columns
    user_requests_df.drop(['data.data.profile_image_url', 'data.data.description'], axis=1)

    # Rename
    user_requests_df = user_requests_df[['data.data.id','data.data.username','data.data.name','data.data.public_metrics.followers_count','data.data.public_metrics.following_count','data.data.public_metrics.tweet_count','data.data.public_metrics.listed_count']]
    user_requests_df.columns = ['user_id','username','name','followers_count','following_count','tweet_count','listed_count']


    # Transform tweet stats data
    tweet_stats_dta = []
    for item in tweet_stats:
        tweet_stats_dta.append([item])

    if tweet_stats_dta:
        tweet_stats_df = pd.DataFrame(tweet_stats_dta, columns=['data'])

        tweet_stats_df = pd.json_normalize(json.loads(tweet_stats_df.to_json(orient='records')))

        # Drop columns
        tweet_stats_df.drop(['data.data.edit_history_tweet_ids'], axis=1)

        # Rename
        tweet_stats_df = tweet_stats_df[['data.data.id','data.data.text','data.data.public_metrics.retweet_count','data.data.public_metrics.reply_count','data.data.public_metrics.like_count','data.data.public_metrics.quote_count','data.data.public_metrics.impression_count','data.data.author_id']]
        tweet_stats_df.columns = ['tweet_id','text','retweet_count','reply_count','like_count','quote_count','impression_count', 'user_id']

    
    # Transform new tweets data
    new_tweets_dta = []
    for item in new_tweets:
        new_tweets_dta.append(item['data'])

    flattened = sum(new_tweets_dta, [])

    new_tweets_df = pd.DataFrame(flattened)

    new_tweets_df = pd.json_normalize(json.loads(new_tweets_df.to_json(orient='records')))

    # Drop columns
    new_tweets_df.drop(['edit_history_tweet_ids'], axis=1)

    # Rename
    new_tweets_df = new_tweets_df[['id','text','public_metrics.retweet_count','public_metrics.reply_count','public_metrics.like_count','public_metrics.quote_count','public_metrics.impression_count','author_id']]
    new_tweets_df.columns = ['tweet_id','text','retweet_count','reply_count','like_count','quote_count','impression_count', 'user_id']

    # Combine
    if tweet_stats_dta:
        combined = pd.concat([tweet_stats_df,new_tweets_df])
    else:
        combined = new_tweets_df

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jay_orten/airflow-cs280/auth/bucket_auth.json"

    client = storage.Client()
    bucket = client.get_bucket("j-o-apache-airflow-cs280")
    bucket.blob("data/user_data.csv").upload_from_string(user_requests_df.to_csv(index=False), "text/csv")
    bucket.blob("data/tweet_data.csv").upload_from_string(combined.to_csv(index=False), "text/csv")

    return

def write_data_task_func(ti : TaskInstance, **kwargs):
    # Get data from bucket
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jay_orten/airflow-cs280/auth/bucket_auth.json"

    fs = GCSFileSystem(project="Jay-Orten-CS-280")
    with fs.open('gs://j-o-apache-airflow-cs280/data/tweet_data.csv', 'rb') as f:
        tweet_data = pd.read_csv(f)

    with fs.open('gs://j-o-apache-airflow-cs280/data/user_data.csv', 'rb') as f:
        user_data = pd.read_csv(f)

    session = Session()

    users = []
    # Read the data from the csvs and upload to database
    for _, row in user_data.iterrows():
        if pd.isna(row.user_id):
            print("NOT A NUMBER")
            continue
        user = User_Timeseries(
                        user_id=row.user_id,
                        followers_count=row.followers_count,
                        following_count=row.following_count,
                        tweet_count = row.tweet_count,
                        listed_count = row.listed_count,
                        date=datetime.now()
                    )
        users.append(user)
    
    session.add_all(users)
    session.commit()

    tweets = []
    tweet_timeseries = []
    for _, row in tweet_data.iterrows():
        if pd.isna(row.tweet_id):
            print("NOT A NUMBER")
            continue
        tweet = Tweet_Timeseries(
                        tweet_id=row.tweet_id,
                        retweet_count=row.retweet_count,
                        favorite_count=row.like_count,
                        date=datetime.now()
                )
        tweet_timeseries.append(tweet)
    
        # If this tweet hasn't been seen before, add it to the tweets table
        if not session.query(session.query(Tweet).filter(Tweet.tweet_id==row.tweet_id).exists()).scalar():
            tweet = Tweet(
                        tweet_id=row.tweet_id,
                        user_id=row.user_id,
                        text=row.text,
                        created_at=datetime.now()
                    )
            tweets.append(tweet)
    
    session.add_all(tweets)
    session.add_all(tweet_timeseries)
    session.commit()
            

    session.close()

with DAG(
    dag_id="project_lab_2_data_warehouse",
    schedule_interval="0 9 * * *",
    start_date=pendulum.datetime(2023, 2, 19, tz="US/Pacific"),
    catchup=False,
) as dag:
    load_data_task = PythonOperator(
        task_id="load_data_task",
        python_callable = load_data_task_func,
        provide_context=True
        )
    call_api_task = PythonOperator(
        task_id="call_api_task",
        python_callable=call_api_task_func,
        provide_context=True
        )
    transform_data_task = PythonOperator(
        task_id="transform_data_task",
        python_callable=transform_data_task_func,
        provide_context=True
        )
    write_data_task = PythonOperator(
        task_id="write_data_task",
        python_callable=write_data_task_func,
        provide_context=True
    )


load_data_task >> call_api_task >> transform_data_task >> write_data_task
