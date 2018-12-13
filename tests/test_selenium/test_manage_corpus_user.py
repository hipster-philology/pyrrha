from tests.test_selenium.base import TestBase


class TestManageCorpusUser(TestBase):

    def go_to_corpus_management(self, corpus_name):
        self.driver.find_element_by_link_text("Dashboard").click()
        corpora_dashboard = self.driver.find_element_by_id("corpora-dashboard")
        corpora_dashboard.find_element_by_link_text(corpus_name).click()

    def get_ownership_table(self):
        accesses_table = self.driver.find_element_by_id("accesses-table")
        return accesses_table.find_elements_by_name("ownership")

    def get_trash_table(self):
        accesses_table = self.driver.find_element_by_id("accesses-table")
        return accesses_table.find_elements_by_class_name("fa-trash-o")

    def toggle_ownership(self, user_index):
        el = self.get_ownership_table()
        el[user_index].click()

    def submit(self):
        self.driver.find_element_by_id("accesses-form-submit").click()

    def grant_access_to_user(self, corpus_name, user_id):
        # grant access
        users_table = self.driver.find_element_by_id("users-table")
        for row in users_table.find_elements_by_tag_name("tr"):
            print(row.get_attribute("id"))
        user_row = users_table.find_element_by_id("access-u-"+str(user_id))
        user_row.click()
        # toggle ownership to the last added user
        el = self.get_ownership_table()
        self.toggle_ownership(len(el)-1)

        # submit form
        self.submit()
        self.driver.implicitly_wait(3)
        # come back to the management page
        self.go_to_corpus_management(corpus_name)

    def revoke_access_to_user(self, corpus_name, user_index):
        # revoke access
        el = self.get_trash_table()
        el[user_index].click()
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
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        self.go_to_corpus_management("Wauchier")

        # grant access to admin
        self.grant_access_to_user("Wauchier", 0)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

        # grant access to foo
        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, False)
        self.driver.refresh()
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

        # test you can't add duplicates
        self.grant_access_to_user("Wauchier", 0)
        self.grant_access_to_user("Wauchier", 1)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

    def test_revoke_access(self):
        self.addCorpus("wauchier")
        self.addCorpus("floovant")

        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, is_owner=True)
        self.go_to_corpus_management("Wauchier")
        self.grant_access_to_user("Wauchier", 0)

        el = self.get_ownership_table()
        self.assertTrue(len(el) == 2)

        # revoke access to admin
        self.revoke_access_to_user("Wauchier", 0)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

        # revoke access to foo
        self.grant_access_to_user("Wauchier", 0)
        self.revoke_access_to_user("Wauchier", 1)
        el = self.get_ownership_table()
        self.assertTrue(len(el) == 1)

    def test_corpus_has_at_least_one_owner(self):
        self.addCorpus("wauchier", is_owner=False)
        self.addCorpus("floovant", is_owner=False)
        print(self.AUTO_LOG_IN)
        foo_email = self.add_user("foo", "bar")
        cu = self.addCorpusUser("Wauchier", foo_email, is_owner=False)
        print(cu.is_owner)

        self.go_to_corpus_management("Wauchier")
        self.driver.get_screenshot_as_file("here0.png")
        self.grant_access_to_user("Wauchier", 1)

        self.driver.refresh()
        el = self.get_ownership_table()
        self.driver.get_screenshot_as_file("here1.png")
        self.assertEqual(len(el), 2, "There should be two accessors : Admin and Foo")
        self.assertEqual(len([e for e in el if e.get_property("checked")]), 2, "Both should be admin")

        # cannot save all ownership removing
        self.toggle_ownership(0)
        self.toggle_ownership(1)
        self.submit()
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.driver.save_screenshot("here2.png")
        self.assertEqual(
            len([e for e in el if e.get_property("checked")]),
            2,
            "Cannot save all ownership removing"
        )

        # can save partial ownership removing
        self.toggle_ownership(0)
        self.submit()
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertTrue(len([e for e in el if e.get_property("checked")]) == 1)

        # cannot save ownership removing (last owner remaining)
        self.toggle_ownership(1)
        self.submit()
        self.go_to_corpus_management("Wauchier")
        el = self.get_ownership_table()
        self.assertTrue(len([e for e in el if e.get_property("checked")]) == 1)

    def test_corpus_creator_is_owner(self):
        self.addCorpus("wauchier")
        self.driver.find_element_by_link_text("New Corpus").click()
        self.driver.find_element_by_id("corpusName").send_keys("FreshNewCorpus")
        self.writeMultiline(
            self.driver.find_element_by_id("tokens"),
            """tokens	lemmas	pos
De	de	PRE
seint	saint	ADJqua
Martin	martin	NOMpro
mout	mout	ADVgen
doit	devoir	VERcjg"""
        )
        self.driver.find_element_by_id("submit").click()
        self.driver.implicitly_wait(3)
        self.go_to_corpus_management("FreshNewCorpus")

        el = self.get_ownership_table()
        self.assertTrue(len([e for e in el if e.get_property("checked")]) == 1)
