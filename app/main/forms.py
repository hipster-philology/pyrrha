from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired


class Delete(FlaskForm):
    name = StringField("Name", validators=[InputRequired()])
    submit = SubmitField('Delete this corpus')
