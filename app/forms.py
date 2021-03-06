from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Mountain
from wtforms.widgets import TextArea


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

#format mountains to be used by selectfield
def mountain_choices():
    choices = ['']
    try:
        mts = Mountain.query.all()
        mts.sort(key=lambda x: x.name)
        i = 1
        for mt in mts:
            choices.append(mt.name)
            i += 1
        # print(choices)
    except Exception as e:
        print(e)
    return choices

class ManualEntryEditForm(FlaskForm):
    name = StringField('Activity Name', validators=[DataRequired()])
    mtn = SelectField('Mountain', validators=[DataRequired()], choices=mountain_choices())
    date = StringField('Date (YYYYMMDD)', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Save')

class ContactUsForm(FlaskForm):
    message = StringField(u'Text', widget=TextArea())

class LinkStravaForm(FlaskForm):
    yes = SubmitField(label='Yes')
    no = SubmitField(label='No')

