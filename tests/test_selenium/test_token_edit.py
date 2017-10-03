from tests.test_selenium.test_base import TestBase
from app.models import WordToken
import time


class TestTokenEdit(TestBase):
    """ Checks that token edition works correctly """

    def edith_nth_row_value(
            self, value,
            value_type="lemma",
            id_row="1", corpus_id="1",
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

        return self.db.session.query(WordToken).get(int(id_row)), row.find_elements_by_tag_name("td")[-1].text.strip()

    def test_edit_token(self):
        """ Test the edition of a token """
        self.addWauchier(with_token=True)
        token, status_text = self.edith_nth_row_value("un")
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_with_allowed_values(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addWauchier(with_token=True, with_allowed_lemma=True)
        token, status_text = self.edith_nth_row_value("un", id_row="1")
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "saint", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "martin", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_with_allowed_values_autocomplete(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addWauchier(with_token=True, with_allowed_lemma=True)
        token, status_text = self.edith_nth_row_value(
            "d", id_row="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='devoir']"
        )
        self.assertEqual(token.lemma, "devoir", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "PRE", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")
