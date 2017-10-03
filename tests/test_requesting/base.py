from flask_testing import TestCase

from app import create_app, db


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

        db.session.commit()
        db.drop_all()
        db.create_all()
        db.session.commit()
        self.db = db

    def tearDown(self):
        """
        Will be called after every test
        """

        db.session.remove()
        db.drop_all()
