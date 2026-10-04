from flask_babel import gettext as _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired


class Delete(FlaskForm):
    name = StringField(_l("Name"), validators=[InputRequired()])
    submit = SubmitField(_l('Delete this corpus'))
