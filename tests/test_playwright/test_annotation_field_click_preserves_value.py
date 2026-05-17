"""Regression test: clicking an annotation field must not empty it.

Issue #346 – when a user clicked an already-filled autocomplete cell (lemma,
POS, morph) the visible input value was cleared, making single-character edits
impossible.  The root cause was onInputFocus() initialising query to '' instead
of the current modelValue.
"""
import pytest

from app.models import WordToken
from tests.test_playwright.base import TokenCorrectHelpers


class TestAnnotationFieldClickPreservesValue(TokenCorrectHelpers):

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def _go_to_corpus(self):
        self.page.goto(self.url_for("main.tokens_correct", corpus_id=self.CORPUS_ID))
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".at-loading").wait_for(state="hidden", timeout=10000)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _lemma_input(self, token_order_id):
        row = self.page.locator(f"[data-token-order='{token_order_id}']")
        return row.locator("[data-field='lemma'] .anno-field-input")

    def _pos_input(self, token_order_id):
        row = self.page.locator(f"[data-token-order='{token_order_id}']")
        return row.locator("[data-field='POS'] .anno-field-input")

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_clicking_filled_lemma_preserves_value(self):
        """Clicking a lemma cell whose value is already set must not clear it."""
        self.addCorpus(with_token=True, tokens_up_to=4)
        self._go_to_corpus()

        # Token order 1 is "De" with lemma "de" (from the wauchier fixture)
        inp = self._lemma_input(1)

        # Before clicking, the closed input should show the saved lemma
        before = inp.input_value()
        assert before == "de", f"Expected 'de' before click, got {before!r}"

        # Click opens the autocomplete dropdown
        inp.click()

        # After clicking, the input value must still reflect the saved lemma,
        # not be empty.  Before the fix, this would return ''.
        after = inp.input_value()
        assert after == "de", (
            f"Clicking the input emptied the field: got {after!r} instead of 'de'. "
            "This is the regression described in issue #346."
        )

    def test_clicking_filled_pos_preserves_value(self):
        """Same check for the POS autocomplete field."""
        self.addCorpus(with_token=True, tokens_up_to=4)
        self._go_to_corpus()

        # Token order 1 has POS "PRE"
        inp = self._pos_input(1)

        before = inp.input_value()
        assert before == "PRE", f"Expected 'PRE' before click, got {before!r}"

        inp.click()

        after = inp.input_value()
        assert after == "PRE", (
            f"Clicking the POS field emptied it: got {after!r} instead of 'PRE'."
        )

    def test_single_char_edit_after_click(self):
        """After clicking a filled cell the user should be able to edit a single
        character without the existing value being wiped first."""
        self.addCorpus(with_token=True, tokens_up_to=4)
        self._go_to_corpus()

        # Token order 1: form="De", lemma="de"  →  we want to change it to "des"
        inp = self._lemma_input(1)
        inp.click()

        # Append a single character to the end of the current value
        inp.press("End")
        inp.type("s")

        # The visible value must now be "des"
        assert inp.input_value() == "des", (
            f"Expected 'des' after appending 's', got {inp.input_value()!r}"
        )

        # Save and verify persistence
        row = self.page.locator("[data-token-order='1']")
        row.locator("button.save-btn").click()
        self.page.wait_for_load_state("networkidle")
        row.locator(".save-status").wait_for(state="visible", timeout=10000)

        from app import db
        token = (
            db.session.query(WordToken)
            .filter_by(corpus=int(self.CORPUS_ID), order_id=1)
            .first()
        )
        db.session.refresh(token)
        assert token.lemma == "des", (
            f"Expected saved lemma 'des', got {token.lemma!r}"
        )
