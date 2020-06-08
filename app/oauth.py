import json

from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session
import urllib
import requests



class StravaOauth():
    def __init__(self):
        # credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        # self.consumer_id = credentials['id']
        # self.consumer_secret = credentials['secret']
        self.consumer_id = 28599
        self.consumer_secret = '0b89acaaafd09735ed93707d135ebf3519bfbfd7'

    def authorize(self):
        return redirect(self.get_callback_url())

    def get_callback_url(self):
        params = {"client_id": self.consumer_id,
              "response_type": 'code',
              "redirect_uri": 'http://localhost:5000/login',
              "approval_prompt": "auto",
              "scope": "activity:read,profile:read_all"}
        url = "https://www.strava.com/oauth/authorize?" + urllib.parse.urlencode(params)
        return url

    def callback(self):
        code = request.args.get('code')
        access_token = self.get_token(code)
        # Note: In most cases, you'll want to store the access token, in, say,
        # a session for use in other parts of your web app.
        # return get_username(access_token)
        id = self.get_athlete_id(access_token)
        return id


    def get_token(self, code):
        post_data = {"grant_type": "authorization_code",
                     "client_id": 28599,
                     "client_secret": '0b89acaaafd09735ed93707d135ebf3519bfbfd7',
                     "code": code,
                     "redirect_uri": 'http://localhost:5000/login'}
        headers = self.base_headers()
        response = requests.post("https://www.strava.com/oauth/token",
                                 headers=headers,
                                 data=post_data)
        token_json = response.json()
        return token_json["access_token"]

    def get_athlete_id(self, access_token):
        headers = self.base_headers()
        headers.update({'Authorization': 'Bearer ' + access_token})
        url = "https://www.strava.com/api/v3/athlete"
        results = requests.get(url, headers=headers).json()
        id = results['id']
        print(f'!!!!!!!!!!!!!!! id {id}')
        return id

    def user_agent(self):
        '''reddit API clients should each have their own, unique user-agent
        Ideally, with contact info included.
        e.g.,
        '''
        user_age = request.headers.get('User-Agent')

        return "oauth2-sample-app by /u/%s" % user_age

    def base_headers(self):
        return {"User-Agent": self.user_agent()}