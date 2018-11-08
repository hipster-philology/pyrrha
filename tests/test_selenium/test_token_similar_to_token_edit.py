from tests.test_selenium.base import TokenEdit2CorporaBase
import time


class TokenEditBase(TokenEdit2CorporaBase):
    """ Base class with helpers to test token edition page """
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def apply_new_filter(self, css_selector):
        self.driver.find_element_by_css_selector(css_selector).click()

    def go_to_filter_similar_with(self, css_selector="a.partial", token_id="1", as_callback=True):
        def callback():
            row = self.driver.find_element_by_id("token_"+token_id+"_row")
            similar_count_obj = row.find_element_by_css_selector("a.similar-link")
            similar_count = similar_count_obj.text
            similar_count_obj.click()
            self.apply_new_filter(css_selector)
            return similar_count
        if as_callback:
            return callback
        return callback()

    def get_main_table_body_rows(self):
        return self.driver.find_elements_by_css_selector(".main tbody tr")

    def test_edit_token(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, text, row = self.edith_nth_row_value(
            value="NOMcom", value_type="POS", id_row="82",
            additional_action_before=self.go_to_filter_similar_with(token_id="2"),

        )
        self.assertEqual(token.lemma, "saint", "Lemma has been kept")
        self.assertEqual(token.POS, "NOMcom", "POS has been changed")
        self.assertEqual(text, "(Saved) Save 2 similar to see", "POS has been changed")
        # Go to find similar
        row.find_element_by_class_name("similar-link").click()
        # Count the number of similar case
        self.assertEqual(len(self.get_main_table_body_rows()), 2, "There is two similar POS to edit")
        # Apply changes to the two others
        self.driver.find_element_by_css_selector(".save-lemma").click()
        time.sleep(0.2)
        self.assertEqual(len(self.get_main_table_body_rows()), 0, "There is two similar POS to edit")

    def test_filters_links(self):
        """ Check that links filter correctly the list """
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        # Go to token "saint" which is POSed as VERcjg sometimes
        self.go_to_edit_token_page("1", as_callback=False)
        similar_count = self.go_to_filter_similar_with(token_id="2", as_callback=False)
        self.assertEqual(similar_count, "3", "There should be three similar tokens")
        # We are by default on partial !
        self.assertEqual(len(self.get_main_table_body_rows()), 3, "There is 3 partial match")
        # Then we go to complete
        self.apply_new_filter("a.complete")
        self.assertEqual(len(self.get_main_table_body_rows()), 0, "There is 0 complete match")
        # Then we go to lemma
        self.apply_new_filter("a.lemma")
        self.assertEqual(len(self.get_main_table_body_rows()), 3, "There is 3 lemma match")
        # Then we go to lemma
        self.apply_new_filter("a.POS")
        self.assertEqual(len(self.get_main_table_body_rows()), 0, "There is 3 POS match")
        # Then we go to lemma
        self.apply_new_filter("a.morph")
        self.assertEqual(len(self.get_main_table_body_rows()), 3, "There is 3 morph match")
        # Then we go to lemma exluded
        self.apply_new_filter("a.lemma_ex")
        self.assertEqual(len(self.get_main_table_body_rows()), 0, "There is 0 lemma excluded match")
        # Then we go to POS excluded
        self.apply_new_filter("a.POS_ex")
        self.assertEqual(len(self.get_main_table_body_rows()), 3, "There is 3 POS excluded match")
        # Then we go to Morph excluded
        self.apply_new_filter("a.morph_ex")
        self.assertEqual(len(self.get_main_table_body_rows()), 0, "There is 0 morph excluded match")

        # Go to token "l" which is lemmatized and POSED differently
        self.go_to_edit_token_page("1", as_callback=False)
        similar_count = self.go_to_filter_similar_with(token_id="24", as_callback=False)
        self.assertEqual(similar_count, "3", "There should be three similar tokens")
        # We are by default on partial !
        self.assertEqual(len(self.get_main_table_body_rows()), 3, "There is 3 partial match")
        # Then we go to complete
        self.apply_new_filter("a.complete")
        self.assertEqual(len(self.get_main_table_body_rows()), 1, "There is 1 complete match")
        # Then we go to lemma
        self.apply_new_filter("a.lemma")
        self.assertEqual(len(self.get_main_table_body_rows()), 1, "There is 1 lemma match")
        # Then we go to POS
        self.apply_new_filter("a.POS")
        self.assertEqual(len(self.get_main_table_body_rows()), 1, "There is 1 POS match")
        # Then we go to Morph
        self.apply_new_filter("a.morph")
        self.assertEqual(len(self.get_main_table_body_rows()), 3, "There is 3 morph match")
        # Then we go to lemma exluded
        self.apply_new_filter("a.lemma_ex")
        self.assertEqual(len(self.get_main_table_body_rows()), 2, "There is 2 lemma excluded match")
        # Then we go to POS excluded
        self.apply_new_filter("a.POS_ex")
        self.assertEqual(len(self.get_main_table_body_rows()), 2, "There is 2 POS excluded match")
        # Then we go to Morph excluded
        self.apply_new_filter("a.morph_ex")
        self.assertEqual(len(self.get_main_table_body_rows()), 0, "There is 0 morph excluded match")
