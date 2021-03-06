from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, SubmitField, DateTimeField
# from wtforms.fields.html5 import DateTimeField
from wtforms.validators import DataRequired, Length, Optional, EqualTo, ValidationError


class KeyForm(Form):
    spot_id = StringField('spot_id', validators=[Length(min=33, max=33)])
    description = StringField('description', validators=[])
    submit = SubmitField('submit')


# class LoginForm(Form):
#     openid = StringField('openid', validators=[DataRequired()])
#     remember_me = BooleanField('remember_me', default=False)
class LoginForm(Form):
    username = StringField('username', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('login')

class RegistrationForm(Form):
    username = StringField('username', validators=[DataRequired(), Length(4, 64)])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password_again = PasswordField('password again', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('register')


class DateForm(Form):
    start = DateTimeField('start', format='%Y-%m-%dT%H:%M:%S')
    end = DateTimeField('end', format='%Y-%m-%dT%H:%M:%S')
    submit = SubmitField('submit')