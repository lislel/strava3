from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User, Mountain, Activity
from app.oauth import StravaOauth, DataIngest
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, ManualEntryForm, ManualEntryEditForm, ManualEntryViewForm
from app.email import send_password_reset_email

import time
import requests
import json


@app.route('/')
@app.route('/index')
@login_required
def index():
    mts = Mountain.query.all()
    finished = dict()
    unfinished = []
    for mt in mts:
        acts = [a for a in mt.activities if a.user_id == current_user.id]
        if len(acts) > 0:
            finished[mt] = acts
        else:
            unfinished.append(mt)

    return render_template('index.html', title='Home', finished=finished, unfinished=unfinished, user_id=current_user.id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print(f'current user is {current_user.username}')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            oauth = StravaOauth()
            if user.social_id is None:
                # User has never been authenticated with Strava, get authentication information
                print('new user!')
                user.last_seen = None
                oauth.callback()
                if oauth.social_id is None:
                    flash('Authentication failed.')
                    redirect(url_for('login'))
                user.social_id = oauth.social_id
                update_access(user, oauth)
            elif user.expires_at < time.time():
                # Get new access_token and refresh_token
                print(f'Expires {user.expires_at}, now {time.time()}')
                oauth.get_refresh_token(user.refresh_token)
                update_access(user, oauth)
            else:
                pass
        login_user(user, remember=form.remember_me.data)

        # Get Strava activity
        data_ingest = DataIngest(user, oauth)
        data_ingest.update()

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


def update_access(user, oauth):
    user.access_token = oauth.access_token
    user.refresh_token = oauth.refresh_token
    user.expires_at = oauth.expires_at
    db.session.commit()
    print(f'user {user.username}, social_id: {user.social_id}, access token: {user.access_token}, refresh_token: {user.refresh_token}, expires_at: {user.expires_at}')
    return

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    print(f'1 current user authenitcated? {current_user.is_authenticated}')
    print(session)
    if current_user.is_authenticated:
        logout_user()
        print(f'2 current user authenitcated? {current_user.is_authenticated}')

        # print('current user is authenticated')
        # return redirect(url_for('index'))

    app.logger.setLevel(logging.INFO)
    app.logger.info('User Registration Started')

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

@login_required
@app.route('/map')
def map():
    mts = Mountain.query.all()
    map_markers = []
    all_polylines = []
    for mt in mts:
        mt_dict = {'lat': mt.lat, 'lon': mt.lon, 'name': mt.name}
        acts = [a for a in mt.activities if a.user_id == current_user.id]
        act_names = [a.name for a in acts]
        polylines = [p.polyline for p in acts if p.polyline != None]
        urls = [a.url for a in acts]

        if len(act_names) > 0:
            mt_dict['act_names'] = act_names
        else:
            mt_dict['act_names'] = 'missing'

        if len(polylines) > 0:
            all_polylines.extend(polylines)

        mt_dict['urls'] = urls
        map_markers.append(mt_dict)

    polylines = json.dumps(polylines)

    print('Here are my map markes:\n')
    for m in map_markers:
        print('\n', m)
    return render_template('map.html', title='Map', all_polylines=all_polylines, map_markers=map_markers)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    form = ManualEntryForm()
    if form.validate_on_submit():
        if manual_entry_data_check(form.mtn.data, form.date.data):
            act = Activity()
            act.name = form.name.data
            act.polyline = None
            act_id = act.id
            act.url = '/view/' + act.name 
            #act.url = 'https://www.youtube.com/watch?v=p3G5IXn0K7A'
            mt = find_mountain(form.mtn.data)
            act.mountains.append(mt)
            act.activity_id = None
            act.date = convert_date(form.date.data)
            current_user.activities.append(act)
            act.description = form.description.data
            db.session.commit()

            flash("Peak Saved!")
            return redirect(url_for('index'))
        if not manual_entry_data_check(form.mtn.data, form.date.data):
            flash("Invalid Data")

    return render_template('manual_entry.html', form=form, title="Manual Entry")

def manual_entry_data_check(mountain, date):
    if len(mountain) < 3:
        return 0
    if len(date) != 8:
        return 0
    return 1

def find_mountain(input):
    for mt in Mountain.query.all():
        if input == mt.name:
            return mt
    
    print('Error: Mountain not found')
    return None

def convert_date(date_str):
    # convert 'YYYYMMDD' to 'YYYY-DD-MMT00-00-00Z'
    year = date_str[0:4]
    month = date_str[4:6]
    day = date_str[6:8]
    new_date_str = year + '-' + month + '-' + day + 'T00-00-00Z'
    return new_date_str

@app.route('/edit/<act_name>', methods=['GET', 'POST'])
@login_required
def manual_entry_edit(act_name):
    act = find_act_from_name(act_name)
    date_str = act.date[0:4] + act.date[5:7] + act.date[8:10]
    form = ManualEntryEditForm(name=act.name, mountain=act.mountains[0].name, date=date_str, description=act.description)
    if form.validate_on_submit():
        if manual_entry_data_check(form.mtn.data, form.date.data):
            act.name = form.name.data
            act.polyline = None
            #act.url = 'https://www.youtube.com/watch?v=p3G5IXn0K7A'
            act.url = '/view/' + act.name
            mt = find_mountain(form.mtn.data)
            act.mountains[0] = mt
            act.activity_id = None
            act.date = convert_date(form.date.data)
            act.description = form.description.data
            db.session.commit()

            flash("Edit Saved!")
            return redirect(url_for('index'))
        if not manual_entry_data_check(form.mountain.data, form.date.data):
            flash("Invalid Data   ")

    return render_template('manual_entry_edit.html', form=form, title="Manual Entry Edit")

def find_act_from_name(act_name):
    for act in Activity.query.all():
        if act.name == act_name:
            return act
    return None


@app.route('/view/<act_name>', methods=['GET', 'POST'])
@login_required
def manual_entry_view(act_name):
    form = ManualEntryViewForm()
    act = find_act_from_name(act_name)

    if form.validate_on_submit():
        if form.edit.data:
            flash("Edit Button Clicked")
            return redirect('/edit/' + act_name)
        if form.delete.data:
            flash("Activity Deleted")
            db.session.delete(act)
            db.session.commit()
            return index()

    return render_template('manual_entry_view.html', title="Big Booty", act=act, form=form)


