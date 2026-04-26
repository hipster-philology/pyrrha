import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from sqlalchemy import text

from tests.test_playwright.base import TokenCorrect2CorporaHelpers, TokenCorrectHelpers


class TestTokenCorrectWauchierCorpus(TokenCorrectHelpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_edit_token(self):
        self.addCorpus(with_token=True, tokens_up_to=24)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("un", corpus_id=self.CORPUS_ID)
        assert token.lemma == "un", "Lemma should have been changed"
        assert status_text == "Save"
        self.assert_saved(row)
        assert "table-changed" in row.get_attribute("class")
        self.page.reload()
        row = self.page.locator("#token_1_row")
        assert "table-changed" in row.get_attribute("class")

    def test_edit_token_lemma_with_allowed_values(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("un", id_row="1")
        self.assert_token_has_values(token, lemma="un")
        self.assert_saved(row)

        self.page.reload()
        self.page.wait_for_load_state("networkidle")
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assert_token_has_values(token, lemma="saint")
        self.assert_invalid_value(row, "lemma")

        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assert_token_has_values(token, lemma="martin", POS="ADJqua")
        self.assert_saved(row)

    def test_edit_token_lemma_with_allowed_values_autocomplete(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value(
            "d",
            id_row="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='devoir']",
        )
        self.assert_token_has_values(token, lemma="devoir", POS="PRE")
        self.assert_saved(row)

    def test_edit_POS(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("ADJqua", id_row="1", value_type="POS")
        self.assert_token_has_values(token, lemma="de", POS="ADJqua")
        self.assert_saved(row)

    def test_edit_morph(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("_", id_row="1", value_type="morph")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="de", POS="PRE", morph="_")

        token, status_text, row = self.edith_nth_row_value("Not Allowed", id_row="2", value_type="morph")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="saint", POS="ADJqua", morph="Not Allowed")

    def test_edit_morph_with_allowed(self):
        self.addCorpus(
            with_token=True,
            with_allowed_lemma=True,
            with_allowed_morph=True,
            tokens_up_to=24,
        )
        self.page.goto(self.url_for("main.index"))
        token, status_text, row = self.edith_nth_row_value("_", id_row="1", value_type="morph")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="de", POS="PRE", morph="_")

        token, status_text, row = self.edith_nth_row_value("Not Allowed", id_row="2", value_type="morph")
        self.assert_invalid_value(row, "morph")
        self.assert_token_has_values(token, lemma="saint", POS="ADJqua", morph="None")

        token, status_text, row = self.edith_nth_row_value(
            "masc sing",
            id_row="3",
            corpus_id="1",
            value_type="morph",
            autocomplete_selector=".autocomplete-suggestion[data-val='NOMB.=s|GENRE=m|CAS=n']",
        )
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="martin", POS="NOMpro", morph="NOMB.=s|GENRE=m|CAS=n")

        token, status_text, row = self.edith_nth_row_value(
            "NOMB.=s GENRE=m",
            id_row="4",
            corpus_id="1",
            value_type="morph",
            autocomplete_selector=".autocomplete-suggestion[data-val='NOMB.=s|GENRE=m|CAS=n']",
        )
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="mout", POS="ADVgen", morph="NOMB.=s|GENRE=m|CAS=n")

    def test_edit_token_with_filter(self):
        corpus = self.addCorpus(with_token=True, cl=True, with_allowed_lemma=True)
        self.addControlListsUser(corpus.control_lists_id, self.app.config["ADMIN_EMAIL"], is_owner=True)
        self.page.reload()

        token, status_text, row = self.edith_nth_row_value("#", id_row="1")
        assert token.lemma != "#", "Lemma # is forbidden in control list"

        self.page.get_by_role("link", name="Dashboard", exact=True).click()
        controllists_dashboard = self.page.locator("#control_lists-dashboard")
        controllists_dashboard.get_by_role("link", name="Wauchier").click()
        self.page.get_by_role("link", name="Ignore values").click()
        self.page.locator("[name='punct']").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        token, status_text, row = self.edith_nth_row_value("]", value_type="lemma", id_row="1")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="]")


class TestTokensCorrectFloovant(TokenCorrectHelpers):
    CORPUS = "floovant"
    CORPUS_ID = "2"

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_edit_POS(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("ADJqua", id_row="1", value_type="POS")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="seignor", POS="ADJqua")

    def test_edit_token_lemma_with_allowed_values_lemma_pos(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_pos=True)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("estoire1", id_row="1")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="estoire1")

        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assert_invalid_value(row, "lemma")
        self.assert_token_has_values(token, lemma="or4")

        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="escouter", POS="ADJqua")

    def test_edit_token_morph_with_allowed_values_lemma(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("SomeMorph", id_row="1", value_type="morph")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="seignor", morph="SomeMorph")

    def test_edit_token_morph(self):
        self.addCorpus(with_token=True)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("SomeMorph", id_row="1", value_type="morph")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="seignor", morph="SomeMorph")

    def test_edit_token_with_same_value(self):
        self.addCorpus(with_token=True)
        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("seignor", id_row="1", value_type="lemma")
        self.assert_unchanged(row)
        assert "table-changed" not in row.get_attribute("class")


class TestTokensEditTwoCorpora(TokenCorrect2CorporaHelpers):
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_edit_token_lemma_with_allowed_values_lemma_pos(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_pos=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("saint", id_row="1")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="saint")

        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("seignor", id_row="2")
        self.assert_invalid_value(row, "lemma")
        self.assert_token_has_values(token, lemma="saint")

        self.page.reload()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="martin", POS="ADJqua")

    def test_edit_token_lemma_with_typeahead_click(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "s",
            id_row="1",
            corpus_id="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='saint']",
        )
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="saint")
        assert row.locator("b").nth(0).text_content() == token.form

        self.page.reload()
        second_corpus_first_id = str(self.first_token_id(2) + 1)
        token, status_text, row = self.edith_nth_row_value(
            "s",
            id_row=second_corpus_first_id,
            corpus_id="2",
            autocomplete_selector=".autocomplete-suggestion[data-val='seignor']",
        )
        self.assert_saved(row)
        self.assert_token_has_values(token, lemma="seignor")

        self.page.reload()
        with pytest.raises(PlaywrightTimeoutError):
            self.edith_nth_row_value(
                "s",
                id_row=second_corpus_first_id,
                corpus_id="2",
                autocomplete_selector=".autocomplete-suggestion[data-val='saint']",
            )

    def test_correct_delete(self):
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("saint", id_row="1")
        self.assert_saved(row)
        from app import db as _db
        assert len(_db.session.execute(text("SELECT * FROM change_record")).all()) == 1

        self.token_dropdown_link(1, "Delete")
        inp = self.page.locator("input[name='form']")
        inp.fill("De")
        self.page.locator("button[type='submit']").click()

        row = self.page.locator("tr.token-anchor[data-token-order='1']").first
        assert row.locator("td").nth(1).text_content() == "seint", "Token was removed"

        self.page.locator('a[title="Browse the annotations\' history"]').click()
        self.page.wait_for_load_state("networkidle")
        assert len(_db.session.execute(text("SELECT * FROM change_record")).all()) == 1
        self.page.screenshot(path="truc.png")
        history_rows = self.page.locator("tbody tr.history").all()
        assert len(history_rows) == 1
