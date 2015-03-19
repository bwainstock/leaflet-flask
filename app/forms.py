from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length


class KeyForm(Form):
    spot_id = StringField('spot_id', validators=[Length(min=33, max=33)])
    description = StringField('description', validators=[])


class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)