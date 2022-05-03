from tests.test_selenium.base import TestBase
from collections import namedtuple
import csv
import os
from tests.db_fixtures.wauchier import WauchierAllowedPOS, WauchierAllowedMorph


User = namedtuple("User", ["user", "owner"])


class TestUpdateControlList(TestBase):
    AUTO_LOG_IN = False

    def go_to_control_lists_management(self, control_lists):
        self.driver_find_element_by_id("toggle_controllists").click()
        dropdown = self.driver_find_element_by_id("cl-dd")
        self.element_find_element_by_partial_link_text(dropdown, control_lists).click()

    def test_action_as_owner(self):
        """ [ControlLists Administration] CL Admin can propose changes and propose to make a list public """
        foor_bar = self.add_user("foo", "bar", False)
        self.addControlLists("wauchier", partial_allowed_pos=False, partial_allowed_morph=False,
                             no_corpus_user=True, for_users=[User(foor_bar, True)])
        self.addControlLists("floovant", no_corpus_user=True)

        self.login_with_user(foor_bar)
        self.go_to_control_lists_management("Wauchier")
        # This should work otherwise there is an issue
        # links = self.driver_find_element_by_id("right-column").find_elements_by_tag_name("a")
        links = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_id("right-column"),
            "a"
        )
        self.assertEqual(
            sorted([link.text for link in links]),
            sorted(['Rewrite Lemma List', 'Rewrite POS List', 'Rewrite Morphology List']),
            "Full rewrite are limited to control lists users"
        )

        # Check that we can make public
        # links = self.driver_find_element_by_id("left-menu").find_elements_by_tag_name("a")
        links = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_id("left-menu"),
            "a"
        )
        self.assertEqual(
            sorted([link.text for link in links]),
            sorted([
                "Edit informations",
                "Guidelines",
                'Lemma',
                'Make public',
                'Morphologies',
                'POS',
                'Propose changes',
                'Wauchier',
                'Rename'
            ]),
            "Full rewrite are limited to control lists users"
        )

        # Check that we can send mail to admin to ask for publication
        self.driver_find_element_by_link_text("Make public").click()
        self.driver_find_element_by_id("mail-title").send_keys("Hello")
        self.writeMultiline(self.driver_find_element_by_id("mail-message"), "My\nName\nis\nBond")
        self.driver_find_element_by_id("mail-submit").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-success").text.strip(),
            'The email has been sent to the administrators.',
            "The list should be updated"
        )
        # Check that we can't do that twice
        self.driver_find_element_by_link_text("Make public").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-warning").text.strip(),
            'This list is already public or submitted.',
            "The same list cannot be made public twice"
        )

        # Check that we cannot make the liost public
        self.driver.get(self.url_for_with_port("control_lists_bp.go_public", control_list_id=1))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-danger").text.strip(),
            'You do not have the rights for this action.',
            "CL Admin cannot make a list public"
        )

        # Check that we cannot access edit pages of unknown type
        self.driver.get(self.url_for_with_port("control_lists_bp.edit", cl_id=1, allowed_type="patate"))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_id("error_message").text.strip(),
            "Page not found",
            "403 is generated when accessing something forbidden"
        )

        # Check that we cannot access edit pages of unknown type
        self.driver.get(self.url_for_with_port("control_lists_bp.read_allowed_values",
                                               control_list_id=1, allowed_type="patate"))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-danger").text.strip(),
            "The category you selected is wrong petit coquin !",
            "User is redirected on none existing category"
        )

        # Check that we can read values
        self.driver.get(self.url_for_with_port("control_lists_bp.read_allowed_values",
                                               control_list_id=1, allowed_type="POS"))
        self.driver.implicitly_wait(5)
        found = [
            el.text.strip()
            for el in self.driver_find_elements_by_css_selector(".allowed .label")
        ]
        self.assertEqual(
            sorted(found),
            sorted([x.label for x in WauchierAllowedPOS]),
            "We should be able to read the POS"
        )

        # Check that we can read values
        self.driver.get(self.url_for_with_port("control_lists_bp.read_allowed_values",
                                               control_list_id=1, allowed_type="morph"))
        self.driver.implicitly_wait(5)
        found = [
            el.text.strip()
            for el in self.driver_find_elements_by_css_selector(".allowed .label")
        ]
        self.assertEqual(
            sorted(found),
            sorted([x.label for x in WauchierAllowedMorph]),
            "We should be able to read the POS"
        )
        found = [
            el.text.strip()
            for el in self.driver_find_elements_by_css_selector(".allowed .readable")
        ]
        self.assertEqual(
            sorted(found),
            sorted([x.readable for x in WauchierAllowedMorph]),
            "We should be able to read the POS"
        )

        # Check that we can edit informations about markdown or whatever
        self.driver.get(self.url_for_with_port("control_lists_bp.information_edit", control_list_id=1))
        self.driver_find_element_by_id("cl_notes").send_keys("# This is some notes")
        self.driver.save_screenshot("HELLOOOO1.png")
        self.driver_find_element_by_id("submit").click()
        self.driver.get(self.url_for_with_port("control_lists_bp.information_read", control_list_id=1))
        self.driver.save_screenshot("HELLOOOO2.png")
        self.assertEqual(
            self.driver_find_element_by_tag_name("h1").text, "This is some notes",
            "Check that edition works"
        )

    def test_action_as_admin_but_not_owner(self):
        """ [ControlLists Administration] App Admin can propose changes and turn a list public """
        self.addControlLists("wauchier", no_corpus_user=True, for_users=[User(self.app.config['ADMIN_EMAIL'], False)])
        self.addControlLists("floovant", no_corpus_user=True)

        self.admin_login()
        self.go_to_control_lists_management("Wauchier")
        # This should work otherwise there is an issue
        # links = self.driver_find_element_by_id("right-column").find_elements_by_tag_name("a")
        links = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_id("right-column"),
            "a"
        )
        self.assertEqual(
            sorted([link.text.strip() for link in links]),
            sorted(['Make public', 'Rewrite Lemma List', 'Rewrite POS List',
                    'Rewrite Morphology List']),
            "Full rewrite are limited to control lists users and admin. Admin can make list public"
        )

        # Check that we can make public
        #links = self.driver_find_element_by_id("left-menu").find_elements_by_tag_name("a")
        links = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_id("left-menu"),
            "a"
        )
        self.assertEqual(
            sorted([link.text.strip() for link in links]),
            sorted(["Guidelines",
                    "Edit informations", 'Lemma', 'Morphologies', 'POS', 'Propose changes', 'Rename', 'Wauchier']),
            "Full rewrite are limited to control lists users"
        )

        # Check that we can send mail to admin to ask for publication
        self.driver_find_element_by_link_text("Propose changes").click()
        self.driver_find_element_by_id("mail-title").send_keys("Hello")
        self.writeMultiline(self.driver_find_element_by_id("mail-message"), "My\nName\nis\nBond")
        self.driver_find_element_by_id("mail-submit").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-success").text.strip(),
            'The email has been sent to the control list administrators.',
            "The list should be updated"
        )
        # Check that admins can make a list public (and it can be done only once)
        self.go_to_control_lists_management("Wauchier")
        self.driver_find_element_by_link_text("Make public").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-success").text.strip(),
            'This list is now public.',
            "The list can be made public by admins"
        )
        self.assertEqual(
            self.driver_find_elements_by_link_text("Make public"),
            [],
            "There should be no link anymore."
        )

        # Check that we cannot make the list public
        self.driver.get(self.url_for_with_port("control_lists_bp.go_public", control_list_id=1))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-warning").text.strip(),
            'This list is already public.',
            "Admin cannot make a list public twice"
        )

        # Check that we cannot make the list public
        self.driver.get(self.url_for_with_port("control_lists_bp.rename", control_list_id=1))
        self.driver_find_element_by_id("rename-title").send_keys("WOOHOOO")
        self.driver_find_element_by_id("rename-submit").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-success").text.strip(),
            'The name of the list has been updated.'
        )
        self.assertEqual(
            self.driver_find_element_by_css_selector("h1").text.strip(),
            'WOOHOOO'
        )

        # Check that we can edit informations about markdown or whatever
        self.driver.get(self.url_for_with_port("control_lists_bp.information_edit", control_list_id=1))
        self.driver_find_element_by_id("cl_notes").send_keys("# This is some notes")
        self.driver_find_element_by_id("submit").click()
        self.driver.get(self.url_for_with_port("control_lists_bp.information_read", control_list_id=1))
        self.assertEqual(
            self.driver_find_element_by_tag_name("h1").text, "This is some notes",
            "Check that edition works"
        )


    def test_action_as_user(self):
        """ [ControlLists Administration] Normal users can only propose changes"""
        foor_bar = self.add_user("foo", "bar", False)
        self.addControlLists("wauchier", no_corpus_user=True, for_users=[User(foor_bar, False)])
        self.addControlLists("floovant", no_corpus_user=True)

        self.login_with_user(foor_bar)
        self.go_to_control_lists_management("Wauchier")
        # This should work otherwise there is an issue
        #links = self.driver_find_element_by_id("right-column").find_elements_by_tag_name("a")
        links = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_id("right-column"),
            "a"
        )
        self.assertEqual(
            [link.text.strip() for link in links], [],
            "Users have no specific abilities on the dashboard"
        )

        # Check that we can make public
        links = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_id("left-menu"),
            "a"
        )
        self.assertEqual(
            sorted([link.text.strip() for link in links]),
            sorted(['Lemma', "Guidelines",
                    'Morphologies', 'POS', 'Propose changes', 'Wauchier']),
            "Only contacting and reading is possible to users"
        )

        # Check that we can send mail to admin to ask for publication
        self.driver_find_element_by_link_text("Propose changes").click()
        self.driver_find_element_by_id("mail-title").send_keys("Hello")
        self.writeMultiline(self.driver_find_element_by_id("mail-message"), "My\nName\nis\nBond")
        self.driver_find_element_by_id("mail-submit").click()
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-success").text.strip(),
            'The email has been sent to the control list administrators.',
            "The list should be updated"
        )

        # Check that we cannot access the propose as public page
        self.driver.get(self.url_for_with_port("control_lists_bp.propose_as_public", control_list_id=1))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-danger").text.strip(),
            'You are not an owner of the list.',
            "User cannot access list administration"
        )

        # Check that we cannot make the list public
        self.driver.get(self.url_for_with_port("control_lists_bp.go_public", control_list_id=1))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-danger").text.strip(),
            'You do not have the rights for this action.',
            "User cannot make a list public"
        )

        # Check that we cannot access edit pages
        self.driver.get(self.url_for_with_port("control_lists_bp.edit", cl_id=1, allowed_type="lemma"))
        self.driver.implicitly_wait(5)
        self.assertEqual(
            self.driver_find_element_by_css_selector(".alert.alert-danger").text.strip(),
            'You are not an owner of the list.',
            "User cannot edit control list they don't own"
        )

    def test_edit_upload_file(self):
        """Test that an user can upload a file to fill in 'allowed_values' textarea."""
        self.addControlLists(
            "wauchier",
            no_corpus_user=True,
            for_users=[User(self.app.config['ADMIN_EMAIL'], False)]
        )
        self.admin_login()
        self.go_to_control_lists_management("Wauchier")
        self.driver_find_element_by_class_name("settings-lemma").click()
        self.driver.implicitly_wait(15)
        upload = self.driver_find_element_by_id("upload")
        temp_file = self.create_temp_example_file()
        upload.send_keys(temp_file.name)
        self.driver.implicitly_wait(15)
        allowed_values = self.driver_find_element_by_id("allowed_values")
        with open(temp_file.name) as fp:
            self.assertCountEqual(
                [row for row in csv.reader(allowed_values.get_attribute("value").split("\n"), delimiter="\t") if row],
                [row for row in csv.reader(open(fp.name), delimiter="\t")]
            )
        os.remove(temp_file.name)
