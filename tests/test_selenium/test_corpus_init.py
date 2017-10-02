import time
from flask import url_for
from app.models import Corpus
from app import db
from tests.test_selenium.test_base import TestBase
from tests.fixtures import CORPUS_NAME, CORPUS_DATA


class TestCorpusRegistration(TestBase):

    def test_registration(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        time.sleep(1)

        # Fill in registration form
        self.driver.find_element_by_id("corpusName").send_keys(CORPUS_NAME)
        self.driver.find_element_by_id("tokens").send_keys(CORPUS_DATA)
        self.driver.find_element_by_id("submit").click()
        time.sleep(1)

        self.assertIn(
            url_for('main.corpus_new'), self.driver.current_url,
            "Result page is the corpus new page"
        )

        self.assertEqual(
            db.session.query(Corpus).filter_by(Corpus.name == CORPUS_NAME).count(), 1,
            "There should be one well named corpus"
        )
