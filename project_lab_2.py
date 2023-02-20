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
import Datetime

def get_auth_header(my_bearer_token):
    return {"Authorization": f"Bearer {my_bearer_token}"}

def load_data_task_func(ti : TaskInstance, **kwargs):
    session = Session()

    # Get all user ids
    all_users = session.query(User).all()

    # get all tweets
    all_tweets = session.query(Tweet).all()

    ti.xcom_push("user_ids", all_users)
    ti.xcom_push("tweet_ids", all_tweets)

    session.close()

def call_api_task_func(ti : TaskInstance, **kwargs):
    all_users = ti.xcom_pull(key="user_ids", task_ids="load_data_task")
    all_tweets = ti.xcom_pull(key="tweet_ids", task_ids="load_data_task")

    # Pulls bearer token
    # bearer_token = Variable.get("Bearer Token")

    # Create authentication header
    auth_header = get_auth_header(bearer_token)

    user_stats = []
    tweet_stats = []
    new_tweets = []

    # Get updated stats for each user
    user_params = {'user.fields':'public_metrics,profile_image_url,username,description,id'}
    for user in all_users:
        id = user.twitter_user_id
        api_url = f"https://api.twitter.com/2/users/{id}"
        request = requests.get(api_url, headers=auth_header, params=user_params).json()
        user_stats.append(request)
        log.info(request)

        # Retrieve the latest tweets for each user
        tweet_params = {'tweet.fields':'public_metrics,author_id,text'}
        api_url = f"https://api.twitter.com/2/users/{id}/tweets"
        request = requests.get(api_url, headers=auth_header, params=tweet_params).json()
        new_tweets.append(request)
        log.info(request)


    # Retrieve every tweets updated stats
    tweet_params = {'tweet.fields':'public_metrics,author_id,text'}
    for tweet in all_tweets:
        id = tweet.tweet_id
        api_url = f"https://api.twitter.com/2/tweets/{id}"
        request = requests.get(api_url, headers=auth_header, params=tweet_params).json()
        tweet_stats.append(request)
        log.info(request)

    ti.xcom_push("user_stats", user_stats)
    ti.xcom_push("tweet_stats", tweet_stats)
    ti.xcom_push("new_tweets", new_tweets)



def transform_data_task_func(ti : TaskInstance, **kwargs):
    user_stats = ti.xcom_pull(key="user_stats", task_ids="call_api_task")
    tweet_stats = ti.xcom_pull(key="tweet_stats", task_ids="call_api_task")
    new_tweets = ti.xcom_pull(key="new_tweets", task_ids="new_tweets")
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


    # Transform tweet data
    tweet_stats_dta = []
    for item in tweet_stats:
        tweet_stats_dta.append([item])

    for item in new_tweets:
        tweet_stats_dta.append([item])
        
    tweet_requests_df = pd.DataFrame(tweet_stats_dta, columns=['data'])

    tweet_requests_df = pd.json_normalize(json.loads(tweet_requests_df.to_json(orient='records')))

    # Drop columns
    tweet_requests_df.drop(['data.data.edit_history_tweet_ids'], axis=1)

    # Rename
    tweet_requests_df = tweet_requests_df[['data.data.id','data.data.text','data.data.public_metrics.retweet_count','data.data.public_metrics.reply_count','data.data.public_metrics.like_count','data.data.public_metrics.quote_count','data.data.public_metrics.impression_count,','data.data.author_id']]
    tweet_requests_df.columns = ['tweet_id','text','retweet_count','reply_count','like_count','quote_count','impression_count', 'user_id']


    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jay_orten/airflow-cs280/auth/bucket_auth.json"

    client = storage.Client()
    bucket = client.get_bucket("j-o-apache-airflow-cs280")
    bucket.blob("data/user_data.csv").upload_from_string(user_requests_df.to_csv(index=False), "text/csv")
    bucket.blob("data/tweet_data.csv").upload_from_string(tweet_requests_df.to_csv(index=False), "text/csv")

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
    for row in user_data:
        user = User_Timeseries.create(
                        user_id=row.user_id,
                        followers_count=row.followers_count,
                        following_count=row.following_count,
                        tweet_count = row.tweet_count,
                        listed_count = row.listed_count,
                        date=Datetime.now()
                    )
        users.append(user)
    
    
    
    session.add_all(users)
    session.commit()

    tweets = []
    tweet_timeseries = []
    for row in tweet_data:
        tweet = Tweet_Timeseries.create(
                        tweet_id=row.tweet_id,
                        retweet_count=row.retweet_count,
                        favorite_count=row.like_count,
                        date=Datetime.now()
                )
        tweet_timeseries.append(tweet)
    
        # If this tweet hasn't been seen before, add it to the tweets table
        if session.query(~Tweet.query.filter(tweet_id=row.tweet_id).exists()).scalar():
            tweet = Tweet.create(
                        tweet_id=row.tweet_id,
                        user_id=row.user_id,
                        text=row.text,
                        created_at=Datetime.now()
                    )
            tweets.append(tweet)
    
    session.add_all(tweets)
    session.add_all(tweet_timeseries)
    session.commit()
            

    session.close()

with DAG(
    dag_id="project_lab_2_data_warehouse",
    schedule_interval="0 9 * * *",
    start_date=pendulum.datetime(2023, 2, 26, tz="US/Pacific"),
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
