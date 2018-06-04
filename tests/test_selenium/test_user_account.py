import unittest

from app.models import User, Corpus
from app.models.linguistic import CorpusUser
from tests.test_selenium.base import TestBase


class TestUserAccount(TestBase):

    def test_user_info(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.driver.find_element_by_link_text('Your Account').click()
        table = self.driver.find_element_by_tag_name("table")
        # parse the info table
        info = {}
        last_key = None
        for i, v in enumerate(table.find_elements_by_tag_name("td")):
            if i % 2 == 0:
                info[v.text] = ""
                last_key = v.text
            else:
                info[last_key] = v.text

        self.assertEqual(info["Full name"], "foo bar")
        self.assertEqual(info["Email address"], "foo.bar@ppa.fr")
        self.assertEqual(info["Account type"], "User")

    def test_registration(self):
        self.logout()
        self.driver.find_element_by_link_text('Register').click()
        self.driver.find_element_by_id("first_name").send_keys("john")
        self.driver.find_element_by_id("last_name").send_keys("doe")
        self.driver.find_element_by_id("email").send_keys("john.doe@ppa.fr")
        self.driver.find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'] + "testcase01!")
        self.driver.find_element_by_id("password2").send_keys(self.app.config['ADMIN_PASSWORD'] + "testcase01!")
        self.driver.find_element_by_id("submit").click()

        self.driver.implicitly_wait(5)

        user = User.query.filter(
            User.first_name == "john",
            User.last_name == "doe",
            User.email == "john.doe@ppa.fr",
            User.confirmed.is_(False)
        ).first()
        self.assertTrue(user is not None)

    def test_reset_password(self):
        self.logout()
        self.driver.find_element_by_link_text('Log In').click()
        self.driver.find_element_by_link_text('Forgot password?').click()
        self.driver.find_element_by_id("email").send_keys(self.app.config['ADMIN_EMAIL'])
        self.driver.find_element_by_id("submit").click()
        warning = self.driver.find_element_by_class_name("alert-warning").text
        self.assertTrue(warning == "A password reset link has been sent to %s." % self.app.config['ADMIN_EMAIL'])

    def test_change_email(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.driver.find_element_by_link_text('Your Account').click()
        self.driver.find_element_by_link_text('Change email address').click()
        self.driver.find_element_by_id("email").send_keys("bar.foo@ppa.fr")
        self.driver.find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver.find_element_by_id("submit").click()
        warning = self.driver.find_element_by_class_name("alert-warning").text
        self.assertTrue(warning == "A confirmation link has been sent to %s." % "bar.foo@ppa.fr")

    def test_change_password(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.driver.find_element_by_link_text('Your Account').click()
        self.driver.find_element_by_link_text('Change password').click()
        self.driver.find_element_by_id("old_password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver.find_element_by_id("new_password").send_keys(self.app.config['ADMIN_PASSWORD'] + "new")
        self.driver.find_element_by_id("new_password2").send_keys(self.app.config['ADMIN_PASSWORD'] + "new")
        self.driver.find_element_by_id("submit").click()
        self.logout()
        self.login(foo_email, self.app.config['ADMIN_PASSWORD'] + "new")
        success = self.driver.find_element_by_class_name("alert-success").text
        self.assertTrue(success == "You are now logged in. Welcome back!")

    def test_delete_user(self):
        self.addCorpus("wauchier")
        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, is_owner=True)
        # test that the used is correctly deleted
        self.assertTrue(User.query.filter(User.email == foo_email).first() is not None)

        # test that corpora are not deleted when the user is deleted
        self.admin_login()
        self.driver.find_element_by_link_text('Dashboard').click()
        self.driver.find_element_by_id('admin-dashboard').find_element_by_partial_link_text("Registered Users").click()
        self.driver.find_elements_by_class_name("role")[1].click()
        self.driver.find_element_by_link_text('Delete user').click()
        self.driver.find_element_by_class_name('hidden').click()
        self.driver.find_element_by_class_name("deletion").click()
        self.assertTrue(User.query.filter(User.email == foo_email).first() is None)

        corpus = Corpus.query.filter(Corpus.name == "Wauchier").first()
        self.assertTrue(corpus is not None)
        self.assertTrue(CorpusUser.query.filter(CorpusUser.corpus_id == corpus.id).first() is None)

    def test_invalid_login(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email + "2")
        danger = self.driver.find_element_by_class_name("alert-danger").text
        self.assertTrue(danger == "Invalid email address.")

    def test_invalid_password(self):
        self.logout()
        foo_email = self.add_user("foo", "bar")
        self.login(foo_email, "wrong_password")
        danger = self.driver.find_element_by_class_name("alert-danger").find_element_by_class_name("list").text
        self.assertTrue(danger == "Invalid email or password.")

    def test_invite_new_user(self):
        self.admin_login()
        self.driver.find_element_by_link_text('Dashboard').click()
        self.driver.find_element_by_id('admin-dashboard').find_element_by_partial_link_text("Invite New User").click()
        self.driver.find_element_by_id("first_name").send_keys("foo")
        self.driver.find_element_by_id("last_name").send_keys("bar")
        self.driver.find_element_by_id("email").send_keys("foo.bar@ppa.fr")
        self.driver.find_element_by_id("submit").click()

        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "foo.bar@ppa.fr",
            User.confirmed.is_(False)
        ).first()
        self.assertTrue(user is not None)

    @unittest.skip("NotImplemented")
    def test_join_from_invite(self):
        raise NotImplementedError

    @unittest.skip("NotImplemented")
    def test_confirm_token(self):
        raise NotImplementedError

    def test_unconfirmed(self):
        self.addCorpus("wauchier")
        foo_email = self.add_user("foo", "bar")
        user = User.query.filter(User.first_name == "foo",User.last_name == "bar").first()
        user.confirmed = False
        self.db.session.add(user)
        self.db.session.commit()
        self.login_with_user(foo_email)
        success = self.driver.find_element_by_class_name("alert-success").text
        self.assertTrue(success == "You are now logged in. Welcome back!")
        h3 = self.driver.find_element_by_tag_name("h3").text
        self.assertTrue(h3 == "You need to confirm your account before continuing.")
        # check that you can't nor create corpus nor go to your dashboard while your account is unconfirmed
        self.driver.find_element_by_link_text('New Corpus').click()
        self.driver.find_element_by_link_text('Resend confirmation email')
        self.driver.find_element_by_link_text('Dashboard').click()
        self.driver.find_element_by_link_text('Resend confirmation email')

    def test_admin_add_new_user(self):
        self.admin_login()
        self.driver.find_element_by_link_text('Dashboard').click()
        self.driver.find_element_by_id('admin-dashboard').find_element_by_partial_link_text("Add New User").click()
        self.driver.find_element_by_id("first_name").send_keys("foo")
        self.driver.find_element_by_id("last_name").send_keys("bar")
        self.driver.find_element_by_id("email").send_keys("foo.bar@ppa.fr")
        self.driver.find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver.find_element_by_id("password2").send_keys(self.app.config['ADMIN_PASSWORD'])

        self.driver.find_element_by_id("submit").click()

        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "foo.bar@ppa.fr",
            User.confirmed.is_(False)
        ).first()
        self.assertTrue(user is not None)