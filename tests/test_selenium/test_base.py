from flask_testing import LiveServerTestCase
from app import create_app, db

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
        db.session.commit()
        db.drop_all()
        db.create_all()
        db.session.commit()

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.get(self.get_server_url())

    def writeMultiline(self, element, text):
        """ Helper to write in multiline text

        :param element: Element in which to write the text
        :type element: selenium.webdriver.remote.webelement.WebElement
        :param text: Multiline text to write
        :return: element
        """
        self.driver.execute_script('arguments[0].value = arguments[1];', element, text)
        return element

    def tearDown(self):
        self.driver.quit()