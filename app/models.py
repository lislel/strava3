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

	activities = db.relationship('Activity', lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.username)
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
	lat = db.Column(db.Integer)
	lon = db.Column(db.Integer)
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
	activity_id = db.Column(db.Integer, unique=True)
	url = db.Column(db.String(1280))
	polyline = db.Column(db.String(1280))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	mountains = db.relationship('Mountain',  secondary = 'activity_mountain_link')

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
