"""
Email related functions can be found here
"""

from threading import Thread
from flask import render_template
from flask_mail import Message
from app import app, mail


def send_async_email(app, msg):
	"""send asychronous email"""
	with app.app_context():
		mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
	"""send email"""
	msg = Message(subject, sender=sender, recipients=recipients)
	msg.body = text_body
	msg.html = html_body
	Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
	"""send reset password email to user"""
	token = user.get_reset_password_token()
	send_email('[NH High Peaks] Reset Your Password',
			sender=app.config['ADMINS'][0],
				recipients=[user.email],
				text_body=render_template('email/reset_password.txt',
											user=user, token=token),
               html_body=render_template('email/reset_password.html',
											user=user, token=token))
