"""Tests for dashboard / favorites (AUTO_LOG_IN=True)."""
import pytest

from flask import url_for

from tests.db_fixtures import DB_CORPORA
from tests.test_playwright.base import Helpers


class TestDashboard(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

    def get_fav_link(self, corpus_id):
        with self.app.test_request_context():
            href = url_for("main.corpus_fav", corpus_id=corpus_id)
        return self.page.locator(f"a[href='{href}']")

    def test_get_index(self):
        self.page.goto(self.url_for("main.index"))
        assert self.get_corpus_names_in_list_browser(admin=False) == ["Floovant", "Wauchier"]

    def test_index_pagination(self):
        self.add_n_corpora(200)
        # Get the first page
        self.page.goto(self.url_for("main.index"))
        first_page = self.get_corpus_names_in_list_browser(admin=False)

        # Go to next page
        self.page.locator(".pagination .page-item:not(.disabled) .next-link").click()
        self.page.wait_for_load_state("networkidle")
        second_page = self.get_corpus_names_in_list_browser(admin=False)
        assert first_page != second_page, "Pagination should lead to different sequences"

    def test_mark_favorite(self):
        self.page.goto(self.url_for("main.index"))
        link = self.get_fav_link(1)
        assert link.locator(".fa-star-o").count() == 1, "Should show an empty star"
        link.click()
        self.page.wait_for_load_state("networkidle")
        link = self.get_fav_link(1)
        assert link.locator(".fa-star-o").count() == 0
        assert link.locator(".fa.fa-star").count() == 1, "Should show a filled star"

    def test_favourite_in_menu(self):
        self.page.goto(self.url_for("main.index"))
        self.get_fav_link(1).click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#toggle_corpus_corpora").click()
        favorites = self.page.locator(".dd-corpus").all()
        assert sorted([f.text_content().strip() for f in favorites]) == ["Wauchier"]
