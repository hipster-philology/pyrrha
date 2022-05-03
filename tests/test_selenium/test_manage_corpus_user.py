from tests.test_selenium.base import TestBase


class TestManageCorpusUser(TestBase):

    def go_to_corpus_management(self, corpus_name):
        self.driver.get(self.url_for_with_port("main.list_corpora"))
        for tr in self.driver_find_elements_by_css_selector("tbody > tr"):
            if self.element_find_element_by_css_selector(tr, ".name").text.strip() == corpus_name:
                return self.element_find_element_by_css_selector(tr, "a span[aria-label='Manage']").click()
        raise ValueError(f"Corpus not found {corpus_name}")

    def get_ownership_table(self):
        accesses_table = self.driver_find_element_by_id("accesses-table")
        return self.element_find_elements_by_name(accesses_table, "ownership")

    def get_trash_table(self):
        accesses_table = self.driver_find_element_by_id("accesses-table")
        return self.element_find_elements_by_class_name(accesses_table, "fa-trash-o")

    def toggle_ownership(self, user_id):
        el = self.driver_find_element_by_id("accesses-table")
        checkbox = self.element_find_element_by_css_selector(el, "input[type='checkbox'][value='"+str(user_id)+"']")
        checkbox.click()

    def submit(self):
        self.driver_find_element_by_id("accesses-form-submit").click()

    def grant_access_to_user(self, corpus_name, user_id):
        """ Gives ownering access to a specific user

        Returns automatically to the edited corpus management page

        :param corpus_name: Name of the corpus
        :param user_id: Id of the user to select
        """
        # grant access
        users_table = self.driver_find_element_by_id("users-table")
        user_row = self.element_find_element_by_class_name(users_table, "u-"+str(user_id))
        user_row.click()
        # toggle ownership to the last added user
        el = self.get_ownership_table()
        self.toggle_ownership(user_id)

        # submit form
        self.submit()
        self.driver.implicitly_wait(3)
        # come back to the management page
        self.go_to_corpus_management(corpus_name)

    def revoke_access_to_user(self, corpus_name, user_id):
        # revoke access
        accesses_table = self.driver_find_element_by_id("accesses-table")
        el = self.element_find_element_by_css_selector(accesses_table, ".fa-trash-o.u-"+str(user_id))
        el.click()
        self.submit()
        self.driver.implicitly_wait(3)
        # come back to the management page
        self.go_to_corpus_management(corpus_name)

    def test_display_corpus_users(self):
        self.addCorpus("wauchier", no_corpus_user=True)
        self.addCorpus("floovant", no_corpus_user=True)

        # there is no user on this corpus
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 0)

        # add admin as the owner
        self.addCorpusUser("Wauchier", self.app.config['ADMIN_EMAIL'], True)
        self.driver.refresh()
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

        # grant access to foo
        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, False)
        self.driver.refresh()
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

        # let's check it's still ok with user foo
        self.login_with_user(foo_email)
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

    def test_grant_access(self):
        self.addCorpus("wauchier", no_corpus_user=True)
        self.addCorpus("floovant", no_corpus_user=True)

        self.go_to_corpus_management("Wauchier")

        # grant access to admin
        self.grant_access_to_user("Wauchier", 1)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

        # grant access to foo
        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, False)
        self.driver.refresh()
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

        # test you can't add duplicates
        self.grant_access_to_user("Wauchier", 1)
        self.grant_access_to_user("Wauchier", 2)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

    def test_revoke_access(self):
        self.addCorpus("wauchier", no_corpus_user=True)
        self.addCorpus("floovant", no_corpus_user=True)

        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, is_owner=True)
        self.go_to_corpus_management("Wauchier")
        self.grant_access_to_user("Wauchier", 1)

        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

        # revoke access to admin
        self.revoke_access_to_user("Wauchier", 1)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

        # revoke access to foo
        self.grant_access_to_user("Wauchier", 1)
        self.revoke_access_to_user("Wauchier", 2)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

    def test_corpus_has_at_least_one_owner(self):
        self.addCorpus("wauchier", no_corpus_user=True)
        self.addCorpus("floovant", no_corpus_user=True)

        foo_email = self.add_user("foo", "bar")
        cu = self.addCorpusUser("Wauchier", foo_email, is_owner=True)
        self.go_to_corpus_management("Wauchier")
        self.grant_access_to_user("Wauchier", 1)

        self.driver.refresh()
        el = self.get_ownership_table()
        self.assertEqual(len(el), 2, "There should be two accessors : Admin and Foo")
        self.assertEqual(len([e for e in el if e.get_property("checked")]), 2, "Both should be admin")

        # cannot save all ownership removing
        self.toggle_ownership(1)
        self.toggle_ownership(2)
        self.submit()
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertEqual(
            len([e for e in el if e.get_property("checked")]),
            2,
            "Cannot remove ownership from everyone "
        )

        # can save partial ownership removing
        self.toggle_ownership(1)
        self.submit()
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertEqual(
            len([e for e in el if e.get_property("checked")]),
            1,
            "There should be one remaining admin only"
        )

        # cannot save ownership removing (last owner remaining)
        self.toggle_ownership(2)
        self.submit()
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertEqual(
            len([e for e in el if e.get_property("checked")]),
            1,
            "Last admin can't be removed"
        )

    def test_corpus_creator_is_owner(self):
        self.addCorpus("wauchier")
        self.driver_find_element_by_link_text("New Corpus").click()
        self.driver_find_element_by_id("corpusName").send_keys("FreshNewCorpus")
        self.writeMultiline(
            self.driver_find_element_by_id("tokens"),
            """tokens	lemmas	pos
De	de	PRE
seint	saint	ADJqua
Martin	martin	NOMpro
mout	mout	ADVgen
doit	devoir	VERcjg"""
        )
        self.driver_find_element_by_id("label_checkbox_create").click()
        self.driver_find_element_by_id("submit").click()
        self.driver.implicitly_wait(3)
        self.go_to_corpus_management("FreshNewCorpus")

        el = self.get_ownership_table()
        self.assertTrue(len([e for e in el if e.get_property("checked")]) == 1)
