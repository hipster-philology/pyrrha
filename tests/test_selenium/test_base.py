from flask_testing import LiveServerTestCase
from app import create_app, db
import unittest

from selenium import webdriver
from urllib.request import urlopen


class TestBase(LiveServerTestCase, unittest.TestCase):

    def create_app(self):
        config_name = 'test'
        app = create_app(config_name)
        app.config.update(
            # Change the port that the liveserver listens on
            LIVESERVER_PORT=8943
        )
        return app

    def setUp(self):
        """Setup the test driver and create test users"""
        self.driver = webdriver.Chrome()
        self.driver.get(self.get_server_url())

        db.session.commit()
        db.drop_all()
        db.create_all()
        db.session.commit()

    def tearDown(self):
        self.driver.quit()

    def test_server_is_up_and_running(self):
        response = urlopen(self.get_server_url())
        self.assertEqual(response.code, 200)
