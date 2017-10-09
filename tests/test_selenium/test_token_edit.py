from tests.test_selenium.base import TestBase
from app.models import WordToken
import time
import selenium


class TokenEditBase(TestBase):
    """ Base class with helpers to test token edition page """
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def edith_nth_row_value(
            self, value,
            value_type="lemma",
            id_row="1", corpus_id=None,
            autocomplete_selector=None):
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

        :returns: Token that has been edited, Content of the save link td
        :rtype: WordToken, str
        """
        if corpus_id is None:
            corpus_id = self.CORPUS_ID
        # Show the dropdown
        self.driver.find_element_by_id("toggle_corpus_"+corpus_id).click()
        # Click on the edit link
        self.driver.find_element_by_id("corpus_"+corpus_id+"_edit_tokens").click()
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


class TestTokenEditWauchierCorpus(TokenEditBase):
    def test_edit_token_lemma_with_allowed_values(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("un", id_row="1")
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "saint", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "martin", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_allowed_values_autocomplete(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "d", id_row="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='devoir']"
        )
        self.assertEqual(token.lemma, "devoir", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "PRE", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_POS(self):
        """ Edit POS of a token """
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "ADJqua", id_row="1", value_type="POS"
        )
        self.assertEqual(token.lemma, "de", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "ADJqua", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")


class TestTokensEditFloovant(TokenEditBase):
    CORPUS = "floovant"
    CORPUS_ID = "2"

    def test_edit_POS(self):
        """ Edit POS of a token """
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, status_text, row = self.edith_nth_row_value(
            "ADJqua", id_row="1", value_type="POS"
        )
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "ADJqua", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_allowed_values_lemma_pos(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_pos=True)
        token, status_text, row = self.edith_nth_row_value("estoire1", id_row="1")
        self.assertEqual(token.lemma, "estoire1", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "or4", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "escouter", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_allowed_values_lemma(self):
        """ Test the edition of a token's lemma and POS with allowed_lemma """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, status_text, row = self.edith_nth_row_value("estoire1", id_row="1")
        self.assertEqual(token.lemma, "estoire1", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "or4", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "escouter", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_morph_with_allowed_values_lemma(self):
        """ Test the edition of a token's morph  with allowed_lemma """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, status_text, row = self.edith_nth_row_value("SomeMorph", id_row="1", value_type="morph")
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed")
        self.assertEqual(token.morph, "SomeMorph", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_morph(self):
        """ Test the edition of a token's morph"""
        # Try first with an edit that would word
        self.addCorpus(with_token=True)
        token, status_text, row = self.edith_nth_row_value("SomeMorph", id_row="1", value_type="morph")
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed")
        self.assertEqual(token.morph, "SomeMorph", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_with_same_value(self):
        """ Test the edition of a token's morph"""
        # Try first with an edit that would word
        self.addCorpus(with_token=True)
        token, status_text, row = self.edith_nth_row_value("seignor", id_row="1", value_type="lemma")
        self.assertEqual(status_text, "(No value where changed) Save")
        self.assertNotIn("table-changed", row.get_attribute("class"))


class TestTokensEditTwoCorpora(TokenEditBase):
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def addCorpus(self, *args, **kwargs):
        super(TokenEditBase, self).addCorpus("wauchier", *args, **kwargs)
        super(TokenEditBase, self).addCorpus("floovant", *args, **kwargs)

    def test_edit_token_lemma_with_allowed_values_lemma_pos(self):
        """ Test the edition of a token """
        # Try first with an edit that would work
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_pos=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("saint", id_row="1")
        self.assertEqual(token.lemma, "saint", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an allowed lemma from the second corpus
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("seignor", id_row="2")
        self.assertEqual(token.lemma, "saint", "Lemma should not have been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "martin", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_typeahead_click(self):
        """ Test the edition of a token """
        # Try first with an edit that would work
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "s", id_row="1", corpus_id="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='saint']"
        )
        self.assertEqual(token.lemma, "saint", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an allowed lemma from the second corpus
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value(
            "s", id_row=str(self.first_token_id(2)+1), corpus_id="2",
            autocomplete_selector=".autocomplete-suggestion[data-val='seignor']"
        )
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an allowed lemma from the second corpus
        self.driver.refresh()
        with self.assertRaises(selenium.common.exceptions.NoSuchElementException):
            _ = self.edith_nth_row_value(
                "s", id_row=str(self.first_token_id(2)+1), corpus_id="2",
                autocomplete_selector=".autocomplete-suggestion[data-val='saint']"
            )
