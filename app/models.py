from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt
from app import app
import redis
import rq
import json

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    refresh_token = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    mountains = db.relationship('Mountain', backref='hiker', secondary = 'user_mountain_link')
    social_id = db.Column(db.Integer)
    access_token = db.Column(db.String(128))
    expires_at = db.Column(db.Integer)
    code = db.Column(db.String(128))
    activities = db.relationship('Activity', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')

    def __repr__(self):
        return f'User {self.username} access_token {self.access_token} social id {self.social_id}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception as e:
            print('verify_reset_password_token failed')
            print(e)
            return
        return User.query.get(id)

    def get_token(self, oauth):
        if self.code is None:
            return None
        else:
            try:
                access_token = oauth.get_token(self.code, None)
            except Exception as e:
                print(f'Error occurred {e}')
                return None
        return access_token

    def get_refresh_token(self, oauth):
        try:
            refresh_token = oauth.get_token(None, self.refresh_token, self.social_id)
            print(f'got refresh token successfully! Token is: {refresh_token}')
        except Exception as e:
            print(f'Error occurred getting token: {e}')
            return None
        return refresh_token

    def update_access(self, token):
        self.access_token = token.access_token
        self.refresh_token = token.refresh_token
        self.social_id = token.social_id
        self.expires_at = token.expires_at
        db.session.commit()
        print(f'user {self.username}, social_id: {self.social_id}, access token: {self.access_token}, '
                f'refresh_token: {self.refresh_token}, expires_at: {self.expires_at}')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def launch_task(self, name, description, *args, **kwargs):
        print(f'Models: name: {name}, description {description} args {args}')
        rq_job = app.task_queue.enqueue('app.tasks.' + name, self.id,
                                                *args, **kwargs)

        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Mountain(db.Model):
    __tablename__ = 'mountain'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    users = db.relationship('User', secondary='user_mountain_link')
    activities = db.relationship('Activity', secondary='activity_mountain_link')


def __repr__(self):
    return '<Mountain {}>'.format(self.name)


class User_Mountain_Link(db.Model):
    __tablename__ = 'user_mountain_link'
    user_id = db.Column(
      db.Integer,
      db.ForeignKey('user.id'),
      primary_key = True)

    mountain_id = db.Column(
       db.Integer,
       db.ForeignKey('mountain.id'),
       primary_key = True)


class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1280))
    activity_id = db.Column(db.BigInteger, unique=True)
    url = db.Column(db.String(1280))
    polyline = db.Column(db.String(1280))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mountains = db.relationship('Mountain',  secondary = 'activity_mountain_link')
    date = db.Column(db.String(1280))
    description = db.Column(db.String(1280))

    def __repr__(self):
        return '<Activity {}>'.format(self.name)


class Activity_Mountain_Link(db.Model):
    __tablename__ = 'activity_mountain_link'
    activity_id = db.Column(
      db.Integer,
      db.ForeignKey('activity.id'),
      primary_key = True)

    mountain_id = db.Column(
       db.Integer,
       db.ForeignKey('mountain.id'),
       primary_key = True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100

