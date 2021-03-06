import polyline
from app import db, app
from app.models import Activity, Mountain
import math
import datetime
import asyncio
from aiohttp import ClientSession
from app.email import send_email
import requests
import json


async def fetch(url, params, headers, session):
    async with session.get(url, params=params, headers=headers) as response:
        reply_string = await response.read()
        reply = json.loads(reply_string.decode('utf-8'))
        return reply


class DataIngest:
    PAGE_URL = "https://www.strava.com/api/v3/athletes/%s/stats"
    ACTIVITIES_URL = "https://www.strava.com/api/v3/activities"
    LAT_MAX = 43.82
    LAT_MIN = 44.62
    LON_MAX = -71.97
    LON_MIN = -71.012
    REQUESTS_PER_PAGE = 200
    MIN_ELEVATION = 1210
    MIN_DISTANCE = 0.0085
    NEW_USER = 'new_user'
    RETURNING_USER = 'returning_user'

    def __init__(self, user, oauth):
        self.user = user
        self.oauth = oauth
        self.headers = self.oauth.update_headers(self.user.access_token)
        self.responses = None

    def update(self, user_type):
        errors = []
        if user_type == self.NEW_USER:
            errors = self.update_new_user(errors)
        elif user_type == self.RETURNING_USER:
            errors = self.update_returning_visitor(errors)

        if len(errors) > 1:
            self.send_error_email(errors)

        self.user.last_seen = datetime.datetime.now()
        db.session.commit()
        return True

    def update_new_user(self, errors):
        all_responses = self.get_activities_from_api()
        for act in all_responses:
            try:
                self.parse(act)
            except Exception as e:
                print(f'Exception occurred {e}')
                errors.append(e)
        return errors

    def update_returning_visitor(self, errors):
        counter = 1
        done = False
        print(f'starting')
        while done is False:
            activities = self.get_page(counter)
            for act in activities:
                activity_start = datetime.datetime.strptime(act['start_date'], '%Y-%m-%dT%H:%M:%SZ')
                print(f'activity start_date: {activity_start} user last seen {self.user.last_seen} ')
                if activity_start < self.user.last_seen:
                    done = True
                    print('No new activities!')
                    break
                else:
                    try:
                        self.parse(act)
                    except Exception as e:
                        print(f'Exception occurred {e}')
                        errors.append(e)
            counter += 1
        return errors

    def send_error_email(self, errors):
        message = f'User id: {self.user.id}\n Errors: {errors}'
        try:
            send_email('[NH High Peaks] Error adding activity into database',
                       sender=app.config['ADMINS'][0],
                       recipients=[app.config['ADMINS'][0]],
                       text_body=message,
                       html_body=message)
        except Exception as e:
            print(f'Could not send error email for errors involving user {self.user.id}')

    def get_activities_from_api(self):
        # Get all known number of pages asynchronously
        num_pages = self.get_approximate_number_of_pages()
        all_responses = self.get_known_pages(num_pages)

        # Get rest synchronously first time:
        if self.user.last_seen is not None:
            synchronous_activities = self.get_unknown_pages(num_pages)
            # Concatenate results
            all_responses.extend(synchronous_activities)
        return all_responses

    def get_page(self, page):
        page_result = requests.get(self.ACTIVITIES_URL, headers=self.headers,
                                   params={'page': page, 'per_page': self.REQUESTS_PER_PAGE}).json()
        return page_result

    def get_known_pages(self, num_pages):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(self.run(num_pages + 1, self.headers))
        self.responses = loop.run_until_complete(future)
        all_responses = [item for sublist in self.responses for item in sublist]
        return all_responses

    def get_unknown_pages(self, num_pages):
        sync = []
        page = num_pages + 1
        page_result = self.get_page(page)
        while len(page_result) > 0:
            for a in page_result:
                sync.append(a)
            page += 1
            page_result = self.get_page(page)
        return sync

    async def run(self, r, headers):
        headers = headers
        tasks = []
        # Fetch all responses within one Client session,
        # keep connection alive for all requests.
        async with ClientSession() as session:
            for i in range(r):
                print(f'page {i}')
                task = asyncio.ensure_future(fetch(self.ACTIVITIES_URL, {'page': i, 'per_page': self.REQUESTS_PER_PAGE},
                                                   headers, session))
                tasks.append(task)

            return await asyncio.gather(*tasks)

    def get_approximate_number_of_pages(self):
        url = self.PAGE_URL % self.user.social_id
        results = requests.get(url, headers=self.headers).json()
        print(f'results = {results}')
        act_total = int(results['all_run_totals']['count']) + int(results['all_ride_totals']['count']) + int(
            results['all_swim_totals']['count'])
        #  Get total number of known pages
        page_num = int(math.ceil(act_total / self.REQUESTS_PER_PAGE))
        return page_num

    def parse(self, item):
        if self.validate_item(item):
            print(f'parsing {item["id"]}')
            line = item['map']['summary_polyline']
            points = polyline.decode(line)
            for mt in Mountain.query.all():
                min_dist = float('inf')
                for pt in points:
                    hypot = self.get_hypot(pt, mt.lat, mt.lon)
                    if hypot < min_dist:
                        min_dist = hypot
                if min_dist <= self.MIN_DISTANCE:
                    id_string = int(f"{item['id']}{mt.id}{self.user.id}")
                    exists = db.session.query(Activity).filter_by(activity_id=id_string).scalar()
                    if exists is None:
                        # New activity
                        act = self.create_activity(item, mt, id_string)
                        self.user.activities.append(act)
                        db.session.commit()
                    else:
                        act_exist_for_user = db.session.query(Activity).filter_by(activity_id=id_string).filter_by(
                            user_id=self.user.id).scalar()
                        if act_exist_for_user is None:
                            act = db.session.query(Activity).filter_by(activity_id=id_string).first()
                            self.user.activities.append(act)
                            db.session.commit()

    def validate_item(self, item):
        if isinstance(item, dict) is False:
            print(f'Item {item} is not a dict instance, it is {type(item)}')
            return False
        if {'start_latlng', 'type', 'elev_high', 'map'}.issubset(item.keys()) is False:
            print(f'Item {item} missing data to parse')
            return False
        if item['start_latlng'] is None:
            print(f'{item} No start latlng for activity')
            return False
        if item['type'] == 'Bike':
            print('This is a biking activity, not parsing')
            return False
        if self.check_start_location(item) is False:
            return False
        if item['elev_high'] < self.MIN_ELEVATION:
            return False
        if len(item['map']['summary_polyline']) == 0:
            return False
        return True

    def check_start_location(self, item):
        if self.LAT_MAX <= item['start_latlng'][0] <= self.LAT_MIN and self.LON_MAX <= item['start_latlng'][1] <= self.LON_MIN:
            return True
        else:
            return False

    @staticmethod
    def create_activity(item, mt, id_string):
        act = Activity()
        act.name = item['name']
        act.polyline = item['map']['summary_polyline']
        act.url = f'https://www.strava.com/activities/{item["id"]}'
        act.mountains.append(mt)
        act.activity_id = id_string
        act.date = item['start_date']
        return act

    @staticmethod
    def get_hypot(pt, lat, lon):
        x_ind = pt[0] - lat
        y_ind = pt[1] - lon
        hypot = math.sqrt(math.pow(x_ind, 2) + math.pow(y_ind, 2))
        return hypot
