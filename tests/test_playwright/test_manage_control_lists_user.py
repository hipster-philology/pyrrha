import pytest

from tests.test_playwright.base import Helpers


class TestManageControlListsUser(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def go_to_control_lists_management(self, control_lists):
        self.page.get_by_role("link", name="Dashboard", exact=True).click()
        controllists_dashboard = self.page.locator("#control_lists-dashboard")
        controllists_dashboard.get_by_role("link", name=control_lists).click()

    def get_ownership_table(self):
        accesses_table = self.page.locator("#accesses-table")
        return accesses_table.locator("[name='ownership']").all()

    def get_trash_table(self):
        accesses_table = self.page.locator("#accesses-table")
        return accesses_table.locator(".fa-trash-o").all()

    def toggle_ownership(self, user_id):
        el = self.page.locator("#accesses-table")
        el.locator(f"input[type='checkbox'][value='{user_id}']").click()

    def submit(self):
        self.page.locator("#accesses-form-submit").click()

    def grant_access_to_user(self, control_list_name, user_id):
        users_table = self.page.locator("#users-table")
        users_table.locator(f".u-{user_id}").click()
        self.toggle_ownership(user_id)
        self.submit()
        self.page.wait_for_load_state("networkidle")
        self.go_to_control_lists_management(control_list_name)

    def revoke_access_to_user(self, control_list_name, user_id):
        accesses_table = self.page.locator("#accesses-table")
        accesses_table.locator(f".fa-trash-o.u-{user_id}").click()
        self.submit()
        self.page.wait_for_load_state("networkidle")
        self.go_to_control_lists_management(control_list_name)

    def test_display_control_lists_users(self):
        self.addControlLists("wauchier", no_corpus_user=True)
        self.addControlLists("floovant", no_corpus_user=True)

        self.go_to_control_lists_management("Wauchier")
        assert len(self.get_ownership_table()) == 0

        self.addControlListsUser("Wauchier", self.app.config["ADMIN_EMAIL"], True)
        self.page.reload()
        assert len(self.get_ownership_table()) == 1

        foo_email = self.add_user("foo", "bar")
        self.addControlListsUser("Wauchier", foo_email, False)
        self.page.reload()
        assert len(self.get_ownership_table()) == 2

        self.login_with_user(foo_email)
        self.go_to_control_lists_management("Wauchier")
        assert len(self.get_ownership_table()) == 2

    def test_grant_access_to_control_list(self):
        self.addControlLists("wauchier", no_corpus_user=True)
        self.addControlLists("floovant", no_corpus_user=True)

        self.go_to_control_lists_management("Wauchier")
        self.grant_access_to_user("Wauchier", 1)
        assert len(self.get_ownership_table()) == 1

        foo_email = self.add_user("foo", "bar")
        self.addControlListsUser("Wauchier", foo_email, False)
        self.page.reload()
        assert len(self.get_ownership_table()) == 2

        self.grant_access_to_user("Wauchier", 1)
        self.grant_access_to_user("Wauchier", 2)
        assert len(self.get_ownership_table()) == 2

    def test_revoke_access(self):
        self.addControlLists("wauchier", no_corpus_user=True)
        self.addControlLists("floovant", no_corpus_user=True)

        foo_email = self.add_user("foo", "bar")
        self.addControlListsUser("Wauchier", foo_email, is_owner=True)
        self.go_to_control_lists_management("Wauchier")
        self.grant_access_to_user("Wauchier", 1)

        assert len(self.get_ownership_table()) == 2

        self.revoke_access_to_user("Wauchier", 1)
        assert len(self.get_ownership_table()) == 1

        self.grant_access_to_user("Wauchier", 1)
        self.revoke_access_to_user("Wauchier", 2)
        assert len(self.get_ownership_table()) == 1

    def test_control_list_has_at_least_one_owner(self):
        self.addControlLists("wauchier", no_corpus_user=True)
        self.addControlLists("floovant", no_corpus_user=True)

        foo_email = self.add_user("foo", "bar")
        self.addControlListsUser("Wauchier", foo_email, is_owner=True)
        self.go_to_control_lists_management("Wauchier")
        self.grant_access_to_user("Wauchier", 1)

        self.page.reload()
        el = self.get_ownership_table()
        assert len(el) == 2, "There should be two accessors: Admin and Foo"
        assert len([e for e in el if e.is_checked()]) == 2, "Both should be owners"

        self.toggle_ownership(1)
        self.toggle_ownership(2)
        self.submit()
        self.go_to_control_lists_management("Wauchier")
        el = self.get_ownership_table()
        assert len([e for e in el if e.is_checked()]) == 2, "Cannot remove ownership from everyone"

        self.toggle_ownership(1)
        self.submit()
        self.go_to_control_lists_management("Wauchier")
        el = self.get_ownership_table()
        assert len([e for e in el if e.is_checked()]) == 1, "One remaining admin only"

        self.toggle_ownership(2)
        self.submit()
        self.go_to_control_lists_management("Wauchier")
        el = self.get_ownership_table()
        assert len([e for e in el if e.is_checked()]) == 1, "Last admin can't be removed"

    def test_corpus_creator_is_owner(self):
        self.addControlLists("wauchier")
        self.page.get_by_role("link", name="New Corpus", exact=True).click()
        self.page.locator("#corpusName").fill("FreshNewCorpus")
        self.page.locator("#tokens").fill(
            "tokens\tlemmas\tpos\n"
            "De\tde\tPRE\n"
            "seint\tsaint\tADJqua\n"
            "Martin\tmartin\tNOMpro\n"
            "mout\tmout\tADVgen\n"
            "doit\tdevoir\tVERcjg"
        )
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        self.go_to_control_lists_management("Control List FreshNewCorpus")

        el = self.get_ownership_table()
        assert len([e for e in el if e.is_checked()]) == 1


class TestNotAdmin(Helpers):
    @pytest.fixture
    def auto_login(self):
        return False

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def go_to_control_lists_management(self, control_lists):
        self.page.get_by_role("link", name="Dashboard", exact=True).click()
        controllists_dashboard = self.page.locator("#control_lists-dashboard")
        controllists_dashboard.get_by_role("link", name=control_lists).click()

    def test_change_filter(self):
        self.addControlLists("wauchier", no_corpus_user=True)
        foo_email = self.add_user("foo", "bar")
        self.addControlListsUser("Wauchier", foo_email, is_owner=True)
        self.login(foo_email, self.app.config["ADMIN_PASSWORD"])
        self.page.reload()
        self.go_to_control_lists_management("Wauchier")

        self.page.get_by_role("link", name="Ignore values").click()
        self.page.locator("[name='punct']").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        assert (
            self.page.locator(".alert.alert-success").text_content().strip()
            == "The filters have been updated."
        )
