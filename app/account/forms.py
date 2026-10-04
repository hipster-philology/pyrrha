from flask import url_for
from markupsafe import Markup
from flask_babel import gettext as _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.fields import (
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
    EmailField
)
from wtforms.validators import Email, EqualTo, InputRequired, Length

from app.models import User


class LoginForm(FlaskForm):
    email = EmailField(
        _l('Email'), validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    password = PasswordField(_l('Password'), validators=[InputRequired()])
    remember_me = BooleanField(_l('Keep me logged in'))
    submit = SubmitField(_l('Log in'))


class RegistrationForm(FlaskForm):
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
    password = PasswordField(
        _l('Password'),
        validators=[
            InputRequired(),
            EqualTo('password2', _l('Passwords must match'))
        ])
    password2 = PasswordField(_l('Confirm password'), validators=[InputRequired()])
    submit = SubmitField(_l('Register'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            # The message is a trusted, translated string holding a link: mark it as safe HTML.
            raise ValidationError(Markup(_(
                'Unable to register a user with the provided information. '
                'Link to <a href="%(url)s">password reset</a>'
            )) % {"url": url_for('account.reset_password_request')})


class RequestResetPasswordForm(FlaskForm):
    email = EmailField(
        _l('Email'), validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField(_l('Reset password'))

    # We don't validate the email address so we don't confirm to attackers
    # that an account with the given email exists.


class ResetPasswordForm(FlaskForm):
    email = EmailField(
        _l('Email'), validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    new_password = PasswordField(
        _l('New password'),
        validators=[
            InputRequired(),
            EqualTo('new_password2', _l('Passwords must match.'))
        ])
    new_password2 = PasswordField(
        _l('Confirm new password'), validators=[InputRequired()])
    submit = SubmitField(_l('Reset password'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first() is None:
            raise ValidationError(_('Unknown email address.'))


class CreatePasswordForm(FlaskForm):
    password = PasswordField(
        _l('Password'),
        validators=[
            InputRequired(),
            EqualTo('password2', _l('Passwords must match.'))
        ])
    password2 = PasswordField(
        _l('Confirm new password'), validators=[InputRequired()])
    submit = SubmitField(_l('Set password'))


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(_l('Old password'), validators=[InputRequired()])
    new_password = PasswordField(
        _l('New password'),
        validators=[
            InputRequired(),
            EqualTo('new_password2', _l('Passwords must match.'))
        ])
    new_password2 = PasswordField(
        _l('Confirm new password'), validators=[InputRequired()])
    submit = SubmitField(_l('Update password'))


class ChangeEmailForm(FlaskForm):
    email = EmailField(
        _l('New email'), validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    password = PasswordField(_l('Password'), validators=[InputRequired()])
    submit = SubmitField(_l('Update email'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))
