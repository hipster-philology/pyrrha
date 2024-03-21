from tests.test_selenium.base import TestBase
from tests.db_fixtures.wauchier import WauchierTokens
from app.models import Bookmark, WordToken


class TestBookmark(TestBase):
    """ Check that saving a bookmark and going to it works
    """

    def set_bookmark(self, tok_id, page=None):
        self.driver.get(self.url_for_with_port("main.tokens_correct", corpus_id="1", page=page))
        self.driver.save_screenshot("token.png")
        self.driver_find_element_by_id("dd_t"+str(tok_id)).click()
        self.driver.implicitly_wait(2)
        dd = self.driver_find_element_by_css_selector("*[aria-labelledby='dd_t{}']".format(tok_id))
        self.element_find_element_by_partial_link_text(dd, "Set as bookmark").click()
        self.driver.implicitly_wait(2)

    def test_create_bookmark(self):
        """ [Bookmark] Check that we are able to create a bookmark """
        self.addCorpus("wauchier")
        # First edition
        self.set_bookmark(110, 2)

        with self.app.app_context():
            self.assertIsNotNone(
                Bookmark.query.filter(
                    self.db.and_(
                        Bookmark.corpus_id == 1,
                        Bookmark.user_id == 1,
                        Bookmark.token_id == 110,
                        Bookmark.page == 2
                    )
                ).first()
            )

    def test_edit_bookmark(self):
        """ [Bookmark] Check that we are able to create a bookmark then recreate one"""
        self.addCorpus("wauchier")
        # Create the bokomark
        self.set_bookmark(110, 2)
        # Update it
        self.set_bookmark(220, 3)
        self.assertEqual(
            self.driver.current_url,
            self.url_for_with_port("main.tokens_correct", corpus_id="1", page=3)+"#token_220_row",
            "No bookmark should go to first page"
        )

        with self.app.app_context():
            bookmark = Bookmark.query.filter(
                    self.db.and_(
                        Bookmark.corpus_id == 1,
                        Bookmark.user_id == 1
                    )
                ).all()
            self.assertIsNotNone(bookmark)
            self.assertEqual(len(bookmark), 1)
            self.assertEqual(bookmark[0].token_id, 220)
            self.assertEqual(bookmark[0].page, 3)

    def test_go_to_bookmark(self):
        """ [Bookmark] Check that we are able to go to a bookmarked token """
        self.addCorpus("wauchier")
        # Check first cases where there is nothing
        self.driver.get(self.url_for_with_port("main.tokens_correct", corpus_id="1"))
        self.driver_find_element_by_id("bookmark_link").click()
        self.driver.implicitly_wait(1)
        self.assertEqual(
            self.driver.current_url, self.url_for_with_port("main.tokens_correct", corpus_id="1"),
            "No bookmark should go to first page"
        )
        # Set the bookmark
        self.set_bookmark(220, 3)
        # Reset page
        self.driver.get(self.url_for_with_port("main.tokens_correct", corpus_id="1"))
        self.driver_find_element_by_id("bookmark_link").click()
        self.driver.implicitly_wait(1)
        self.assertEqual(
            self.driver.current_url,
            self.url_for_with_port("main.tokens_correct", corpus_id="1", page=3)+"#token_220_row",
            "No bookmark should go to first page"
        )
