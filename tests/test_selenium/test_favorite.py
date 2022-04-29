from selenium.common.exceptions import NoSuchElementException

from tests.test_selenium.base import TestBase
from tests.db_fixtures import DB_CORPORA
from flask import url_for


class TestDashboard(TestBase):
    AUTO_LOG_IN = True

    def setUp(self):
        super(TestDashboard, self).setUp()
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

    def test_get_index(self):
        """ Check that all corpora are displayed on the index"""
        self.driver.get(self.url_for_with_port("main.index"))
        corpora = self.driver_find_elements_by_class_name("corpus-nav-link")
        self.assertEqual(
            sorted([corpus.text for corpus in corpora]),
            ["Floovant", "Wauchier"]
        )

    def test_index_pagination(self):
        """ Test that we can follow a specific pagination """
        self.add_n_corpora(200)
        # Get the index
        self.driver.get(self.url_for_with_port("main.index"))
        first_page = self.driver_find_elements_by_class_name("corpus-nav-link")
        first_page = sorted([corpus.text for corpus in first_page])

        self.driver_find_elements_by_css_selector(".page-item a.page-link")[1].click()
        second_page = self.driver_find_elements_by_class_name("corpus-nav-link")
        second_page = sorted([corpus.text for corpus in second_page])

        self.assertNotEqual(first_page, second_page, "Pagination should lead to different sequences")

    def get_fav_link(self, corpus_id):
        url = url_for("main.corpus_fav", corpus_id=corpus_id)
        return self.driver_find_element_by_css_selector("a[href='{}']".format(url))

    def test_mark_favorite(self):
        """ Check that favorite can be marked"""
        self.driver.get(self.url_for_with_port("main.index"))
        # Check before clicking
        link = self.get_fav_link(1)
        self.assertEqual(
            len(self.element_find_elements_by_css_selector(link, ".fa-star-o")), 1,
            "There should be a link, and it should have an empty star"
        )
        link.click()
        self.driver.implicitly_wait(1)
        # Check after
        link = self.get_fav_link(1)
        self.assertEqual(
            len(self.element_find_elements_by_css_selector(link, ".fa-star-o")), 0,
            "There should be a link, and it should have an empty star"
        )
        self.assertEqual(
            len(self.element_find_elements_by_css_selector(link, ".fa.fa-star")), 1,
            "There should be a link, and it should have a filled star"
        )

    def test_favourite_in_menu(self):
        """ Check that favorite can be marked"""
        self.driver.get(self.url_for_with_port("main.index"))
        # Add a corpus in header as favorite
        link = self.get_fav_link(1)
        link.click()
        self.driver_find_element_by_id("toggle_corpus_corpora").click()
        favorites = self.driver_find_elements_by_css_selector(".dd-corpus")
        self.assertEqual(
            sorted([fav.text for fav in favorites]),
            ["Wauchier"],
            "Favourite should be available in top header"
        )