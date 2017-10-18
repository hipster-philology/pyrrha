from flask import url_for
from app.models import Corpus, WordToken, AllowedLemma
from app import db
from tests.test_selenium.base import TestBase
from tests.fixtures import PLAINTEXT_CORPORA


class TestCorpusRegistration(TestBase):
    """ Test creation of Corpus """
    def test_registration(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver.find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver.find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)

        self.assertIn(
            url_for('main.corpus_new'), self.driver.current_url,
            "Result page is the corpus new page"
        )

        self.assertEqual(
            db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).count(), 1,
            "There should be one well named corpus"
        )
        corpus = db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        tokens = db.session.query(WordToken).filter(WordToken.corpus == corpus.id)
        self.assertEqual(tokens.count(), 25, "There should be 25 tokens")

        saint = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "saint"))
        self.assertEqual(saint.count(), 1, "There should be the saint lemma")
        saint = saint.first()
        self.assertEqual(saint.form, "seint", "It should be correctly saved")
        self.assertEqual(saint.label_uniform, "saint", "It should be correctly saved and unidecoded")
        self.assertEqual(saint.POS, "ADJqua", "It should be correctly saved with POS")
        self.assertEqual(saint.morph, None, "It should be correctly saved with morph")

        oir = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "öir"))
        self.assertEqual(oir.count(), 1, "There should be the oir lemma")
        oir = oir.first()
        self.assertEqual(oir.form, "oïr", "It should be correctly saved")
        self.assertEqual(oir.label_uniform, "oir", "It should be correctly saved and unidecoded")
        self.assertEqual(oir.POS, "VERinf", "It should be correctly saved with POS")
        self.assertEqual(oir.morph, None, "It should be correctly saved with morph")

    def test_registration_with_full_allowed_lemma(self):
        """
        Test that a user can create a corpus wit allowed lemmas and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver.find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver.find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.writeMultiline(self.driver.find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["lemma"])
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)

        self.assertIn(
            url_for('main.corpus_new'), self.driver.current_url,
            "Result page is the corpus new page"
        )

        self.assertEqual(
            db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).count(), 1,
            "There should be one well named corpus"
        )
        corpus = db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        tokens = db.session.query(WordToken).filter(WordToken.corpus == corpus.id)
        self.assertEqual(tokens.count(), 25, "There should be 25 tokens")

        saint = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "saint"))
        self.assertEqual(saint.count(), 1, "There should be the saint lemma")
        saint = saint.first()
        self.assertEqual(saint.form, "seint", "It should be correctly saved")
        self.assertEqual(saint.label_uniform, "saint", "It should be correctly saved and unidecoded")
        self.assertEqual(saint.POS, "ADJqua", "It should be correctly saved with POS")
        self.assertEqual(saint.morph, None, "It should be correctly saved with morph")

        allowed = db.session.query(AllowedLemma).filter(AllowedLemma.corpus == corpus.id)
        self.assertEqual(allowed.count(), 21, "There should be 21 allowed token")

        # Checking the model
        self.assertEqual(corpus.get_unallowed("lemma").count(), 0, "There should be no unallowed value")

    def test_registration_with_partial_allowed_lemma(self):
        """
        Test that a user can create a corpus with wrong lemmas and a list of allowed lemmas
        and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver.find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver.find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.writeMultiline(self.driver.find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)

        self.assertIn(
            url_for('main.corpus_new'), self.driver.current_url,
            "Result page is the corpus new page"
        )

        self.assertEqual(
            db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).count(), 1,
            "There should be one well named corpus"
        )
        corpus = db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        tokens = db.session.query(WordToken).filter(WordToken.corpus == corpus.id)
        self.assertEqual(tokens.count(), 25, "There should be 25 tokens")

        saint = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "saint"))
        self.assertEqual(saint.count(), 1, "There should be the saint lemma")
        saint = saint.first()
        self.assertEqual(saint.form, "seint", "It should be correctly saved")
        self.assertEqual(saint.label_uniform, "saint", "It should be correctly saved and unidecoded")
        self.assertEqual(saint.POS, "ADJqua", "It should be correctly saved with POS")
        self.assertEqual(saint.morph, None, "It should be correctly saved with morph")

        allowed = db.session.query(AllowedLemma).filter(AllowedLemma.corpus == corpus.id)
        self.assertEqual(allowed.count(), 3, "There should be 21 allowed token")

        # Checking the model
        self.assertEqual(
            corpus.get_unallowed("lemma").count(), 22,
            "There should be 22 unallowed value as only de saint martin are allowed"
        )
