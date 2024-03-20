from selenium.common.exceptions import NoSuchElementException

from tests.test_selenium.base import TestBase
from tests.db_fixtures import DB_CORPORA


class TestDashboard(TestBase):
    AUTO_LOG_IN = False

    def test_admin_dashboard(self):
        """
        Admins should see the admin dashboard
        :return:
        """
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        self.admin_login()
        self.driver_find_element_by_link_text("Dashboard").click()
        # admin dashboard  displayed & corpora dashboard displayed
        self.assertTrue(self.driver_find_element_by_id("admin-dashboard").is_displayed())
        self.assertTrue(self.driver_find_element_by_id("corpora-dashboard").is_displayed())

    def test_user_dashboard(self):
        """
        Test that the right corpora are displayed
        :return:
        """
        self.addCorpus("wauchier")
        self.addCorpus("floovant")
        self.addCorpusUser("Wauchier", self.app.config['ADMIN_EMAIL'], True)

        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.addCorpusUser("Wauchier", foo_email, True)

        self.driver_find_element_by_link_text("Dashboard").click()

        # admin dashboard not displayed & corpora dashboard displayed
        with self.assertRaises(NoSuchElementException):
            self.driver_find_element_by_id("admin-dashboard")
        corpora_dashboard = self.driver_find_element_by_id("corpora-dashboard")
        self.assertTrue(corpora_dashboard.is_displayed())

        # Floovant not displayed & Wauchier displayed
        c = self.element_find_elements_by_class_name(corpora_dashboard, "col")
        self.assertTrue(len(c) == 1)
        self.assertTrue(c[0].text == "Wauchier")

        # Floovant & Wauchier displayed
        self.addCorpusUser("Floovant", foo_email, False)
        self.driver.refresh()
        corpora_dashboard = self.driver_find_element_by_id("corpora-dashboard")

        c = self.element_find_elements_by_class_name(corpora_dashboard, "col")
        self.assertTrue(len(c) == 2)
        self.assertTrue(c[0].text == "Wauchier")
        self.assertTrue(c[1].text == "Floovant")

    def test_corpora_displayed_same_as_header_items(self):
        """
        Test that the displayed corpora match the ones in the head navbar
        :return:
        """
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        inserted_corpora = sorted([
            DB_CORPORA["wauchier"]["corpus"].name,
            DB_CORPORA["floovant"]["corpus"].name
        ])

        self.add_favorite(user_id=self.get_admin_id(), corpora_ids=(
            DB_CORPORA["wauchier"]["corpus"].id,
            DB_CORPORA["floovant"]["corpus"].id
        ))
        self.admin_login()
        self.driver_find_element_by_link_text("Dashboard").click()
        self.driver_find_element_by_link_text("See all as administrator").click()

        corpora_dashboard = self.driver_find_element_by_css_selector("table.sortable tbody")
        corpora_items = self.element_find_elements_by_class_name(corpora_dashboard, "name")
        corpora_names = sorted([item.text for item in corpora_items])

        self.assertEqual(
            inserted_corpora, corpora_names,
            "Admin has access on dashboard to all corpora"
        )

        # add a new corpus and check again
        self.driver_find_element_by_link_text("New Corpus").click()
        self.driver_find_element_by_id("corpusName").send_keys("FreshNewCorpus")
        self.write_lorem_impsum_tokens()
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.driver_find_element_by_id("submit").click()
        self.driver.implicitly_wait(3)

        self.add_favorite(user_id=self.get_admin_id(), corpora_ids=(3, ))
        self.driver_find_element_by_link_text("Dashboard").click()

        navbars = self.driver_find_element_by_id("main-nav")
        self.element_find_element_by_id(navbars, "toggle_corpus_corpora").click()
        header_items = self.element_find_elements_by_class_name(navbars, "dd-corpus")
        header_names = sorted([item.text for item in header_items])

        corpora_dashboard = self.driver_find_element_by_id("corpora-dashboard")
        corpora_items = self.element_find_elements_by_class_name(corpora_dashboard, "col")
        corpora_names = sorted([item.text for item in corpora_items])

        self.driver_find_element_by_link_text("See all as administrator").click()

        corpora_dashboard = self.driver_find_element_by_css_selector("table.sortable tbody")
        corpora_items = self.element_find_elements_by_class_name(corpora_dashboard, "name")
        full_corpora_names = sorted([item.text for item in corpora_items])

        self.assertEqual(header_names, corpora_names,
                            "Quick-link corpora are the same even for admins")
        self.assertEqual(
            header_names, ["FreshNewCorpus"],
            "FreshNewCorpus is owned by admin so it's shown in header"
        )
        self.assertEqual(
            corpora_names,
            ["FreshNewCorpus"],
            "Admin's main dashboard contains their corpora"
        )
        self.assertEqual(
            full_corpora_names,
            sorted(["FreshNewCorpus"] + inserted_corpora),
            "Admin's corpora dashboard contains all corpora"
        )
