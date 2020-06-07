from datetime import datetime
from app import db

class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	refresh_token = db.Column(db.String(128))
	mountains = db.relationship('Mountain', backref='hiker', secondary = 'link')

def __repr__(self):
    return '<User {}>'.format(self.username)

class Mountain(db.Model):
	__tablename__ = 'mountain'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128))
	lat = db.Column(db.String(128))
	lon = db.Column(db.String(128))
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