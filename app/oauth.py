from flask import current_app, url_for, request, redirect, session
import urllib
import requests

class Token:
    def __init__(self, access_token, refresh_token, social_id, expires_at):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.social_id = social_id
        self.expires_at = expires_at


class StravaOauth:
    #TODO: import REDIRECT_URI from config.py
    # Heroku redirect
    # REDIRECT_URI = 'http://nhhighpeaks.herokuapp.com/login'
    # Local redirect
    REDIRECT_URI = 'http://localhost:5000/login'
    # REDIRECT_URI = 'https://www.nhhighpeaks.com/login'
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
        self.access_token = None
        self.expires_at = None
        self.refresh_token = None
        self.social_id = None

    def authorize(self):
        callback_url = self.get_callback_url()
        return redirect(callback_url)

    def get_callback_url(self):
        params = {"client_id": self.consumer_id,
              "response_type": self.RESPONSE_TYPE,
              "redirect_uri": self.REDIRECT_URI,
              "approval_prompt": self.APPROVAL_PROMPT,
              "scope": self.SCOPE}
        url = self.AUTHORIZATION_URL + urllib.parse.urlencode(params)
        return url

    def callback(self):
        code = request.args.get('code')
        print(f'Code = {code}')
        return code


    def get_token(self, code):
        print(f'Grant_type {self.AUTHORIZATION_GRANT},'
             f'client_id {self.consumer_id},'
             f'client_secret {self.consumer_secret},'
             f'code {code}')
        post_data = {"grant_type": self.AUTHORIZATION_GRANT,
                     "client_id": self.consumer_id,
                     "client_secret": self.consumer_secret,
                     "code": code,
                     "redirect_uri": self.REDIRECT_URI}
        headers = self.base_headers()
        try:
            response = requests.post(self.TOKEN_URL,
                                     headers=headers,
                                     data=post_data)
        except Exception as e:
            print(f'Exception occurred accessing strava api {e}')
            return None
        print('response status code', response.status_code)
        if response.status_code == 200:
            token_json = response.json()
            if {'access_token', 'expires_at', 'refresh_token', 'athlete'}.issubset(token_json.keys()):
                token = Token(token_json['access_token'], token_json['refresh_token'], token_json['athlete']['id'],
                              token_json['expires_at'])
                return token
        return None
        

    def get_athlete_id(self):
        headers = self.base_headers()
        headers.update({'Authorization': 'Bearer ' + self.access_token})
        url = "https://www.strava.com/api/v3/athlete"
        results = requests.get(url, headers=headers).json()
        id = results['id']
        return id

    @staticmethod
    def user_agent():
        user_agent = request.headers.get('User-Agent')
        return "oauth2-sample-app by /u/%s" % user_agent

    def base_headers(self):
        return {"User-Agent": self.user_agent()}


    def update_headers(self, token):
        headers = self.base_headers()
        headers.update({'Authorization': 'Bearer ' + token})
        return headers


    def get_refresh_token(self, refresh_token, social_id):
        post_data = {"grant_type": self.REFRESH_GRANT,
                     "client_id": self.consumer_id,
                     "client_secret": self.consumer_secret,
                     "refresh_token": refresh_token}
        headers = self.base_headers()
        try:
            response = requests.post(self.TOKEN_URL,
                                         headers=headers,
                                         data=post_data)
        except Exception as e:
            print(f'Error getting refresh token {e}')
            return None
        if response.status_code == 200:
            refresh_json = response.json()
            print(f'refresh_json {refresh_json}')
            if {'access_token', 'refresh_token', 'expires_at'}.issubset(refresh_json.keys()):
                token = Token(refresh_json['access_token'], refresh_json['refresh_token'], social_id,
                              refresh_json['expires_at'])
                return token
        return None
