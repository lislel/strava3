import json
from flask import current_app, url_for, request, redirect, session
import urllib
import requests
import polyline
from app.models import Mountain, Activity, User


class DataIngest():
    PAGE_URL = "https://www.strava.com/api/v3/athletes/%s/stats"
    ACTIVITES_URL = "https://www.strava.com/api/v3/activities"

    def __init__(self, user, oauth):
        self.user = user
        self.oauth = oauth
        self.headers = self.oauth.update_headers(self.user.access_token)

    def update(self):
        for page in self.get_activities(1):
            print(f'page = {page}')
            self.parse(page)


    def get_pages(self):
        url = self.PAGE_URL % self.user.social_id
        results = requests.get(url, headers=self.headers).json()
        print(f'Page results: {results}')
        act_total = int(results['all_run_totals']['count']) +  int(results['all_ride_totals']['count']) + int(results['all_swim_totals']['count'])
        #  Get total number of known pages
        self.page_num = int(act_total/200)
        return self.page_num


    def get_activities(self, page):
        url = self.ACTIVITES_URL
        page_result = requests.get(url, headers=self.headers, params={'page': page, 'per_page': 200}).json()
        while len(page_result) > 0:
            try:
                page_result = requests.get(url, headers=self.headers, params={'page': page, 'per_page': 200}).json()
                yield page_result
                page += 1
            except:
                pass


    def parse(self, page):
        mountains = Mountain.query.all()
        print(f'page2 = {page}')
        for item in page:
            if item['start_latlng'] is not None:
                if item['type'] != 'Bike' and item['start_latlng'][0] >= 43.82 and item['start_latlng'][0] <= 44.62 and \
                        item['start_latlng'][1] >= -71.97 and item['start_latlng'][1] <= -71.012:
                    if item['elev_high'] > 1210:
                        line = item['map']['summary_polyline']
                        points = polyline.decode(line)
                        for mt in mountains:
                            min_dist = 10000000
                            for pt in points:
                                hypot = get_hypot(pt, mt.lat, mt.lon)
                                if hypot < min_dist:
                                    min_dist = hypot
                            if min_dist <= 0.0085:
                                # add id to list of activities that have touched this mountain
                                acitivty = Activity()
                                activity.name = item['name']
                                acitivty.polyline = item['map']['summary_polyline']
                                activity.url = item['id']
                                activity.user_id = user.id
                                activity.mountains.append(mt)
                                db.session.commit()

        return




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


    def update_headers(self, token):
        headers = self.base_headers()
        headers.update({'Authorization': 'Bearer ' + token})
        return headers


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