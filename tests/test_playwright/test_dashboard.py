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
        self.page.get_by_role("link", name="Dashboard", exact=True).click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator("#admin-dashboard").is_visible()
        assert self.page.locator("#corpora-dashboard").is_visible()

    def test_user_dashboard(self):
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.addCorpusUser("Wauchier", foo_email, True)

        self.page.get_by_role("link", name="Dashboard", exact=False).click()
        self.page.wait_for_load_state("networkidle")

        assert self.page.locator("#admin-dashboard").count() == 0
        corpora_dashboard = self.page.locator("#corpora-dashboard")
        assert corpora_dashboard.is_visible()

        cols = corpora_dashboard.locator(".col").all()
        assert len(cols) == 1
        assert cols[0].text_content().strip() == "Wauchier"

        self.addCorpusUser("Floovant", foo_email, False)
        self.page.reload()
        corpora_dashboard = self.page.locator("#corpora-dashboard")
        cols = corpora_dashboard.locator(".col").all()
        assert len(cols) == 2
        assert cols[0].text_content().strip() == "Wauchier"
        assert cols[1].text_content().strip() == "Floovant"

    def test_corpora_displayed_same_as_header_items(self):
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        inserted_corpora = sorted([
            DB_CORPORA["wauchier"]["corpus"].name,
            DB_CORPORA["floovant"]["corpus"].name,
        ])

        self.add_favorite(
            user_id=self.get_admin_id(),
            corpora_ids=(
                DB_CORPORA["wauchier"]["corpus"].id,
                DB_CORPORA["floovant"]["corpus"].id,
            ),
        )
        self.admin_login()
        self.page.get_by_role("link", name="Dashboard", exact=False).click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="See all as administrator", exact=False).click()
        self.page.wait_for_load_state("networkidle")

        corpora_dashboard = self.page.locator("table.sortable tbody")
        corpora_names = sorted(
            [el.text_content().strip() for el in corpora_dashboard.locator(".name").all()]
        )
        assert corpora_names == inserted_corpora

        self.page.get_by_role("link", name="New Corpus", exact=False).click()
        self.page.locator("#corpusName").fill("FreshNewCorpus")
        self.write_lorem_ipsum_tokens()
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        self.add_favorite(user_id=self.get_admin_id(), corpora_ids=(3,), reset=False)
        self.page.locator("#main-nav").get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")

        navbars = self.page.locator("#main-nav")
        navbars.locator("#toggle_corpus_corpora").click()
        header_names = sorted(
            [el.text_content().strip() for el in navbars.locator(".dd-corpus").all()]
        )
        self.page.get_by_role("link", name="See all as administrator", exact=False).click()
        self.page.wait_for_load_state("networkidle")
        corpora_dashboard = self.page.locator("table.sortable tbody")
        full_corpora_names = sorted(
            [el.text_content().strip() for el in corpora_dashboard.locator(".name").all()]
        )

        assert header_names == ['Floovant', 'FreshNewCorpus', 'Wauchier'], \
            "Nav quick-links show only favorites"
        assert full_corpora_names == sorted(["FreshNewCorpus"] + inserted_corpora)
