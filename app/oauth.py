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
    AUTHORIZATION_GRANT = "authorization_code"
    REFRESH_GRANT = "refresh_token"
    TOKEN_URL = "https://www.strava.com/oauth/token"



    def __init__(self):
        # credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = current_app.config['CONSUMER_ID']
        self.consumer_secret = current_app.config['CONSUMER_SECRET']

    def authorize(self):
        return redirect(self.get_callback_url())

    def get_callback_url(self):
        params = {"client_id": self.consumer_id,
              "response_type": self.RESPONSE_TYPE,
              "redirect_uri": self.REDIRECT_URI,
              "approval_prompt": self.APPROVAL_PROMPT,
              "scope": self.SCOPE}
        url =  self.AUTHORIZATION_URL + urllib.parse.urlencode(params)
        return url

    def callback(self):
        code = request.args.get('code')
        print(f'Code = {code}')
        self.get_token(code)
        return


    def get_token(self, code):
        post_data = {"grant_type": self.AUTHORIZATION_GRANT,
                     "client_id": self.consumer_id,
                     "client_secret": self.consumer_secret,
                     "code": code,
                     "redirect_uri": self.REDIRECT_URI}
        headers = self.base_headers()
        response = requests.post(self.TOKEN_URL,
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


    def get_refresh_token(self, refresh_token):
        post_data = {"grant_type": self.REFRESH_GRANT,
                     "client_id": self.consumer_id,
                     "client_secret": self.consumer_secret,
                     "refresh_token": refresh_token}
        headers = self.base_headers()
        response = requests.post("https://www.strava.com/oauth/token",
                                 headers=headers,
                                 data=post_data)    

        refresh_json = response.json()
        print(f'Response: {refresh_json}')
        self.access_token = refresh_json['access_token']
        self.refresh_token = refresh_json['refresh_token']
        self.expires_at = refresh_json['expires_at']