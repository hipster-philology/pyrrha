"""Playwright tests for the 'mark for review' feature."""
import pytest

from app.models import WordToken
from tests.test_playwright.base import TokenCorrectHelpers


class TestTokenReview(TokenCorrectHelpers):

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def _go_to_corpus(self):
        self.page.goto(self.url_for("main.tokens_correct", corpus_id=self.CORPUS_ID))
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".at-loading").wait_for(state="hidden", timeout=10000)

    def _open_review_panel(self, token_order_id):
        """Open the review flag panel for a token row via the ⋯ dropdown."""
        row = self.page.locator(f"[data-token-order='{token_order_id}']")
        row.locator(".at-dd-toggle").click()
        menu = row.locator(".at-dd-menu:visible")
        menu.get_by_role("link", name="Mark for review").click()

    def test_mark_for_review_with_comment(self):
        """Flagging a token shows the badge and persists needs_review + comment in DB."""
        self.addCorpus(with_token=True, tokens_up_to=24)
        self._go_to_corpus()

        token_order_id = 2
        self._open_review_panel(token_order_id)

        row = self.page.locator(f"[data-token-order='{token_order_id}']")

        # Review panel should be visible
        panel = row.locator(".at-review-panel")
        panel.wait_for(state="visible", timeout=5000)

        # Fill in a comment
        panel.locator("textarea").fill("Needs double-checking")

        # Submit the flag
        panel.locator("button", has_text="Flag for review").click()

        # Panel should close after save
        panel.wait_for(state="hidden", timeout=5000)

        # Toggle button in ID column should now be active
        toggle = row.locator(".at-review-toggle")
        toggle.wait_for(state="visible", timeout=5000)
        assert "at-review-toggle--active" in toggle.get_attribute("class")

        # Row should have the review CSS class
        assert "at-row--needs-review" in row.get_attribute("class")

        # DB should reflect the change
        from app import db
        token = (
            db.session.query(WordToken)
            .filter_by(corpus=int(self.CORPUS_ID), order_id=token_order_id)
            .first()
        )
        db.session.refresh(token)
        assert token.needs_review is True
        assert token.review_comment == "Needs double-checking"

    def test_remove_review_flag(self):
        """Removing the review flag clears the badge and updates the DB."""
        self.addCorpus(with_token=True, tokens_up_to=24)
        self._go_to_corpus()

        token_order_id = 2

        # First: mark for review
        self._open_review_panel(token_order_id)
        row = self.page.locator(f"[data-token-order='{token_order_id}']")
        panel = row.locator(".at-review-panel")
        panel.wait_for(state="visible", timeout=5000)
        panel.locator("textarea").fill("check me")
        panel.locator("button", has_text="Flag for review").click()
        panel.wait_for(state="hidden", timeout=5000)

        # Toggle should be active now
        toggle = row.locator(".at-review-toggle")
        assert "at-review-toggle--active" in toggle.get_attribute("class")

        # Now remove it via the dropdown
        row.locator(".at-dd-toggle").click()
        menu = row.locator(".at-dd-menu:visible")
        menu.get_by_role("link", name="Remove review flag").click()
        self.page.wait_for_load_state("networkidle")

        # Toggle should return to inactive state
        from playwright.sync_api import expect
        expect(toggle).not_to_have_class("at-review-toggle--active", timeout=5000)

        expect(row).not_to_have_class("at-row--needs-review", timeout=5000)

        from app import db
        token = (
            db.session.query(WordToken)
            .filter_by(corpus=int(self.CORPUS_ID), order_id=token_order_id)
            .first()
        )
        db.session.refresh(token)
        assert token.needs_review is False
        assert token.review_comment is None

    def test_toggle_button_tooltip_shows_comment(self):
        """The ⚑ toggle button title attribute should display the review comment."""
        self.addCorpus(with_token=True, tokens_up_to=24)
        self._go_to_corpus()

        token_order_id = 3
        self._open_review_panel(token_order_id)
        row = self.page.locator(f"[data-token-order='{token_order_id}']")
        panel = row.locator(".at-review-panel")
        panel.wait_for(state="visible", timeout=5000)
        panel.locator("textarea").fill("uncertain POS")
        panel.locator("button", has_text="Flag for review").click()
        panel.wait_for(state="hidden", timeout=5000)

        toggle = row.locator(".at-review-toggle")
        assert toggle.get_attribute("title") == "uncertain POS"

    def test_needs_review_page_shows_flagged_token(self):
        """The /tokens/needs-review page lists only tokens flagged for review."""
        self.addCorpus(with_token=True, tokens_up_to=24)
        self._go_to_corpus()

        # Flag token at order_id=2
        self._open_review_panel(2)
        row = self.page.locator("[data-token-order='2']")
        panel = row.locator(".at-review-panel")
        panel.wait_for(state="visible", timeout=5000)
        panel.locator("button", has_text="Flag for review").click()
        panel.wait_for(state="hidden", timeout=5000)

        # Go to the needs-review filtered page
        self.page.goto(self.url_for("main.tokens_needs_review", corpus_id=self.CORPUS_ID))
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".at-loading").wait_for(state="hidden", timeout=10000)

        rows = self.page.locator(".at-row").all()
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"

        # The flagged row should have an active toggle button
        assert rows[0].locator(".at-review-toggle.at-review-toggle--active").count() == 1

    def test_click_toggle_opens_review_panel(self):
        """Clicking the ⚑ toggle button in the ID column opens the review panel."""
        self.addCorpus(with_token=True, tokens_up_to=24)
        self._go_to_corpus()

        token_order_id = 2
        row = self.page.locator(f"[data-token-order='{token_order_id}']")
        panel = row.locator(".at-review-panel")

        # Click the toggle directly — panel should open (no need to flag first)
        row.locator(".at-review-toggle").click()
        panel.wait_for(state="visible", timeout=5000)


class TestOrderIdLinksToCorpus(TokenCorrectHelpers):
    """On the For Review and Unallowed pages, the order id links to the token in the correction page"""

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def _assert_link(self, url):
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".at-loading").wait_for(state="hidden", timeout=10000)
        link = self.page.locator(".at-order-id").first
        link.wait_for(state="visible", timeout=5000)
        order_id = int(link.get_attribute("id").replace("tok", ""))
        href = link.get_attribute("href")
        base = self.url_for("main.tokens_correct", corpus_id=self.CORPUS_ID, _external=False)
        page_number = -(-order_id // self.app.config["PAGINATION_DEFAULT_TOKENS"])
        assert href.endswith(f"/corpus/{self.CORPUS_ID}/tokens/correct?page={page_number}#tok{order_id}"), href
        assert "/tokens/correct" in base

    def test_needs_review_link(self):
        from app import db
        self.addCorpus(with_token=True, tokens_up_to=24)
        token = db.session.query(WordToken).filter_by(corpus=int(self.CORPUS_ID), order_id=3).first()
        token.needs_review = True
        db.session.commit()
        self._assert_link(self.url_for("main.tokens_needs_review", corpus_id=self.CORPUS_ID))

    def test_unallowed_link(self):
        self.addCorpus(with_token=True, tokens_up_to=24, partial_allowed_lemma=True)
        self._assert_link(self.url_for(
            "main.tokens_correct_unallowed", corpus_id=self.CORPUS_ID, allowed_type="lemma"))
