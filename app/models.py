from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	refresh_token = db.Column(db.String(128))
	mountains = db.relationship('Mountain', backref='hiker', secondary = 'link')
	social_id = db.Column(db.Integer)

	def __repr__(self):
		return '<User {}>'.format(self.username)
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id)) 

class Mountain(db.Model):
	__tablename__ = 'mountain'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=True)
	lat = db.Column(db.Integer)
	lon = db.Column(db.Integer)
	users = db.relationship('User', secondary='link')

def __repr__(self):
    return '<Mountain {}>'.format(self.name)


class Link(db.Model):
	__tablename__ = 'link'
	user_id = db.Column(
	  db.Integer, 
	  db.ForeignKey('user.id'), 
	  primary_key = True)

	mountain_id = db.Column(
	   db.Integer, 
	   db.ForeignKey('mountain.id'), 
	   primary_key = True)