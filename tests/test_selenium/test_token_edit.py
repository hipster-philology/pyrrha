from tests.test_selenium.test_base import TestBase
from app.models import WordToken
import time


class TestTokenEdit(TestBase):
    """ Checks that token edition works correctly """

    def edit_first_row_lemma(self, value, value_type="lemma", id_row="1"):
        """ Helper to go to the right page and edit the first row

        :returns: Token that has been edited, Content of the save link td
        :rtype: WordToken, str
        """
        # Show the dropdown
        self.driver.find_element_by_id("toggle_corpus_1").click()
        # Click on the edit link
        self.driver.find_element_by_id("corpus_1_edit_tokens").click()
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

        # Save
        row.find_element_by_class_name("save").click()
        # It's safer to wait for the AJAX call to be completed
        time.sleep(2)

        return self.db.session.query(WordToken).get(int(id_row)), row.find_elements_by_tag_name("td")[-1].text.strip()

    def test_edit_token(self):
        """ Test the edition of a token """
        self.addWauchier(with_token=True)
        token, status_text = self.edit_first_row_lemma("un")
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")
