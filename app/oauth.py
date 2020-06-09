import json
from flask import current_app, url_for, request, redirect, session
import urllib
import requests



class StravaOauth():
    REDIRECT_URI = 'http://localhost:5000/login'
    RESPONSE_TYPE = 'code'
    APPROVAL_PROMPT = "auto"
    SCOPE = "activity:read,profile:read_all"
    AUTHORIZATION_URL = "https://www.strava.com/oauth/authorize?"
    GRANT_TYPE = "authorization_code"
    TOKEN_URL = "https://www.strava.com/oauth/token"



    def __init__(self):
        # credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = current_app.config['CONSUMER_ID']
        self.consumer_secret = current_app.config['CONSUMER_SECRET']

    def authorize(self):
        return redirect(self.get_callback_url())

    def get_callback_url(self):
        params = {"client_id": self.consumer_id,
              "response_type": RESPONSE_TYPE,
              "redirect_uri": REDIRECT_URI,
              "approval_prompt": APPROVAL_PROMPT,
              "scope": SCOPE}
        url =  AUTHORIZATION_URL + urllib.parse.urlencode(params)
        return url

    def callback(self):
        code = request.args.get('code')
        self.get_token(code)
        return


    def get_token(self, code):
        post_data = {"grant_type": GRANT_TYPE,
                     "client_id": self.consumer_id,
                     "client_secret": self.consumer_secret,
                     "code": RESPONSE_TYPE,
                     "redirect_uri": REDIRECT_URI}
        headers = self.base_headers()
        response = requests.post(TOKEN_URL,
                                 headers=headers,
                                 data=post_data)
        token_json = response.json()
        print(f'token_json {token_json}')
        self.access_token = token_json["access_token"]
        self.expires_at = token_json['expires_at']
        self.refresh_token = token_json['refresh_token']
        self.social_id = token_json['athlete']['id']
        return 

    def get_athlete_id(self):
        headers = self.base_headers()
        headers.update({'Authorization': 'Bearer ' + self.access_token})
        url = "https://www.strava.com/api/v3/athlete"
        results = requests.get(url, headers=headers).json()
        id = results['id']
        return id

    def user_agent(self):
        user_age = request.headers.get('User-Agent')
        return "oauth2-sample-app by /u/%s" % user_age

    def base_headers(self):
        return {"User-Agent": self.user_agent()}


    def get_refresh_token():
        post_data = {"grant_type": "refresh_token",
                     "client_id": 28599,
                     "client_secret": '0b89acaaafd09735ed93707d135ebf3519bfbfd7',
                     "refresh_token": user.refresh_token}
        headers = self.base_headers()
        response = requests.post("https://www.strava.com/oauth/token",
                                 headers=headers,
                                 data=post_data)    

        self.access_token = response['access_token']
        self.refresh_token = response['response_token']
        self.expires_at = response['expires_at']