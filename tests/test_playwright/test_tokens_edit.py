import pytest

from tests.db_fixtures.wauchier import WauchierTokens
from tests.test_playwright.base import Helpers


class TestTokenEdit(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def change_form_value(self, value):
        inp = self.page.locator("input[name='form']")
        inp.fill(value)
        self.page.screenshot(path=f"token_{value}.png")

    def select_context_around(self, tok_id, max_id=len(WauchierTokens)):
        return [
            self.page.locator(f"#token_{cur}_row").locator("td").nth(5).text_content().strip()
            for cur in range(
                max(tok_id - 3, 0),
                min(max_id, tok_id + 3 + 2),
            )
        ]

    def get_history(self):
        self.page.locator("a[title='Browse editions of the base text']").click()
        self.page.wait_for_load_state("networkidle")
        return [
            (
                el.locator(".type").text_content().strip(),
                el.locator(".new").text_content().strip(),
                el.locator(".old").text_content().strip(),
            )
            for el in self.page.locator("tbody > tr").all()
        ]

    def test_edition(self):
        self.addCorpus("wauchier")
        self.token_dropdown_link(5, "Edit")
        self.change_form_value("oulala")
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")

        assert self.select_context_around(5) == [
            "De seint Martin mout oulala",
            "De seint Martin mout oulala on",
            "De seint Martin mout oulala on doucement",
            "seint Martin mout oulala on doucement et",
            "Martin mout oulala on doucement et volentiers",
            "mout oulala on doucement et volentiers le",
            "oulala on doucement et volentiers le bien",
            "on doucement et volentiers le bien oïr",
        ]
        self.page.screenshot(path="HERE.png")
        assert self.get_history() == [("Edition", "oulala", "doit")]

        self.token_dropdown_link(8, "Edit")
        self.change_form_value("Oulipo")
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")

        assert self.select_context_around(8) == [
            "seint Martin mout oulala on doucement Oulipo",
            "Martin mout oulala on doucement Oulipo volentiers",
            "mout oulala on doucement Oulipo volentiers le",
            "oulala on doucement Oulipo volentiers le bien",
            "on doucement Oulipo volentiers le bien oïr",
            "doucement Oulipo volentiers le bien oïr et",
            "Oulipo volentiers le bien oïr et entendre",
            "volentiers le bien oïr et entendre ,",
        ]
        assert self.get_history() == [
            ("Edition", "oulala", "doit"),
            ("Edition", "Oulipo", "et"),
        ]

    def test_addition(self):
        self.addCorpus("wauchier")
        self.token_dropdown_link(5, "Add")
        self.change_form_value("oulala")
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")

        assert self.select_context_around(6) == [
            "De seint Martin mout doit oulala",
            "De seint Martin mout doit oulala on",
            "seint Martin mout doit oulala on doucement",
            "mout doit oulala on doucement et volentiers",
            "doit oulala on doucement et volentiers le",
            "oulala on doucement et volentiers le bien",
            "on doucement et volentiers le bien oïr",
            "doucement et volentiers le bien oïr et",
        ]
        assert self.get_history() == [("Addition", "oulala", "")]

        self.token_dropdown_link(8, "Add")
        self.change_form_value("Oulipo")
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")

        assert self.select_context_around(8) == [
            "seint Martin mout doit oulala on doucement",
            "mout doit oulala on doucement Oulipo et",
            "doit oulala on doucement Oulipo et volentiers",
            "on doucement Oulipo et volentiers le bien",
            "doucement Oulipo et volentiers le bien oïr",
            "Oulipo et volentiers le bien oïr et",
            "et volentiers le bien oïr et entendre",
            "volentiers le bien oïr et entendre ,",
        ]
        assert self.get_history() == [
            ("Addition", "oulala", ""),
            ("Addition", "Oulipo", ""),
        ]

    def test_edit_delete(self):
        self.addCorpus("wauchier")
        self.page.goto(self.url_for("main.tokens_correct", corpus_id="1"))
        original_set = self.select_context_around(5)

        self.token_dropdown_link(5, "Add")
        self.change_form_value("oulala")
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")

        assert self.select_context_around(6) == [
            "De seint Martin mout doit oulala",
            "De seint Martin mout doit oulala on",
            "seint Martin mout doit oulala on doucement",
            "mout doit oulala on doucement et volentiers",
            "doit oulala on doucement et volentiers le",
            "oulala on doucement et volentiers le bien",
            "on doucement et volentiers le bien oïr",
            "doucement et volentiers le bien oïr et",
        ]
        assert self.get_history() == [("Addition", "oulala", "")]

        self.token_dropdown_link(6, "Delete")
        self.change_form_value("oulala")
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")
        assert self.select_context_around(5) == original_set
        assert self.get_history() == [
            ("Addition", "oulala", ""),
            ("Deletion", "", "oulala"),
        ]
