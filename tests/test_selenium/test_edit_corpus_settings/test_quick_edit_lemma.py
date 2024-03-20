from tests.test_selenium.base import TestBase
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import WebDriverWait


class TestCorpusSettingsUpdate(TestBase):
    def add_cls(self):
        self.addControlLists("wauchier", with_allowed_lemma=True, partial_allowed_lemma=False)
        self.addControlLists("floovant", with_allowed_lemma=True, partial_allowed_lemma=False)

    def go_to(self, corpus="1"):
        self.driver_find_element_by_id("toggle_controllists").click()
        self.driver_find_element_by_id("dropdown_link_cl_"+corpus).click()
        self.element_find_element_by_link_text(
            self.driver_find_element_by_id("left-menu"),
            "Lemma"
        ).click()

    def search(self, control_list_id="1", token="", limit=1000):
        self.driver.get(
            self.url_for_with_port(
                'control_lists_bp.lemma_list',
                control_list_id=control_list_id,
            )+"?limit="+str(limit)
        )
        keyword = self.driver_find_element_by_css_selector("input[name='kw']")
        keyword.click()
        keyword.clear()
        keyword.send_keys(token)
        keyword.send_keys(Keys.RETURN)

        result = []

        # load each page to get the (partials) result tables
        # pagination = self.driver_find_element_by_class_name("pagination").find_elements_by_tag_name("a")

        pagination = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_class_name("pagination"),
            "a"
        )
        for page_index in range(0, len(pagination)):
            # self.driver_find_element_by_class_name("pagination").find_elements_by_tag_name("a")[page_index].click()
            self.element_find_elements_by_tag_name(
                self.driver_find_element_by_class_name("pagination"),
                "a"
            )[page_index].click()
            # find the result in the result table
            res_table = self.driver_find_element_by_id("lemma-list")
            try:
                rows = self.element_find_elements_by_tag_name(res_table, "li")

                for row in rows:
                    result.append(row.text.strip())
            except NoSuchElementException as e:
                print(e)

        return result

    def test_search(self):
        """ ControlLists : Search Allowed Lemmas """
        self.add_cls()
        self.assertEqual(
            ['bien', 'de', 'devoir', 'doucement', 'en1', 'entendre', 'et', 'le', 'retenir', 'volentiers'],
            sorted(self.search("1", "*e*", limit=1)),
            "Search wildcard should work"
        )

        self.assertEqual(
            ['bien', 'de', 'devoir', 'doucement', 'en1', 'entendre', 'et', 'le', 'retenir', 'volentiers'],
            sorted(self.search("1", "*e*", limit=2)),
            "Check that pagination has no effect on results"
        )

    def add_allowed(self, *lemma, success=1):
        # Show the form
        self.driver_find_element_by_id("show_lemma").click()
        # Write the data
        textarea = self.driver_find_element_by_id("submit_lemma_textarea")
        self.writeMultiline(textarea, "\n".join(lemma))
        # Submit
        self.driver_find_element_by_id("submit_lemma").click()
        # Waiting for the result
        if success == 1:
            self.wait_until_shown("lemma_saved")
        else:
            self.wait_until_shown("lemma_error")

        for badge in self.driver_find_elements_by_css_selector(".lemma_badge"):
            if badge.is_displayed():
                return badge.is_displayed(), badge.text.strip()

    def test_add_values(self):
        """ ControlLists : Quick Add Lemmas """
        self.add_cls()
        self.driver.refresh()
        self.go_to("1")
        displayed, message = self.add_allowed("hello", "hello")
        self.assertEqual("Saved", message, "Data should have been saved")
        self.assertEqual(
            ["hello"], self.search("1", "hello"),
            "There should be only one saved value"
        )

        self.go_to("2")
        displayed, message = self.add_allowed("hello1", "hello2", "hello2", "hello3")
        self.assertEqual("Saved", message, "Data should have been saved")
        self.assertEqual(
            ["hello1", "hello2", "hello3"], self.search("2", "hello*"),
            "Each non duplicated value should have been saved"
        )

    def test_delete(self):
        """ ControlLists : Remove Lemmas """
        self.add_cls()
        self.driver.refresh()
        self.go_to("1")
        # Add specifics
        displayed, message = self.add_allowed("hello")
        self.assertEqual("Saved", message, "Data should have been saved")

        # Go to the remove page
        self.search("1", "hello")

        # Remove the item
        self.driver_find_element_by_class_name("rm-lem").click()
        # Wait for the Lemma LIST to have no more LI
        (WebDriverWait(self.driver, 5)).until(staleness_of(self.driver_find_element_by_css_selector("#lemma-list li")))
        # There should be no results anymore
        self.assertEqual(
            [], self.search("1", "hello"),
            "There should be no more valuesfor `hello`"
        )

    # ToDo: Check that write rights apply here
