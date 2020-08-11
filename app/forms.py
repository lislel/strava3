from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class ManualEntryForm(FlaskForm):
    name = StringField('Activity Name', validators=[DataRequired()])
    mountain = StringField('Mountain', validators=[DataRequired()])
    date = StringField('Date (YYYYMMDD)', validators=[DataRequired()])
    description = StringField('Decription')
    submit = SubmitField('Save')

class ManualEntryEditForm(FlaskForm):
    name = StringField('Activity Name', validators=[DataRequired()])
    mountain = StringField('Mountain', validators=[DataRequired()])
    #mountain = SelectField('Mountain', choices=[('Washington', 'Washington'), ('Adams', 'Adams')])
    date = StringField('Date (YYYYMMDD)', validators=[DataRequired()])
    description = StringField('Decription')
    submit = SubmitField('Save')
    
    def __init__(self, act, *args, **kwargs):
        super(ManualEntryEditForm, self).__init__(*args, **kwargs)
        self.name.data = act.name  
        self.mountain.data = act.mountains
        date_str = act.date[0:4] + act.date[5:7] + act.date[8:10]
        self.date.data = date_str
        #self.description.data = act.description      

class ManualEntryViewForm(FlaskForm):
    edit = SubmitField(label='Edit Activity')
    delete = SubmitField(label='Delete Activity')

