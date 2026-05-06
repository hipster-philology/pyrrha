"""Tests for admin/user dashboard (AUTO_LOG_IN=False)."""
import pytest

from tests.db_fixtures import DB_CORPORA
from tests.test_playwright.base import Helpers


class TestDashboard(Helpers):
    @pytest.fixture
    def auto_login(self):
        return False

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_admin_dashboard(self):
        self.addCorpus("wauchier")
        self.addCorpus("floovant")
        self.admin_login()
        self.page.get_by_role("link", name="Admin", exact=False).first.click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.get_by_role("link", name="All Corpora", exact=False).is_visible()
        assert self.page.get_by_role("link", name="All Control Lists", exact=False).is_visible()

    def test_user_dashboard(self):
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.addCorpusUser("Wauchier", foo_email, True)

        self.page.get_by_role("link", name="My corpora", exact=False).click()
        self.page.wait_for_load_state("networkidle")

        corpora_dashboard = self.page.locator("#list-browser-corpora")
        assert corpora_dashboard.is_visible()

        cols = self.get_corpus_names_in_list_browser(admin=False)
        assert len(cols) == 1
        assert cols[0] == "Wauchier"

        self.addCorpusUser("Floovant", foo_email, False)
        self.page.reload()
        self.page.wait_for_load_state("networkidle")

        cols = self.get_corpus_names_in_list_browser(admin=False)
        assert len(cols) == 2
        assert cols == ["Floovant", "Wauchier"]

    def test_corpora_displayed_same_as_header_items(self):
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        inserted_corpora = sorted([
            DB_CORPORA["wauchier"]["corpus"].name,
            DB_CORPORA["floovant"]["corpus"].name,
        ])

        self.add_favorite_via_db(
            user_id=self.get_admin_id(),
            corpora_ids=(
                DB_CORPORA["wauchier"]["corpus"].id,
                DB_CORPORA["floovant"]["corpus"].id,
            ),
        )
        self.admin_login()
        self.go_to_admin_corpus_page()
        self.page.wait_for_load_state("networkidle")
        corpora_names = self.get_corpus_names_in_list_browser(admin=True)
        assert corpora_names == inserted_corpora

        # Create a corpus
        self.page.get_by_role("link", name="New Corpus", exact=False).click()
        self.page.locator("#corpusName").fill("FreshNewCorpus")
        self.write_lorem_ipsum_tokens()
        self.page.locator("#label_checkbox_create").click()
        with self.page.expect_navigation(timeout=30000):
            self.page.locator("#submit").click()

        # Check that that are added to favorite are visible
        self.add_favorite_via_db(user_id=self.get_admin_id(), corpora_ids=(3,), reset=False)
        self.page.get_by_role("link", name="Pyrrha", exact=False)
        navbars = self.page.locator("#main-nav")
        navbars.locator("#toggle_corpus_corpora").click()
        header_names = sorted(
            [el.text_content().strip() for el in navbars.locator(".dd-corpus").all()]
        )

        #Check it registered on admin
        self.go_to_admin_corpus_page()
        full_corpora_names = self.get_corpus_names_in_list_browser(admin=True)
        assert header_names == ['Floovant', 'FreshNewCorpus', 'Wauchier'], \
            "Nav quick-links show only favorites"
        assert full_corpora_names == sorted(["FreshNewCorpus"] + inserted_corpora)
