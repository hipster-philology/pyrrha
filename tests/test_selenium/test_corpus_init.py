from flask import url_for
from app.models import Corpus, WordToken, AllowedLemma, AllowedMorph, AllowedPOS, ControlLists
from app import db
from tests.test_selenium.base import TestBase
from tests.fixtures import PLAINTEXT_CORPORA
import csv
import os


class TestCorpusRegistration(TestBase):
    """ Test creation of Corpus """
    def test_registration(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.driver_find_element_by_id("submit").click()

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
        self.assertEqual(corpus.delimiter_token, None, "We did not set a delimiter token")

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
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.writeMultiline(self.driver_find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["lemma"])
        self.driver_find_element_by_id("submit").click()
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
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.writeMultiline(self.driver_find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.driver_find_element_by_id("submit").click()
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
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.writeMultiline(self.driver_find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.writeMultiline(self.driver_find_element_by_id("allowed_morph"), PLAINTEXT_CORPORA["Wauchier"]["morph"])
        self.driver_find_element_by_id("submit").click()

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
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.driver_find_element_by_id("context_left").clear()
        self.driver_find_element_by_id("context_left").send_keys("5")
        self.driver_find_element_by_id("context_right").clear()
        self.driver_find_element_by_id("context_right").send_keys("2")
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.writeMultiline(self.driver_find_element_by_id("allowed_lemma"), PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.driver_find_element_by_id("submit").click()
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

    def test_tokenization(self):
        """ Ensure that tokenisation is working as expected """
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)
        self.writeMultiline(self.driver_find_element_by_id("tokens"), "Ci gist mon seignor")
        self.driver_find_element_by_id("tokenize").click()
        self.assertEqual(
            "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n",
            self.driver_find_element_by_id("tokens").get_property("value"),
            "Tokenization tokenizes"
        )
        self.assertEqual(
            True,
            self.driver_find_element_by_id("punct-keep").get_property("checked"),
            "The punctuation is checked by default"
        )
        # Check with punctuation
        self.driver_find_element_by_id("tokens").clear()
        self.writeMultiline(self.driver_find_element_by_id("tokens"), "Ci gist mon seignor...")
        self.driver_find_element_by_id("tokenize").click()
        self.assertEqual(
            "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n.\t\t\t\n.\t\t\t\n.\t\t\t\n",
            self.driver_find_element_by_id("tokens").get_property("value"),
            "Tokenization keeps punctuation"
        )
        # Check with punctuation removed
        self.driver_find_element_by_id("tokens").clear()
        self.writeMultiline(self.driver_find_element_by_id("tokens"), "Ci gist mon seignor...")
        self.driver_find_element_by_id("punct-keep").click()
        self.driver_find_element_by_id("tokenize").click()
        self.assertEqual(
            "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n",
            self.driver_find_element_by_id("tokens").get_property("value"),
            "Tokenization removed punctuation"
        )
        # Check with punctuation removed and hyphens
        self.driver_find_element_by_id("tokens").clear()
        self.writeMultiline(self.driver_find_element_by_id("tokens"), "Ci gist mon sei- gnor...")
        self.driver_find_element_by_id("hyphens-remove").click()
        self.driver_find_element_by_id("tokenize").click()
        self.assertEqual(
            "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n",
            self.driver_find_element_by_id("tokens").get_property("value"),
            "Tokenization removed punctuation and glued back hyphens"
        )

    def test_corpus_with_quotes(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        name = "GUILLEMETS DE MONTMURAIL"
        self.driver_find_element_by_id("corpusName").send_keys(name)
        self.writeMultiline(
            self.driver_find_element_by_id("tokens"),
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
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.driver_find_element_by_id("submit").click()
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

    def test_registration_with_existing_control_list(self):
        self.add_control_lists()
        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Target control list
        target_cl = db.session.query(ControlLists).\
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_"+str(target_cl.id)).click()
        self.driver_find_element_by_id("submit").click()

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

        control_list = db.session.query(ControlLists).filter(ControlLists.id == corpus.control_lists_id).first()
        self.assertEqual(
            "Ancien Français - École des Chartes", control_list.name,
            "The control list has been reused"
        )
        self.driver_find_element_by_id("toggle_controllists").click()
        self.assertEqual(
            self.driver_find_element_by_class_name("dd-control_list").text,
            "Ancien Français - École des Chartes",
            "The control list is available from the top menu"
        )

    def test_registration_with_false_control_list(self):
        """ [Corpus Creation] Check that a non existing control list cannot be used"""
        self.add_control_lists()
        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Target control list
        target_cl = db.session.query(ControlLists).\
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_"+str(target_cl.id)).click()
        # Change the value from JS
        self.driver.execute_script(
            "document.getElementById('cl_opt_"+str(target_cl.id)+"').value = '99999';"
        )
        self.driver_find_element_by_id("submit").click()

        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-danger").text.strip(),
            'This control list does not exist',
            "It is impossible to validate form with a wrong id of control list"
        )

    def test_registration_with_an_existing_name(self):
        """ [Corpus Creation] Check that a corpus using this name does not already exist"""
        self.addCorpus("wauchier")
        self.add_control_lists()
        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Target control list
        target_cl = db.session.query(ControlLists).\
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_"+str(target_cl.id)).click()

        self.driver_find_element_by_id("submit").click()

        self.assertEqual(
            sorted([e.text.strip() for e in self.driver_find_elements_by_css_selector(".alert.alert-danger")]),
            sorted([
                'The corpus cannot be registered. Check your data',
                "You have already a corpus going by the name Wauchier"
            ]),
            "Creating a corpus when one already exists for the current user with the same name fails."
        )

    def test_registration_with_wrongly_formated_input(self):
        """ [Corpus Creation] Check that TSV formatting does not break everything"""
        self.add_control_lists()
        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Target control list
        target_cl = db.session.query(ControlLists). \
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), """lala	lemma	POS	morph
SOIGNORS	seignor	NOMcom	NOMB.=p|GENRE=m|CAS=n
or	or4	ADVgen	DEGRE=-
escoutez	escouter	VERcjg	MODE=imp|PERS.=2|NOMB.=p
que	que4	CONsub	_
	dieu	NOMpro	NOMB.=s|GENRE=m|CAS=n
vos	vos1	PROper	PERS.=2|NOMB.=p|GENRE=m|CAS=r
soit	estre1	VERcjg	MODE=sub|TEMPS=pst|PERS.=3|NOMB.=s""")
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_" + str(target_cl.id)).click()

        self.driver_find_element_by_id("submit").click()

        self.assertEqual(
            sorted([e.text.strip() for e in self.driver_find_elements_by_css_selector(".alert.alert-danger")]),
            sorted([
                'At least one line of your corpus is missing a token/form. Check line 1'
            ]),
            "Creating a corpus with a missing tokens column fails."
        )

    def test_registration_with_no_tsv_input(self):
        """ [Corpus Creation] Check that missing TSV throws a specific error"""
        self.add_control_lists()
        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Target control list
        target_cl = db.session.query(ControlLists). \
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_" + str(target_cl.id)).click()

        self.driver_find_element_by_id("submit").click()

        self.assertEqual(
            sorted([e.text.strip() for e in self.driver_find_elements_by_css_selector(".alert.alert-danger")]),
            sorted([
                'You did not input any text.'
            ]),
            "Creating a corpus without TSV input fails."
        )

    def test_registration_with_sep_token(self):
        """ Test that a user can create a corpus with a delimiter token
        """

        # Click register menu link
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)

        # Fill in registration form
        self.driver_find_element_by_id("corpusName").send_keys(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.writeMultiline(self.driver_find_element_by_id("tokens"), PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.driver_find_element_by_id("sep_token").send_keys("____")
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.driver_find_element_by_id("submit").click()

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
        self.assertEqual(corpus.delimiter_token, "____", "There should be a delimiter token")

    def test_registration_upload_file(self):
        """Test that an user can upload a file to fill in 'tokens' textarea."""

        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver.implicitly_wait(15)
        upload = self.driver_find_element_by_id("upload")
        temp_file = self.create_temp_example_file()
        upload.send_keys(temp_file.name)
        self.driver.implicitly_wait(15)
        tokens = self.driver_find_element_by_id("tokens")
        with open(temp_file.name) as fp:
            self.assertCountEqual(
                [row for row in csv.reader(tokens.get_attribute("value").split("\n"), delimiter="\t") if row],
                [row for row in csv.reader(open(fp.name), delimiter="\t")]
            )
        os.remove(temp_file.name)

    def test_registration_with_field_length_violation(self):
        """Test registrating tokens violating field length constraint.

        Trying: column 'form' violates field length
        Expecting: alert is displayed
        """
        self.add_control_lists()
        target_cl = db.session.query(ControlLists). \
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # prepare form
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver_find_element_by_id("corpusName").send_keys("example")
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_" + str(target_cl.id)).click()
        invalid = "btOUZvzXARqNbnmvVIrcqjAbsRGIvZQsrhspGusZypNlUJSubtOztbiMiwipTpQJVTvSDZyIGCaONJ"
        self.writeMultiline(
            self.driver_find_element_by_id("tokens"),
            f"form\tlemma\tPOS\tmorph\n{invalid}\tseignor\tNOMcom\tNOMB.=p|GENRE=m|CAS=n"
        )

        # submit and wait
        self.driver_find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)
        self.assertEqual(
            self.driver_find_elements_by_css_selector(".alert.alert-danger")[0].text.strip(),
            f"ln. 2, column 'form': '{invalid}' is too long (maximum 64 characters)"
        )

    def test_registration_without_field_length_violation(self):
        """Test registrating tokens respecting field length constraint.

        Trying: field length violations
        Expecting: no alert is displayed
        """
        self.add_control_lists()
        target_cl = db.session.query(ControlLists). \
            filter(ControlLists.name == "Ancien Français - École des Chartes").first()

        # prepare form
        self.driver_find_element_by_id("new_corpus_link").click()
        self.driver_find_element_by_id("corpusName").send_keys("example")
        self.driver_find_element_by_id("label_checkbox_reuse").click()
        self.driver_find_element_by_id("control_list_select").click()
        self.driver_find_element_by_id("cl_opt_" + str(target_cl.id)).click()
        self.writeMultiline(
            self.driver_find_element_by_id("tokens"),
            f"form\tlemma\tPOS\tmorph\nSOIGNORS\tseignor\tNOMcom\tNOMB.=p|GENRE=m|CAS=n"
        )

        # submit and wait
        self.driver_find_element_by_id("submit").click()
        self.driver.implicitly_wait(15)
        self.assertFalse(self.driver_find_elements_by_css_selector(".alert.alert-danger"))
