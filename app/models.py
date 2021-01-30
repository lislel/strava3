from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt
from app import app


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

    def get_code(self, oauth):
        if self.code is None:
            try:
                self.code = oauth.callback()
                print(f'get code code is {self.code}')
                db.session.commit()
            except Exception as e:
                print(f'error occured getting code, {e}')
                return None
        return self.code

    def get_token(self, oauth):
        code = self.get_code(oauth)
        print(f' Code is : {code}')
        if code is None:
            return None
        else:
            try:
                access_token = oauth.get_token(code, None)
            except Exception as e:
                print(f'Error occurred {e}')
                return None
        return access_token

    def get_refresh_token(self, oauth):
        try:
            refresh_token = oauth.get_token(None, self.refresh_token)
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
