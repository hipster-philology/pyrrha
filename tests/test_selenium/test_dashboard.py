from selenium.common.exceptions import NoSuchElementException

from tests.test_selenium.base import TestBase


class TestDashboard(TestBase):

    def test_admin_dashboard(self):
        """
        Admins should see the admin dashboard
        :return:
        """
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        self.driver.find_element_by_link_text("Dashboard").click()
        # admin dashboard  displayed & corpora dashboard displayed
        self.assertTrue(self.driver.find_element_by_id("admin-dashboard").is_displayed())
        self.assertTrue(self.driver.find_element_by_id("corpora-dashboard").is_displayed())

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

        self.driver.find_element_by_link_text("Dashboard").click()

        # admin dashboard not displayed & corpora dashboard displayed
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element_by_id("admin-dashboard")
        corpora_dashboard = self.driver.find_element_by_id("corpora-dashboard")
        self.assertTrue(corpora_dashboard.is_displayed())

        # Floovant not displayed & Wauchier displayed
        c = corpora_dashboard.find_elements_by_class_name("col")
        self.assertTrue(len(c) == 1)
        self.assertTrue(c[0].text == "Wauchier")

        # Floovant & Wauchier displayed
        self.addCorpusUser("Floovant", foo_email, False)
        self.driver.refresh()
        corpora_dashboard = self.driver.find_element_by_id("corpora-dashboard")

        c = corpora_dashboard.find_elements_by_class_name("col")
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
        self.driver.find_element_by_link_text("Dashboard").click()

        navbars = self.driver.find_element_by_id("main-nav")
        navbars.find_element_by_id("toggle_corpus_corpora").click()
        header_items = navbars.find_elements_by_class_name("dd-corpus")
        header_names = [item.text for item in header_items]

        corpora_dashboard = self.driver.find_element_by_id("corpora-dashboard")
        corpora_items = corpora_dashboard.find_elements_by_class_name("col")
        corpora_names = [item.text for item in corpora_items]

        self.assertListEqual(corpora_names, header_names)

        # add a new corpus and check again
        self.driver.find_element_by_link_text("New Corpus").click()
        self.driver.find_element_by_id("corpusName").send_keys("FreshNewCorpus")
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(3)
        self.driver.find_element_by_link_text("Dashboard").click()

        navbars = self.driver.find_element_by_id("main-nav")
        navbars.find_element_by_id("toggle_corpus_corpora").click()
        header_items = navbars.find_elements_by_class_name("dd-corpus")
        header_names = [item.text for item in header_items]

        corpora_dashboard = self.driver.find_element_by_id("corpora-dashboard")
        corpora_items = corpora_dashboard.find_elements_by_class_name("col")
        corpora_names = [item.text for item in corpora_items]

        self.assertListEqual(corpora_names, header_names)
