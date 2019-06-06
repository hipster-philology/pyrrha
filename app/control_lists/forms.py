from flask_wtf import FlaskForm
from wtforms.fields import (
    TextAreaField,
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired


class SendMailToAdmin(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    message = TextAreaField("Message", validators=[InputRequired()])
    submit = SubmitField('Send mail')


class Rename(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    submit = SubmitField('Rename')
