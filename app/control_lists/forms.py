from flask_babel import gettext as _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.fields import (
    TextAreaField,
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired


class SendMailToAdmin(FlaskForm):
    title = StringField(_l('Title'), validators=[InputRequired()])
    message = TextAreaField(_l("Message"), validators=[InputRequired()])
    submit = SubmitField(_l('Send mail'))


class Rename(FlaskForm):
    title = StringField(_l('Title'), validators=[InputRequired()])
    submit = SubmitField(_l('Rename'))
