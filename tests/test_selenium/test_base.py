from flask_testing import LiveServerTestCase
from app import create_app, db

import clipboard

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from urllib.request import urlopen


class TestBase(LiveServerTestCase):

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

    def writeMultiline(self, element, text):
        """ Helper to write in multiline text

        :param element: Element in which to write the text
        :type element: selenium.webdriver.remote.webelement.WebElement
        :param text: Multiline text to write
        :return: element
        """
        clipboard.copy(text)
        element.send_keys(Keys.CONTROL+"v")
        """for part in text.split('\n'):
            count_t = part.count("\t")
            for index, subpart in enumerate(part.split("\t")):
                t = Keys.TAB
                if index == count_t:
                    t = "\n"
                element.send_keys(subpart+t)"""
        return element

    def tearDown(self):
        self.driver.quit()

    def test_server_is_up_and_running(self):
        response = urlopen(self.get_server_url())
        self.assertEqual(response.code, 200)
