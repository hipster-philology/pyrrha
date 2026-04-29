import pytest

from tests.test_playwright.base import TokenCorrect2CorporaHelpers


class TokenEditBase(TokenCorrect2CorporaHelpers):
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def apply_new_filter(self, css_selector):
        self.page.locator(css_selector).click()

    def go_to_filter_similar_with(self, css_selector="a.partial", token_id="1", as_callback=True):
        def callback():
            row = self.page.locator(f"#token_{token_id}_row")
            similar_count_obj = row.locator(".at-cell.at-cell--sim")
            similar_count = similar_count_obj.text_content().strip()
            similar_count_obj.locator("a").click()
            self.apply_new_filter(css_selector)
            return similar_count

        if as_callback:
            return callback
        return callback()

    def get_main_table_body_rows(self):
        return self.page.locator(".main tbody tr").all()

    def get_main_table_annotation_rows(self):
        return self.page.locator("#annotation-table .at-row").all()

class TestTokenSimilarToTokenCorrect(TokenEditBase):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_edit_token(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, row = self.edith_nth_row_value(
            value="NOMcom",
            value_type="POS",
            id_row="82",
            additional_action_before=self.go_to_filter_similar_with(token_id="2"),
        )
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="saint", POS="NOMcom")

        similar_elem = self.get_similar_hint("82")
        assert similar_elem.text_content().strip().startswith("2 similar tokens")
        similar_elem.click()
        self.page.wait_for_load_state("networkidle")
        self.page.screenshot(path="edit_token.png")
        assert len(self.get_main_table_annotation_rows()) == 2, "There are two similar POS to edit"
        self.page.locator(".srt-apply-btn").click()
        try:
            self.wait_until_count(".at-table .at-row", 0)
        except Exception:
            pass
        assert len(self.get_main_table_annotation_rows()) == 0

    def test_filters_links(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        self.go_to_edit_token_page("1", as_callback=False)
        similar_count = self.go_to_filter_similar_with(token_id="2", as_callback=False)
        self.page.wait_for_load_state("networkidle")
        self.page.screenshot(path="similar_file.png")
        assert similar_count == "3", "There should be three similar tokens"
        assert len(self.get_main_table_annotation_rows()) == 3

        self.apply_new_filter("a.complete")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 0
        self.apply_new_filter("a.lemma")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 3
        self.apply_new_filter("a.POS")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 0
        self.apply_new_filter("a.morph")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 3
        self.apply_new_filter("a.lemma_ex")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 0
        self.apply_new_filter("a.POS_ex")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 3
        self.apply_new_filter("a.morph_ex")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 0

        self.go_to_edit_token_page("1", as_callback=False)
        self.page.wait_for_load_state("networkidle")
        similar_count = self.go_to_filter_similar_with(token_id="24", as_callback=False)
        self.page.wait_for_load_state("networkidle")
        assert similar_count == "3", "There should be three similar tokens"
        assert len(self.get_main_table_annotation_rows()) == 3

        self.apply_new_filter("a.complete")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 1
        self.apply_new_filter("a.lemma")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 1
        self.apply_new_filter("a.POS")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 1
        self.apply_new_filter("a.morph")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 3
        self.apply_new_filter("a.lemma_ex")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 2
        self.apply_new_filter("a.POS_ex")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 2
        self.apply_new_filter("a.morph_ex")
        self.page.wait_for_load_state("networkidle")
        assert len(self.get_main_table_annotation_rows()) == 0
