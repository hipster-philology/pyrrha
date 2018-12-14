from flask import url_for
from app.models import Corpus, WordToken, AllowedLemma, AllowedMorph
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
        self.driver.get_screenshot_as_file("here.png")
        self.assertIn(
            url_for('main.corpus_get', corpus_id=1), self.driver.current_url,
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
            url_for('main.corpus_get', corpus_id=1), self.driver.current_url,
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

        allowed = db.session.query(AllowedLemma).filter(AllowedLemma.control_list == corpus.control_lists_id)
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
            url_for('main.corpus_get', corpus_id=1), self.driver.current_url,
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
        self.assertEqual(saint.context, "De seint Martin mout doit")

        allowed = db.session.query(AllowedLemma).filter(AllowedLemma.control_list == corpus.control_lists_id)
        self.assertEqual(allowed.count(), 3, "There should be 21 allowed token")

        # Checking the model
        self.assertEqual(
            corpus.get_unallowed("lemma").count(), 22,
            "There should be 22 unallowed value as only de saint martin are allowed"
        )

    def test_registration_with_allowed_morph(self):

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver.find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver.find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.writeMultiline(self.driver.find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.writeMultiline(self.driver.find_element_by_id("allowed_morph"), PLAINTEXT_CORPORA["Wauchier"]["morph"])
        self.driver.find_element_by_id("submit").click()

        self.assertIn(
            url_for('main.corpus_get', corpus_id=1), self.driver.current_url,
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

        allowed = db.session.query(AllowedLemma).filter(AllowedLemma.control_list == corpus.control_lists_id)
        self.assertEqual(allowed.count(), 3, "There should be 3 allowed lemma")

        allowed = db.session.query(AllowedMorph).filter(AllowedMorph.control_list == corpus.control_lists_id)
        self.assertEqual(allowed.count(), 145, "There should be 145 different possible Morphs")

        # Checking the model
        self.assertEqual(
            corpus.get_unallowed("lemma").count(), 22,
            "There should be 22 unallowed value as only de saint martin are allowed"
        )

    def test_registration_with_context(self):
        """
        Test that a user can create a corpus with wrong lemmas and a list of allowed lemmas
        and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver.find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.driver.find_element_by_id("context_left").clear()
        self.driver.find_element_by_id("context_left").send_keys("5")
        self.driver.find_element_by_id("context_right").clear()
        self.driver.find_element_by_id("context_right").send_keys("2")
        self.writeMultiline(self.driver.find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.writeMultiline(self.driver.find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)

        self.assertEqual(
            db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).count(), 1,
            "There should be one well named corpus"
        )
        corpus = db.session.query(Corpus).filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        tokens = db.session.query(WordToken).filter(WordToken.corpus == corpus.id)
        self.assertEqual(tokens.count(), 25, "There should be 25 tokens")

        # De seint Martin mout doit on doucement et volentiers le bien oïr et entendre , car par le bien
        # savoir et retenir puet l
        saint = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "volentiers"))
        self.assertEqual(saint.count(), 1, "There should be the saint lemma")
        saint = saint.first()
        self.assertEqual(saint.form, "volentiers", "It should be correctly saved")
        self.assertEqual(saint.context, "mout doit on doucement et volentiers le bien")

    def test_corpus_with_quotes(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        name = "GUILLEMETS DE MONTMURAIL"
        self.driver.find_element_by_id("corpusName").send_keys(name)
        self.writeMultiline(
            self.driver.find_element_by_id("tokens"),
            "tokens\tlemmas\tPOS\tmorph\n"
            "\"\t\"\tPONC\tMORPH=EMPTY\n"  # Testing with " Quote Char
            "\'\t\'\tPONC\tMORPH=EMPTY\n"  # Testing with ' Quote Char
            "“\t“\tPONC\tMORPH=EMPTY\n"  # Testing with “ Quote Char
            "”\t”\tPONC\tMORPH=EMPTY\n"  # Testing with ” Quote Char
            "«\t«\tPONC\tMORPH=EMPTY\n"  # Testing with « Quote Char
            "»\t»\tPONC\tMORPH=EMPTY\n"  # Testing with » Quote Char
            "‘\t‘\tPONC\tMORPH=EMPTY\n"  # Testing with ‘ Quote Char
            "’\t’\tPONC\tMORPH=EMPTY\n"  # Testing with ’ Quote Char
            "„\t„\tPONC\tMORPH=EMPTY\n"  # Testing with „ Quote Char
            "《\t《\tPONC\tMORPH=EMPTY\n"  # Testing with „ Quote Char
            "》\t》\tPONC\tMORPH=EMPTY\n"  # Testing with „ Quote Char
        )
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)

        self.assertIn(
            url_for('main.corpus_get', corpus_id=1), self.driver.current_url,
            "Result page is the corpus new page"
        )

        self.assertEqual(
            db.session.query(Corpus).filter(Corpus.name == name).count(), 1,
            "There should be one well named corpus"
        )
        corpus = db.session.query(Corpus).filter(Corpus.name == name).first()
        tokens = db.session.query(WordToken).filter(WordToken.corpus == corpus.id)
        self.assertEqual(tokens.count(), 11, "There should be 11 tokens")
        self.assertEqual(
            WordToken.to_input_format(tokens).replace("\r", ""),
            "token_id\tform\tlemma\tPOS\tmorph\n"
            "1\t\\\"\t\\\"\tPONC\tMORPH=EMPTY\n"  # Testing with " Quote Char
            "2\t\'\t\'\tPONC\tMORPH=EMPTY\n"  # Testing with ' Quote Char
            "3\t“\t“\tPONC\tMORPH=EMPTY\n"  # Testing with “ Quote Char
            "4\t”\t”\tPONC\tMORPH=EMPTY\n"  # Testing with ” Quote Char
            "5\t«\t«\tPONC\tMORPH=EMPTY\n"  # Testing with « Quote Char
            "6\t»\t»\tPONC\tMORPH=EMPTY\n"  # Testing with » Quote Char
            "7\t‘\t‘\tPONC\tMORPH=EMPTY\n"  # Testing with ‘ Quote Char
            "8\t’\t’\tPONC\tMORPH=EMPTY\n"  # Testing with ’ Quote Char
            "9\t„\t„\tPONC\tMORPH=EMPTY\n"  # Testing with „ Quote Char
            "10\t《\t《\tPONC\tMORPH=EMPTY\n"  # Testing with „ Quote Char
            "11\t》\t》\tPONC\tMORPH=EMPTY\n"  # Testing with „ Quote Char
        )