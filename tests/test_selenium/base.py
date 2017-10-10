from flask_testing import LiveServerTestCase
import os
import signal
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

from app import db, create_app
from tests.db_fixtures import add_corpus
from app.models import WordToken

LIVESERVER_TIMEOUT = 1


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

    def _terminate_live_server(self):
        if self._process:
            try:
                os.kill(self._process.pid, signal.SIGINT)
                self._process.join(LIVESERVER_TIMEOUT)
            except Exception as ex:
                logging.error('Failed to join the live server process: %r', ex)
            finally:
                if self._process.is_alive():
                    # If it's still alive, kill it
                    self._process.terminate()

    def tearDown(self):
        self.driver.quit()

    def addCorpus(self, corpus, *args, **kwargs):
        if corpus == "wauchier":
            add_corpus("wauchier", db, *args, **kwargs)
        else:
            add_corpus("floovant", db, *args, **kwargs)
        self.driver.get(self.get_server_url())
        self.driver.refresh()


class TokenEditBase(TestBase):
    """ Base class with helpers to test token edition page """
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def go_to_edit_token_page(self, corpus_id, as_callback=True):
        """ Go to the corpus's edit token page """
        def callback():
            # Show the dropdown
            self.driver.find_element_by_id("toggle_corpus_"+corpus_id).click()
            # Click on the edit link
            self.driver.find_element_by_id("corpus_"+corpus_id+"_edit_tokens").click()
        if as_callback:
            return callback
        callback()

    def edith_nth_row_value(
            self, value,
            value_type="lemma",
            id_row="1", corpus_id=None,
            autocomplete_selector=None,
            additional_action_before=None,
            go_to_edit_token_page=None):
        """ Helper to go to the right page and edit the first row

        :param value: Value to write
        :type value: str
        :param value_type: Type of value to edit (lemma, form, context)
        :type value_type: str
        :param id_row: ID of the row to edit
        :type corpus_id: str
        :param corpus_id: ID of the corpus to edit
        :type corpus_id: str
        :param autocomplete_selector: Selector that match an autocomplete suggestion that will be clicked
        :type autocomplete_selector: str
        :param additional_action_before: Action to perform between page reaching and token editing
        :type additional_action_before: Callable

        :returns: Token that has been edited, Content of the save link td
        :rtype: WordToken, str
        """
        if corpus_id is None:
            corpus_id = self.CORPUS_ID

        if go_to_edit_token_page is None:
            go_to_edit_token_page = self.go_to_edit_token_page(corpus_id)
        go_to_edit_token_page()

        if additional_action_before is not None:
            additional_action_before()

        # Take the first row
        row = self.driver.find_element_by_id("token_"+id_row+"_row")
        # Take the td to edit
        if value_type == "POS":
            td = row.find_element_by_class_name("token_pos")
        elif value_type == "morph":
            td = row.find_element_by_class_name("token_morph")
        else:
            td = row.find_element_by_class_name("token_lemma")

        # Click, clear the td and send a new value
        td.click(), td.clear(), td.send_keys(value)

        if autocomplete_selector is not None:
            time.sleep(1.5)
            self.driver.find_element_by_css_selector(autocomplete_selector).click()
        time.sleep(0.5)
        # Save
        row.find_element_by_class_name("save").click()
        # It's safer to wait for the AJAX call to be completed
        time.sleep(1)

        return self.db.session.query(WordToken).get(int(id_row)), row.find_elements_by_tag_name("td")[-1].text.strip(), row

    def first_token_id(self, corpus_id):
        return self.db.session.query(WordToken.id).\
            filter_by(corpus=corpus_id).order_by(WordToken.order_id).limit(1).first()[0]

    def addCorpus(self, *args, **kwargs):
        return super(TokenEditBase, self).addCorpus(self.CORPUS, *args, **kwargs)

    def test_edit_token(self):
        """ Test the edition of a token """
        self.addCorpus(with_token=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("un", corpus_id=self.CORPUS_ID)
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")
        self.assertIn("table-changed", row.get_attribute("class"))
        self.driver.refresh()
        row = self.driver.find_element_by_id("token_1_row")
        self.assertIn("table-changed", row.get_attribute("class"))


class TokenEdit2CorporaBase(TokenEditBase):
    def addCorpus(self, *args, **kwargs):
        super(TokenEditBase, self).addCorpus("wauchier", *args, **kwargs)
        super(TokenEditBase, self).addCorpus("floovant", *args, **kwargs)