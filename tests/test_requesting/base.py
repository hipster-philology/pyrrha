from flask_testing import TestCase
from tests.db_fixtures import add_corpus
from flask import url_for

from app.models import User, Role
from app import create_app, db
from sqlalchemy_utils import database_exists, create_database


class TestBase(TestCase):

    def create_app(self):

        # pass in test configurations
        config_name = 'test'
        app = create_app(config_name)
        return app

    def setUp(self):
        """
        Will be called before every test
        """
        if not database_exists(db.engine.url):
            create_database(db.engine.url)
        self.app = self.create_app()
        self.client = self.app.test_client()
        db.session.commit()
        db.drop_all()
        db.create_all()
        db.session.commit()
        TestBase.admin_login(self.app, self.client)
        self.db = db

    def tearDown(self):
        """
        Will be called after every test
        """

        db.session.remove()
        db.drop_all()
        # https://stackoverflow.com/questions/66876181/how-do-i-close-a-flask-sqlalchemy-connection-that-i-used-in-a-thread/67077811#67077811
        if self.db.engine.dialect.name == "postgresql":
            db.session.close()
            db.get_engine(self.app).dispose()

    def addCorpus(self, corpus, *args, **kwargs):
        if corpus == "wauchier":
            add_corpus("wauchier", db, *args, **kwargs)
        else:
            add_corpus("floovant", db, *args, **kwargs)

    @staticmethod
    def admin_login(app, client):
        Role.add_default_roles()
        User.add_default_users()
        return client.post(url_for('account.login'), data=dict(
            email=app.config['ADMIN_EMAIL'],
            password=app.config['ADMIN_PASSWORD']
        ), follow_redirects=True)
