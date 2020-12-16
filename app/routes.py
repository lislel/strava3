from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.models import User, Mountain, Activity
from app.oauth import StravaOauth, DataIngest
from app.forms import mountain_choices, ResetPasswordForm, ManualEntryEditForm, ContactUsForm, LinkStravaForm
from app.email import send_password_reset_email, send_email

import time
import requests
import json


@app.route('/', methods=['GET', 'POST'])
@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    return render_template('welcome.html', title="Welcome to NH High Peaks")


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

    n_finished = len(mts) - len(unfinished)

    return render_template('index.html', title='Home', finished=finished, unfinished=unfinished, n_finished=n_finished, user_id=current_user.id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print(f'current user is {current_user.username}')
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        # user doesn't exist or password is bad
        if user is None or not user.check_password(request.form['username']):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        # user did not link strava
        elif user.access_token == 'NA':
            login_user(user, remember=request.form['password'])
            return redirect(url_for('index'))
        # user did link strava
        else:
            oauth = StravaOauth()
            print('user.access_token = ', user.access_token)

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

    return render_template('login.html', title='Sign In')


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
    return redirect(url_for('welcome'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    print(f'1 current user authenitcated? {current_user.is_authenticated}')
    print('Session: ', session)
    if current_user.is_authenticated:
        logout_user()
        print(f'2 current user authenitcated? {current_user.is_authenticated}')
        # print('current user is authenticated')
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        user = User(username=request.form['username'], email=request.form['email'])
        if request.form['password'] != request.form['repeat_password']:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        """
        oauth = StravaOauth()
        return oauth.authorize()
        """
        return redirect('/linkstrava/' + user.username)
        # return render_template('linkstrava.html', title='Link Strava?', user=user, form=LinkStravaForm())

    return render_template('register.html', title='Register')

@app.route('/linkstrava/<username>', methods=['GET', 'POST'])
def linkstrava(username):
    form = LinkStravaForm()
    user = User.query.filter_by(username=username).first()
    if form.validate_on_submit():
        if form.yes.data:
            oauth = StravaOauth()
            return oauth.authorize()
        if form.no.data:
            user.access_token = 'NA'
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('linkstrava.html', title='Link Strava Account', form=form)

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
    """
    print('Here are my map markes:\n')
    for m in map_markers:
        print('\n', m)
    """
    return render_template('map.html', title='Map', all_polylines=all_polylines, map_markers=map_markers)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()

    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            send_password_reset_email(user)
        else:
            send_email('[NH High Peaks] Reset Password request for nonexistent email',
                sender=app.config['ADMINS'][0],
                recipients=[app.config['ADMINS'][0]],
                text_body='',
                html_body='')
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    #if current_user.is_authenticated:
    #    return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Not user')
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title="Reset Password", form=form)


@app.route('/manual_entry', methods=['GET', 'POST'])
@login_required
def manual_entry():
    if request.method == 'POST':
        if manual_entry_data_check(request.form['mountain'], request.form['date']):
            act = Activity()
            act.name = request.form['act_name']
            act.polyline = None
            act_id = act.id
            act.url = '/view/' + act.name 
            #act.url = 'https://www.youtube.com/watch?v=p3G5IXn0K7A'
            mt = find_mountain(request.form['mountain'])
            act.mountains.append(mt)
            act.activity_id = None
            act.date = convert_date(request.form['date'])
            current_user.activities.append(act)
            act.description = request.form['description']
            db.session.commit()

            flash("Peak Saved!")
            return redirect(url_for('index'))
        else:
            flash("Invalid Data")

    return render_template('manual_entry.html', title="Manual Entry", mt_list=mountain_choices())

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
    form_data = {"act_name": act.name, "mountain": act.mountains[0].name, "date": date_str, "description": act.description}
    if request.method == 'POST':
        if manual_entry_data_check(request.form['mountain'], request.form['date']):
            act.name = request.form['act_name']
            act.polyline = None
            #act.url = 'https://www.youtube.com/watch?v=p3G5IXn0K7A'
            act.url = '/view/' + act.name
            mt = find_mountain(request.form['mountain'])
            act.mountains[0] = mt
            act.activity_id = None
            act.date = convert_date(request.form['date'])
            act.description = request.form['description']
            db.session.commit()

            flash("Edit Saved!")
            return redirect(url_for('index'))
        else:
            flash("Invalid Data")

    return render_template('manual_entry_edit.html', title="Edit Activity", form_data=form_data, mt_list=mountain_choices())

def find_act_from_name(act_name):
    for act in Activity.query.all():
        if act.name == act_name:
            return act
    return None


@app.route('/view/<act_name>', methods=['GET', 'POST'])
@login_required
def manual_entry_view(act_name):
    act = find_act_from_name(act_name)

    if request.method == 'POST':
        if request.form['submit'] == 'edit':
            # flash("Edit Button Clicked")
            return redirect('/edit/' + act_name)
        if request.form['submit'] == 'delete':
            flash("Activity Deleted")
            db.session.delete(act)
            db.session.commit()
            return index()

    return render_template('manual_entry_view.html', title="Manual Entry View", act=act)

@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    form = ContactUsForm()
    if form.validate_on_submit():
        message=request.form['message']
        flash(request.form['message'])
        if current_user.is_authenticated:
            send_email('[NH High Peaks] Contact Us Submission',
                sender=app.config['ADMINS'][0],
                recipients=[app.config['ADMINS'][0]],
                text_body=render_template('email/contact_us.txt', 
                    message=message, username=current_user.username, 
                    email=current_user.email, id=current_user.id),
                html_body=render_template('email/contact_us.html', 
                    message=message, username=current_user.username, 
                    email=current_user.email, id=current_user.id))
        else:
            send_email('[NH High Peaks] Contact Us Submission',
                sender=app.config['ADMINS'][0],
                recipients=[app.config['ADMINS'][0]],
                text_body=render_template('email/contact_us.txt', 
                    message=message, username='NA', email='NA', id='NA'),
                html_body=render_template('email/contact_us.html', 
                    message=message, username='NA', email='NA', id='NA'))

        flash("Feedback Sent")
        return index()
    return render_template('contactus.html', title="Contact Us",  form=form)

@app.route('/aboutus', methods=['GET'])
def aboutus():
    return render_template('aboutus.html', title="About Us")

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Print form keys and values
        for key, value in request.form.items():
            print("key: {0}, value: {1}".format(key, value))
        
        # Change Username
        if request.form['submit'] == 'change_username':
            all_users = User.query.all()
            all_usernames = []
            for user in all_users:
                all_usernames.append(user.username)
            if request.form['new_username'] == current_user.username:
                flash('Please choose new username')
                return redirect(url_for('settings'))
            elif request.form['new_username'] in all_usernames or request.form['new_username'] == '':
                flash('Username is already taken')
                return redirect(url_for('settings'))
            else:
                current_user.username = request.form['new_username']
                db.session.commit()
                flash('change_username to %s'%(request.form['new_username']))
                return redirect(url_for('index'))
        
        # Change Password
        if request.form['submit'] == 'change_password':
            token = current_user.get_reset_password_token()
            return redirect(url_for('reset_password', token=token, _external=True))
       
        # Delete Account
        if request.form['submit'] == 'delete':
            delete_account(current_user)
            return redirect(url_for('welcome'))

    return render_template('settings.html', title="Account Settings", username=current_user.username)

def boobs():
    flash('dem boobies')

def delete_account(user):
    flash('%s, your account has been deleted'%user.username)
    act = Activity.query.all()
    for a in act:
        if a.user_id == current_user.id:
            db.session.delete(a)
    db.session.delete(user)
    db.session.commit()






