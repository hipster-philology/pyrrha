from flask import current_app
from flask_login import AnonymousUserMixin, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db, login_manager
from ..utils.token import get_reset_token_salt, get_reset_token, get_reset_token_key, verify_reset_token


class Permission:
    GENERAL = 0x01
    ADMINISTER = 0xff

class Serializer:
    def __init__(self, secret):
        self._secret = secret


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    index = db.Column(db.String(64))
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def add_default_roles():
        roles = {
            'User': (Permission.GENERAL, 'account', True),
            'Administrator': (
                Permission.ADMINISTER,
                'admin',
                False  # grants all permissions
            )
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.index = roles[r][1]
            role.default = roles[r][2]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role \'%s\'>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.query.filter_by(
                    permissions=Permission.ADMINISTER).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_admin(self):
        return self.can(Permission.ADMINISTER)

    @staticmethod
    def get_admins():
        return User.query.filter(User.role_id == Role.id, Role.permissions == Permission.ADMINISTER).all()

    @property
    def password(self):
        raise AttributeError('`password` is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=604800) -> str:
        """Generate a confirmation token to email a new user."""
        return get_reset_token(self, expires_sec=expiration, additional_fields={'confirm': str(self.id)})

    def generate_email_change_token(self, new_email, expiration=3600) -> str:
        """Generate an email change token to email an existing user."""
        return get_reset_token(self, expires_sec=expiration, additional_fields={
            'change_email': str(self.id),
            'new_email': new_email
        })

    def generate_password_reset_token(self, expiration=3600):
        """
        Generate a password reset change token to email to an existing user.
        """
        return get_reset_token(self, expires_sec=expiration, additional_fields={
            'reset': str(self.id)
        })

    def confirm_account(self, token):
        """Verify that the provided token is for this user's id."""
        if not verify_reset_token(self, token, payload_cb=lambda payload: payload.get('confirm') == str(self.id)):
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def change_email(self, token):
        """Verify the new email for this user."""
        payload = verify_reset_token(
            self,
            token,
            payload_cb=lambda loc_payload: loc_payload.get('change_email') == str(self.id),
            get_payload=True
        )
        if payload is False:
            return False
        new_email = payload.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        db.session.commit()
        return True

    def reset_password(self, token, new_password):
        """Verify the new password for this user."""

        if not verify_reset_token(
            self,
            token,
            payload_cb=lambda loc_payload: loc_payload.get('reset') == str(self.id),
            get_payload=True
        ):
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    """
    @staticmethod
    def generate_fake(count=100, **kwargs):
        #Generate a number of fake users for testing
        from sqlalchemy.exc import IntegrityError
        from random import seed, choice
        from faker import Faker

        fake = Faker()
        roles = Role.query.all()

        seed()
        for i in range(count):
            u = User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                password='password',
                confirmed=True,
                role=choice(roles),
                **kwargs)
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User \'%s\'>' % self.full_name()
    """

    @staticmethod
    def add_default_users():
        """
        add default users to the db
        :param db:
        :return:
        """
        default_user = User(
            id=1,
            first_name="admin",
            last_name="admin",
            email="ppa-admin@ppa.fr",
            password="admin",
            password_hash="pbkdf2:sha256:50000$ny4HJVBb$e2effd92d18140d2629d1f00bebbfbbd1544d8a81278e246b5c46e27f20daff4",
            confirmed=True
        )
        db.session.add(default_user)
        db.session.commit()


class AnonymousUser(AnonymousUserMixin):
    id = None
    def can(self, _):
        return False

    def is_admin(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    db.session.rollback()
    return User.query.get(int(user_id))

