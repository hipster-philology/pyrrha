from flask_testing import LiveServerTestCase

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from app import db, create_app
from tests.db_fixtures import add_wauchier


class TestBase(LiveServerTestCase):
    db = db

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

    def addWauchier(self, *args, **kwargs):
        """ Add the Wauchier Corpus to fixtures

        :param with_token: Add tokens as well
        :param with_allowed_lemma: Add allowed lemma to db
        :param partial_allowed_lemma: Restrict to first three allowed lemma (de saint martin)
        :param with_allowed_pos: Add allowed POS to db
        :param partial_allowed_pos: Restrict to first three allowed POS (ADJqua, NOMpro, CONcoo)
        """
        add_wauchier(db, *args, **kwargs)
        self.driver.get(self.get_server_url())
        self.driver.refresh()
