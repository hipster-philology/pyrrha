import pytest

from app.models import Bookmark
from app import db
from tests.test_playwright.base import Helpers


class TestBookmark(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def set_bookmark(self, tok_id, page=None):
        self.page.goto(self.url_for("main.tokens_correct", corpus_id="1", page=page))
        self.page.locator(f"#token_{tok_id}_row .at-dd-toggle").click()
        dd = self.page.locator(f"#token_{tok_id}_row .at-dd-menu:visible")
        dd.get_by_role("link", name="Bookmark").click()
        self.page.wait_for_load_state("networkidle")

    def test_create_bookmark(self):
        self.addCorpus("wauchier")
        self.set_bookmark(110, 2)

        bookmark = Bookmark.query.filter(
            db.and_(
                Bookmark.corpus_id == 1,
                Bookmark.user_id == 1,
                Bookmark.token_id == 110,
                Bookmark.page == 2,
            )
        ).first()
        assert bookmark is not None

    def test_edit_bookmark(self):
        self.addCorpus("wauchier")
        self.set_bookmark(110, 2)
        self.set_bookmark(220, 3)
        assert self.page.url == self.url_for("main.tokens_correct", corpus_id="1", page=3) + "#token_220_row"

        bookmarks = Bookmark.query.filter(
            db.and_(Bookmark.corpus_id == 1, Bookmark.user_id == 1)
        ).all()
        assert bookmarks is not None
        assert len(bookmarks) == 1
        assert bookmarks[0].token_id == 220
        assert bookmarks[0].page == 3

    def test_go_to_bookmark(self):
        self.addCorpus("wauchier")
        self.page.goto(self.url_for("main.tokens_correct", corpus_id="1"))
        self.page.locator("#bookmark_link").click()
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.tokens_correct", corpus_id="1") in self.page.url

        self.set_bookmark(220, 3)
        self.page.goto(self.url_for("main.tokens_correct", corpus_id="1"))
        self.page.locator("#bookmark_link").click()
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.tokens_correct", corpus_id="1", page=3) in self.page.url
        assert self.page.url.endswith("#token_220_row")
