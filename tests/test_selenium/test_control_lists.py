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
        self.driver.find_element_by_id("mail-title").send_keys("Hello")
        self.writeMultiline(self.driver.find_element_by_id("mail-message"), "My\nName\nis\nBond")
        self.driver.find_element_by_id("mail-submit").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver.find_element_by_css_selector(".alert.alert-success").text.strip(),
            'The email has been sent to the administrators.',
            "The list should be updated"
        )
        # Check that we can't do that twice
        self.driver.find_element_by_link_text("Make public").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver.find_element_by_css_selector(".alert.alert-warning").text.strip(),
            'This list is already public or submitted.',
            "The same list cannot be made public twice"
        )

    def test_action_as_admin_but_not_owner(self):
        self.addControlLists("wauchier", no_corpus_user=True, for_users=[User(self.app.config['ADMIN_EMAIL'], False)])
        self.addControlLists("floovant", no_corpus_user=True)

        self.admin_login()
        self.go_to_control_lists_management("Wauchier")
        # This should work otherwise there is an issue
        links = self.driver.find_element_by_id("right-column").find_elements_by_tag_name("a")
        self.assertEqual(
            sorted([link.text.strip() for link in links]),
            sorted(['Make public', 'Rewrite Lemma List', 'Rewrite POS List', 'Rewrite Morphology List']),
            "Full rewrite are limited to control lists users and admin. Admin can make list public"
        )

        # Check that we can make public
        links = self.driver.find_element_by_id("left-menu").find_elements_by_tag_name("a")
        self.assertEqual(
            sorted([link.text.strip() for link in links]),
            sorted(['Lemma', 'Morphologies', 'POS', 'Propose changes', 'Wauchier']),
            "Full rewrite are limited to control lists users"
        )

        # Check that we can send mail to admin to ask for publication
        self.driver.find_element_by_link_text("Propose changes").click()
        self.driver.find_element_by_id("mail-title").send_keys("Hello")
        self.writeMultiline(self.driver.find_element_by_id("mail-message"), "My\nName\nis\nBond")
        self.driver.find_element_by_id("mail-submit").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver.find_element_by_css_selector(".alert.alert-success").text.strip(),
            'The email has been sent to the control list administrators.',
            "The list should be updated"
        )
        # Check that admins can make a list public (and it can be done only once)
        self.go_to_control_lists_management("Wauchier")
        self.driver.find_element_by_link_text("Make public").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver.find_element_by_css_selector(".alert.alert-success").text.strip(),
            'This list is now public.',
            "The list can be made public by admins"
        )
        self.assertEqual(
            self.driver.find_elements_by_link_text("Make public"),
            [],
            "There should be no link anymore."
        )

    def test_action_as_user(self):
        pass

    def test_action_without_access(self):
        pass
