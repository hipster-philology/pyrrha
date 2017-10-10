from tests.test_selenium.base import TokenEdit2CorporaBase


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

    def test_filters_links(self):
        """ Check that links filter correctly the list """
        self.addCorpus(with_token=True, with_allowed_lemma=True)
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
