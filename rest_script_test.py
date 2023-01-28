import requests

def get_auth_header():
	my_bearer_token = ""
	return {"Authorization": f"Bearer {my_bearer_token}"}

tweet_params = {'tweet.fields':'public_metrics,author_id,text'}
tweet_id = "1618838236574679040"
api_url = f"https://api.twitter.com/2/tweets/{tweet_id}"
request = requests.get(api_url, headers=get_auth_header(), params=tweet_params)
print(request.json())