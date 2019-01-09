from tests.test_selenium.base import TestBase
from collections import namedtuple

User = namedtuple("User", ["user", "owner"])


class TestUpdateControlList(TestBase):
    AUTO_LOG_IN = False

    def go_to_control_lists_management(self, control_lists):
        self.driver.find_element_by_id("toggle_controllists").click()
        dropdown = self.driver.find_element_by_id("cl-dd")
        dropdown.find_element_by_partial_link_text(control_lists).click()

    def test_action_as_owner(self):
        foor_bar = self.add_user("foo", "bar", False)
        self.addControlLists("wauchier", no_corpus_user=True, for_users=[User(foor_bar, True)])
        self.addControlLists("floovant", no_corpus_user=True)

        self.login_with_user(foor_bar)
        self.go_to_control_lists_management("Wauchier")
        # This should work otherwise there is an issue
        links = self.driver.find_element_by_id("right-column").find_elements_by_tag_name("a")
        self.assertEqual(
            sorted([link.text for link in links]),
            sorted(['Rewrite Lemma List', 'Rewrite POS List', 'Rewrite Morphology List']),
            "Full rewrite are limited to control lists users"
        )
        # Check that we can make public
        links = self.driver.find_element_by_id("left-menu").find_elements_by_tag_name("a")
        self.assertEqual(
            sorted([link.text for link in links]),
            sorted(['Lemma', 'Make public', 'Morphologies', 'POS', 'Wauchier']),
            "Full rewrite are limited to control lists users"
        )
        # Check that we can send mail to admin to ask for publication
        self.driver.find_element_by_link_text("Make public").click()

    def test_action_as_admin(self):
        pass

    def test_action_as_user(self):
        pass

    def test_action_as_not_access(self):
        pass
