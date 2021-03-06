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
    #REDIRECT_URI = 'http://localhost:5000/login'
    REDIRECT_URI = 'https://www.nhhighpeaks.com/login'
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

    @staticmethod
    def callback():
        code = request.args.get('code')
        return code

    def get_token(self, code, refresh_token):
        if refresh_token is None:
            # Getting user token for first time
            post_data = {"grant_type": self.AUTHORIZATION_GRANT,
                         "client_id": self.consumer_id,
                         "client_secret": self.consumer_secret,
                         "code": code,
                         "redirect_uri": self.REDIRECT_URI}
        else:
            # Getting refresh token
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
            print(f'Exception occurred accessing strava api {e}')
            return None

        if response.status_code == 200:
            token_json = response.json()
            print(f' Token json = {token_json}')
            if {'access_token', 'expires_at', 'refresh_token', 'athlete'}.issubset(token_json.keys()):
                token = Token(token_json['access_token'], token_json['refresh_token'], token_json['athlete']['id'],
                              token_json['expires_at'])
                return token
        return None

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

