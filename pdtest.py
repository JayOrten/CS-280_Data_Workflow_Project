import pandas as pd
import json
from pandas import json_normalize

data = [{'data': {'profile_image_url': 'https://pbs.twimg.com/profile_images/1590968738358079488/IY9Gx6Ok_normal.jpg', 'username': 'elonmusk', 'id': '44196397', 'public_metrics': {'followers_count': 127517933, 'following_count': 176, 'tweet_count': 22406, 'listed_count': 113679}, 'description': '', 'name': 'Mr. Tweet'}}, {'data': {'id': '62513246', 'name': 'J.K. Rowling', 'public_metrics': {'followers_count': 14001802, 'following_count': 1070, 'tweet_count': 15789, 'listed_count': 32160}, 'description': 'Writer sometimes known as Robert Galbraith', 'profile_image_url': 'https://pbs.twimg.com/profile_images/1616880795737620480/mciTd7RT_normal.jpg', 'username': 'jk_rowling'}}, {'data': {'username': 'NASA', 'id': '11348282', 'description': "There's space for everybody. ✨", 'profile_image_url': 'https://pbs.twimg.com/profile_images/1321163587679784960/0ZxKlEKB_normal.jpg', 'name': 'NASA', 'public_metrics': {'followers_count': 70235170, 'following_count': 181, 'tweet_count': 69432, 'listed_count': 99667}}}, {'data': {'id': '29873662', 'name': 'Marques Brownlee', 'profile_image_url': 'https://pbs.twimg.com/profile_images/1468001914302390278/B_Xv_8gu_normal.jpg', 'username': 'MKBHD', 'public_metrics': {'followers_count': 6035546, 'following_count': 439, 'tweet_count': 53770, 'listed_count': 14198}, 'description': 'Web Video Producer | ⋈ | Pro Ultimate Frisbee Player | Host of @WVFRM @TheStudio'}}, {'data': {'name': 'Bill Gates', 'public_metrics': {'followers_count': 61964391, 'following_count': 535, 'tweet_count': 4155, 'listed_count': 121502}, 'username': 'BillGates', 'id': '50393960', 'profile_image_url': 'https://pbs.twimg.com/profile_images/1564398871996174336/M-hffw5a_normal.jpg', 'description': "Sharing things I'm learning through my foundation work and other interests."}}]

data_dta = []
for item in data:
  data_dta.append([item])
    
df = pd.DataFrame(data_dta, columns=['data'])

df = pd.json_normalize(json.loads(df.to_json(orient='records')))

# Drop columns
df = df.drop(df.columns[[0,7]], axis=1)

# Rename
df.columns = ['username','user_id','followers_count','following_count','tweet_count','listed_count','name']

print(df.head())