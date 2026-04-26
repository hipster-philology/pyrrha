"""Tests for control list administration (AUTO_LOG_IN=False)."""
import csv
import os
from collections import namedtuple

import pytest

from tests.db_fixtures.wauchier import WauchierAllowedMorph, WauchierAllowedPOS
from tests.test_playwright.base import Helpers

User = namedtuple("User", ["user", "owner"])


class TestUpdateControlList(Helpers):
    @pytest.fixture
    def auto_login(self):
        return False

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def go_to_control_lists_management(self, control_lists):
        self.page.locator("#toggle_controllists").click()
        dropdown = self.page.locator("#cl-dd")
        dropdown.get_by_role("link", name=control_lists).click()
        self.page.wait_for_load_state("networkidle")

    def test_action_as_owner(self):
        foor_bar = self.add_user("foo", "bar", False)
        self.addControlLists(
            "wauchier",
            partial_allowed_pos=False,
            partial_allowed_morph=False,
            no_corpus_user=True,
            for_users=[User(foor_bar, True)],
        )
        self.addControlLists("floovant", no_corpus_user=True)

        self.login_with_user(foor_bar)
        self.go_to_control_lists_management("Wauchier")

        links = self.page.locator("#right-column").locator("a").all()
        assert sorted([link.text_content().strip() for link in links]) == sorted(
            ["Rewrite Lemma List", "Rewrite POS List", "Rewrite Morphology List"]
        )

        links = self.page.locator("#left-menu").locator("a").all()
        assert sorted([link.text_content().strip() for link in links]) == sorted([
            "Edit informations",
            "Guidelines",
            "Lemma",
            "Make public",
            "Morphologies",
            "POS",
            "Propose changes",
            "Wauchier",
            "Rename",
            "Ignore values",
        ])

        self.page.get_by_role("link", name="Make public", exact=False).click()
        self.page.locator("#mail-title").fill("Hello")
        self.page.locator("#mail-message").fill("My\nName\nis\nBond")
        self.page.locator("#mail-submit").click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-success").text_content().strip()
            == "The email has been sent to the administrators."
        )

        self.page.get_by_role("link", name="Make public", exact=False).click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-warning").text_content().strip()
            == "This list is already public or submitted."
        )

        self.page.goto(self.url_for("control_lists_bp.go_public", control_list_id=1))
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-danger").text_content().strip()
            == "You do not have the rights for this action."
        )

        self.page.goto(self.url_for("control_lists_bp.edit", cl_id=1, allowed_type="patate"))
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator("#error_message").text_content().strip() == "Page not found"

        self.page.goto(
            self.url_for("control_lists_bp.read_allowed_values", control_list_id=1, allowed_type="patate")
        )
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-danger").text_content().strip()
            == "The category you selected is wrong petit coquin !"
        )

        self.page.goto(
            self.url_for("control_lists_bp.read_allowed_values", control_list_id=1, allowed_type="POS")
        )
        self.page.wait_for_load_state("networkidle")
        found = [el.text_content().strip() for el in self.page.locator(".allowed .label").all()]
        assert sorted(found) == sorted([x.label for x in WauchierAllowedPOS])

        self.page.goto(
            self.url_for("control_lists_bp.read_allowed_values", control_list_id=1, allowed_type="morph")
        )
        self.page.wait_for_load_state("networkidle")
        found = [el.text_content().strip() for el in self.page.locator(".allowed .label").all()]
        assert sorted(found) == sorted([x.label for x in WauchierAllowedMorph])
        found_readable = [el.text_content().strip() for el in self.page.locator(".allowed .readable").all()]
        assert sorted(found_readable) == sorted([x.readable for x in WauchierAllowedMorph])

        self.page.goto(self.url_for("control_lists_bp.information_edit", control_list_id=1))
        self.page.locator("#cl_notes").fill("# This is some notes")
        self.page.locator("#submit").click()
        self.page.goto(self.url_for("control_lists_bp.information_read", control_list_id=1))
        assert self.page.locator("h1").text_content() == "This is some notes"

    def test_action_as_admin_but_not_owner(self):
        self.addControlLists(
            "wauchier",
            no_corpus_user=True,
            for_users=[User(self.app.config["ADMIN_EMAIL"], False)],
        )
        self.addControlLists("floovant", no_corpus_user=True)

        self.admin_login()
        self.go_to_control_lists_management("Wauchier")

        links = self.page.locator("#right-column").locator("a").all()
        assert sorted([link.text_content().strip() for link in links]) == sorted(
            ["Make public", "Rewrite Lemma List", "Rewrite POS List", "Rewrite Morphology List"]
        )

        links = self.page.locator("#left-menu").locator("a").all()
        assert sorted([link.text_content().strip() for link in links]) == sorted([
            "Guidelines",
            "Edit informations",
            "Lemma",
            "Morphologies",
            "POS",
            "Propose changes",
            "Rename",
            "Wauchier",
            "Ignore values",
        ])

        self.page.get_by_role("link", name="Propose changes", exact=False).click()
        self.page.locator("#mail-title").fill("Hello")
        self.page.locator("#mail-message").fill("My\nName\nis\nBond")
        self.page.locator("#mail-submit").click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-success").text_content().strip()
            == "The email has been sent to the control list administrators."
        )

        self.go_to_control_lists_management("Wauchier")
        self.page.get_by_role("link", name="Make public", exact=False).click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator(".alert.alert-success").text_content().strip() == "This list is now public."
        assert self.page.locator("a").filter(has_text="Make public").count() == 0

        self.page.goto(self.url_for("control_lists_bp.go_public", control_list_id=1))
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-warning").text_content().strip() == "This list is already public."
        )

        self.page.goto(self.url_for("control_lists_bp.rename", control_list_id=1))
        self.page.locator("#rename-title").fill("WOOHOOO")
        self.page.locator("#rename-submit").click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-success").text_content().strip()
            == "The name of the list has been updated."
        )
        assert self.page.locator("h1").text_content().strip() == "WOOHOOO"

        self.page.goto(self.url_for("control_lists_bp.information_edit", control_list_id=1))
        self.page.locator("#cl_notes").fill("# This is some notes")
        self.page.locator("#submit").click()
        self.page.goto(self.url_for("control_lists_bp.information_read", control_list_id=1))
        assert self.page.locator("h1").text_content() == "This is some notes"

    def test_action_as_user(self):
        foor_bar = self.add_user("foo", "bar", False)
        self.addControlLists(
            "wauchier",
            no_corpus_user=True,
            for_users=[User(foor_bar, False)],
        )
        self.addControlLists("floovant", no_corpus_user=True)

        self.login_with_user(foor_bar)
        self.go_to_control_lists_management("Wauchier")

        links = self.page.locator("#right-column").locator("a").all()
        assert [link.text_content().strip() for link in links] == []

        links = self.page.locator("#left-menu").locator("a").all()
        assert sorted([link.text_content().strip() for link in links]) == sorted(
            ["Lemma", "Guidelines", "Morphologies", "POS", "Propose changes", "Wauchier"]
        )

        self.page.get_by_role("link", name="Propose changes", exact=False).click()
        self.page.locator("#mail-title").fill("Hello")
        self.page.locator("#mail-message").fill("My\nName\nis\nBond")
        self.page.locator("#mail-submit").click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-success").text_content().strip()
            == "The email has been sent to the control list administrators."
        )

        self.page.goto(self.url_for("control_lists_bp.propose_as_public", control_list_id=1))
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-danger").text_content().strip()
            == "You are not an owner of the list."
        )

        self.page.goto(self.url_for("control_lists_bp.go_public", control_list_id=1))
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-danger").text_content().strip()
            == "You do not have the rights for this action."
        )

        self.page.goto(self.url_for("control_lists_bp.edit", cl_id=1, allowed_type="lemma"))
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert.alert-danger").text_content().strip()
            == "You are not an owner of the list."
        )

    def test_edit_upload_file(self, tmp_path):
        self.addControlLists(
            "wauchier",
            no_corpus_user=True,
            for_users=[User(self.app.config["ADMIN_EMAIL"], False)],
        )
        self.admin_login()
        self.go_to_control_lists_management("Wauchier")
        self.page.locator(".settings-lemma").click()
        self.page.wait_for_load_state("networkidle")

        temp_file = self.create_temp_example_file(tmp_path)
        self.page.locator("#upload").set_input_files(str(temp_file))
        self.page.wait_for_load_state("networkidle")

        allowed_values = self.page.locator("#allowed_values").input_value()
        with open(temp_file) as fp:
            file_rows = [row for row in csv.reader(fp, delimiter="\t")]
        textarea_rows = [row for row in csv.reader(allowed_values.split("\n"), delimiter="\t") if row]
        assert sorted(textarea_rows) == sorted(file_rows)
