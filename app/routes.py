from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User
from app.oauth import StravaOauth

import time
import requests


@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            oauth = StravaOauth()
            print(f'user refresh {user.refresh_token}')

            if user.refresh_token is None:
                # User has never been authenticated with Strava, get authentication information
                oauth.callback()
                if oauth.social_id is None:
                    flash('Authentication failed.')
                    return redirect(url_for('login'))
                else:
                    user.social_id = oauth.social_id
                    user.access_token = oauth.access_token
                    user.refresh_token = oauth.refresh_token
                    user.expires_at = oauth.expires_at
                    db.session.commit()

            elif user.expires_at < time.time():
                #get new access_token and refresh_token
                print(f'Expires {user.expires_at}, now {time.time()}')
                oauth.get_refresh_token()
                user.access_token = oauth.access_token
                user.refresh_token = oauth.refresh_token
                user.expires_at = oauth.expires_at
                db.session.commit()

            else:
                pass

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        oauth = StravaOauth()
        return oauth.authorize()
        # return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)
