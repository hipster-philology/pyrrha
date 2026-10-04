from flask_babel import gettext as _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.fields import (
    PasswordField,
    StringField,
    SubmitField,
    EmailField
)
from wtforms.validators import (
    Email,
    EqualTo,
    InputRequired,
    Length,
)

from app import db
from app.models import Role, User


class ChangeUserEmailForm(FlaskForm):
    email = EmailField(
        _l('New email'), validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    submit = SubmitField(_l('Update email'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))


class ChangeAccountTypeForm(FlaskForm):
    role = QuerySelectField(
        _l('New account type'),
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    submit = SubmitField(_l('Update role'))


class ChangeAccountStatusForm(FlaskForm):
    submit = SubmitField(_l('Toggle status'))


class InviteUserForm(FlaskForm):
    role = QuerySelectField(
        _l('Account type'),
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    first_name = StringField(
        _l('First name'), validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        _l('Last name'), validators=[InputRequired(),
                                 Length(1, 64)])
    email = EmailField(
        _l('Email'), validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField(_l('Invite'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))


class NewUserForm(InviteUserForm):
    password = PasswordField(
        _l('Password'),
        validators=[
            InputRequired(),
            EqualTo('password2', _l('Passwords must match.'))
        ])
    password2 = PasswordField(_l('Confirm password'), validators=[InputRequired()])

    submit = SubmitField(_l('Create'))
