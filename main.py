# coding: utf-8

import base64
import hashlib
import os
import sys
import re
import json
import requests
from requests_oauthlib import OAuth2Session

class TwitterHelper:
    def __init__(self, client_id, redirect_uri):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
    def authorize(self):
        scopes = ["bookmark.read", "bookmark.write", "tweet.read", "users.read", "offline.access"]
        
        code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
        code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

        code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
        code_challenge = code_challenge.replace("=", "")

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)

        auth_url = "https://twitter.com/i/oauth2/authorize"
        authorization_url, state = oauth.authorization_url(auth_url, code_challenge=code_challenge, code_challenge_method="S256")
        
        print("Visit the following URL to authorize your App on behalf of your Twitter handle in a browser:")
        print(authorization_url)

        authorization_response = input("Paste in the full URL after you've authorized your App:\n")
        
        token_url = "https://api.twitter.com/2/oauth2/token"

        auth = False

        token = oauth.fetch_token(token_url=token_url, authorization_response=authorization_response, auth=auth, client_id=client_id, include_client_id=True, code_verifier=code_verifier, )

        self.access = token["access_token"]
    def get_user(self):
        user_me = requests.request("GET", "https://api.twitter.com/2/users/me", headers={"Authorization": "Bearer {}".format(self.access)}, ).json()
        return user_me["data"]["id"]
    def get_bookmarks(self, user_id, max_results):
        url = "https://api.twitter.com/2/users/{}/bookmarks?max_results={}&expansions=attachments.media_keys&media.fields=url".format(user_id, max_results)
        headers = {"Authorization": "Bearer {}".format(self.access)}
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
        # print("Response code: {}".format(response.status_code))
        json_response = response.json()
        return json_response
        # print(json.dumps(json_response, indent=4, sort_keys=True))
    def del_bookmark(self, user_id, bookmarked_tweet_id):
        url = "https://api.twitter.com/2/users/{}/bookmarks/{}".format(user_id, bookmarked_tweet_id)
        headers = {"Authorization": "Bearer {}".format(self.access)}
        response = requests.request("DELETE", url, headers=headers)
        if response.status_code != 200:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
        return response.json()

client_id = os.environ.get('TWITTER_CLIENT_ID')
redirect_uri = os.environ.get('TWITTER_REDIRECT_URI')

if client_id == None or redirect_uri == None:
    print('You must set TWITTER_CLIENT_ID and TWITTER_REDIRECT_URI')
    sys.exit(0)
    
twitter = TwitterHelper(client_id=client_id, redirect_uri=redirect_uri,)
twitter.authorize()
user_id = twitter.get_user()

bookmarks = twitter.get_bookmarks(user_id, max_results=3)
print(json.dumps(bookmarks, indent=4, sort_keys=True))

for media in bookmarks['includes']['media']:
    img_name = media['url'].split('/')[-1]
    img_content = requests.get(media['url']).content
    with open(img_name, 'wb') as file:
        file.write(img_content)

for tweet_data in bookmarks['data']:
    result_json = twitter.del_bookmark(user_id, tweet_data['id'])
    print(json.dumps(result_json, indent=4, sort_keys=True))

