from airflow import DAG
import logging as log
import pendulum
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from airflow.models import TaskInstance

def get_auth_header(my_bearer_token):
	return {"Authorization": f"Bearer {my_bearer_token}"}

def get_twitter_api_data_task_func(ti: TaskInstance, **kwargs):
	# Pulls bearer token
	print("test")
	bearer_token = Variable.get("Bearer Token")

	# Create authentication header
	auth_header = get_auth_header(bearer_token)

	user_requests = []
	tweet_requests = []

	# For every single userID and tweetID:

	# User Requests:
	user_ids = Variable.get("TWITTER_USER_IDS", deserialize_json=True)
	tweet_ids = Variable.get("TWITTER_TWEET_IDS", deserialize_json=True)

	user_params = {'user.fields':'public_metrics,profile_image_url,username,description,id'}
	for id in user_ids:
		api_url = f"https://api.twitter.com/2/users/{id}"
		request = requests.get(api_url, headers=auth_header, params=user_params)
		user_requests.append(request)
		logging.info(request)

	# Tweet Requests:

	tweet_params = {'tweet.fields':'public_metrics,author_id,test'}
	for id in tweet_ids:
		api_url = f"https://api.twitter.com/2/tweets/{id}"
		request = requests.get(api_url, headers=auth_header, params=tweet_params)
		tweet_requests.append(request)
		logging.info(request)

	# Push data to next task in two seperate lists
	ti.xcom_push("user_requests", user_requests)
	ti.xcom_push("tweet_requests", tweet_requests)


def my_task_func_2(ti: TaskInstance, **kwargs):
	my_list = ti.xcom_pull(key="i_love_ds", task_ids="my_dummy_task")
	logging.info(my_list)
	# should log the list to this task's log.
	return

with DAG(
    dag_id="project_lab_1_etl",
    schedule_interval="0 9 * * *",
    start_date=pendulum.datetime(2023, 1, 1, tz="US/Pacific"),
    catchup=False,
) as dag:
	start_task = DummyOperator(task_id="start_task")
	get_twitter_api_data_task = PythonOperator(
		task_id="get_twitter_api_data_task",
		python_callable = get_twitter_api_data_task_func,
		provide_context=True
		)
	my_task_two = PythonOperator(
		task_id="my_dummy_task_2",
		python_callable=my_task_func_2,
		provide_context=True
		)
	end_task = DummyOperator(task_id="end_task")


start_task >> get_twitter_api_data_task >> my_task_two >> end_task
