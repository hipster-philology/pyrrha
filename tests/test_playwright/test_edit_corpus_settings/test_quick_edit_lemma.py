"""Tests for the ControlLists quick-edit lemma view (search + add + delete)."""
import pytest

from tests.test_playwright.base import Helpers


class TestCorpusSettingsUpdate(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def add_cls(self):
        self.addControlLists("wauchier", with_allowed_lemma=True, partial_allowed_lemma=False)
        self.addControlLists("floovant", with_allowed_lemma=True, partial_allowed_lemma=False)

    def go_to(self, corpus="1"):
        self.page.locator("#toggle_controllists").click()
        self.page.locator(f"#dropdown_link_cl_{corpus}").click()
        self.page.locator("#left-menu").get_by_role("link", name="Lemma").click()
        self.page.wait_for_load_state("networkidle")

    def search(self, control_list_id="1", token="", limit=1000):
        self.page.goto(
            self.url_for("control_lists_bp.lemma_list", control_list_id=control_list_id)
            + f"?limit={limit}"
        )
        kw = self.page.locator("input[name='kw']")
        kw.click()
        kw.fill(token)
        kw.press("Enter")
        self.page.wait_for_load_state("networkidle")

        result = []
        pagination_links = self.page.locator(".pagination a").all()
        for idx in range(len(pagination_links)):
            self.page.locator(".pagination a").nth(idx).click()
            self.page.wait_for_load_state("networkidle")
            for li in self.page.locator("#lemma-list li").all():
                text = li.text_content().strip()
                if text:
                    result.append(text)
        return result

    def add_allowed(self, *lemma, success=True):
        self.page.locator("#show_lemma").click()
        self.page.locator("#submit_lemma_textarea").fill("\n".join(lemma))
        self.page.locator("#submit_lemma").click()
        target_id = "lemma_saved" if success else "lemma_error"
        self.page.locator(f"#{target_id}").wait_for(state="visible", timeout=10000)
        for badge in self.page.locator(".lemma_badge").all():
            if badge.is_visible():
                return badge.is_visible(), badge.text_content().strip()

    def test_search(self):
        self.add_cls()
        assert sorted(self.search("1", "*e*", limit=1)) == [
            "bien", "de", "devoir", "doucement", "en1", "entendre", "et", "le", "retenir", "volentiers"
        ]
        assert sorted(self.search("1", "*e*", limit=2)) == [
            "bien", "de", "devoir", "doucement", "en1", "entendre", "et", "le", "retenir", "volentiers"
        ]

    def test_add_values(self):
        self.add_cls()
        self.page.reload()
        self.go_to("1")
        displayed, message = self.add_allowed("hello", "hello")
        assert message == "Saved"
        assert self.search("1", "hello") == ["hello"]

        self.go_to("2")
        displayed, message = self.add_allowed("hello1", "hello2", "hello2", "hello3")
        assert message == "Saved"
        assert self.search("2", "hello*") == ["hello1", "hello2", "hello3"]

    def test_delete(self):
        self.add_cls()
        self.page.reload()
        self.go_to("1")
        displayed, message = self.add_allowed("hello")
        assert message == "Saved"

        self.search("1", "hello")
        self.page.locator(".rm-lem").click()
        self.page.locator("#lemma-list li").wait_for(state="detached", timeout=5000)

        assert self.search("1", "hello") == []
