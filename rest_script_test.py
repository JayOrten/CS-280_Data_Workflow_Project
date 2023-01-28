import requests

def get_auth_header():
	my_bearer_token = ""
	return {"Authorization": f"Bearer {my_bearer_token}"}

user_id = "44196397"
api_url = f"https://api.twitter.com/2/users/{user_id}"
request = requests.get(api_url, headers=get_auth_header())
print(request.json())
