from flask import url_for

from app.models import User, Corpus
from app.models import CorpusUser
from tests.test_selenium.base import TestBase


class TestUserAccount(TestBase):
    AUTO_LOG_IN = False

    def test_user_info(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.driver_find_element_by_link_text('Your Account').click()
        table = self.driver_find_element_by_tag_name("table")
        # parse the info table
        info = {}
        last_key = None
        for i, v in enumerate(self.element_find_elements_by_tag_name(table, "td")):
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
        self.driver_find_element_by_link_text('Register').click()
        self.driver_find_element_by_id("first_name").send_keys("john")
        self.driver_find_element_by_id("last_name").send_keys("doe")
        self.driver_find_element_by_id("email").send_keys("john.doe@ppa.fr")
        self.driver_find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'] + "testcase01!")
        self.driver_find_element_by_id("password2").send_keys(self.app.config['ADMIN_PASSWORD'] + "testcase01!")
        self.driver_find_element_by_id("submit").click()

        self.driver.implicitly_wait(5)

        user = User.query.filter(
            User.first_name == "john",
            User.last_name == "doe",
            User.email == "john.doe@ppa.fr",
            User.confirmed.is_(False)
        ).first()
        self.assertIsNotNone(user)

    def test_reset_password_token(self):
        self.logout()
        # test when you receive the mail and click on the link
        url = self.url_for_with_port("account.reset_password", token="FAKE_TOKEN", _external=True)
        self.driver.get(url)
        self.driver_find_element_by_id("email").send_keys(self.app.config['ADMIN_EMAIL'])
        self.driver_find_element_by_id("new_password").send_keys(self.app.config['ADMIN_PASSWORD'] + "testcase01!")
        self.driver_find_element_by_id("new_password2").send_keys(self.app.config['ADMIN_PASSWORD'] + "testcase01!")
        self.driver_find_element_by_id("submit").click()
        # wrong token so you are redirected to the index page
        self.assertEqual(self.url_for_with_port("main.index", _external=True), self.driver.current_url)

    def test_admin_change_user_email(self):
        foo_email = self.add_user("foo", "bar")
        self.admin_login()
        self.driver_find_element_by_link_text('Dashboard').click()
        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Registered Users"
        ).click()
        self.driver_find_elements_by_class_name("role")[1].click()
        self.driver_find_element_by_link_text('Change email address').click()
        self.driver_find_element_by_id("email").send_keys("bar.foo@ppa.fr")
        self.driver_find_element_by_id("submit").click()
        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "bar.foo@ppa.fr"
        ).first()
        self.assertIsNotNone(user)

    def test_admin_change_role(self):
        foo_email = self.add_user("foo", "bar")
        self.admin_login()
        self.driver_find_element_by_link_text('Dashboard').click()
        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Registered Users"
        ).click()
        self.driver_find_elements_by_class_name("role")[1].click()
        self.driver_find_element_by_link_text('Change account type').click()
        # change user role
        self.driver_find_elements_by_tag_name("option")[1].click()
        self.driver_find_element_by_id("submit").click()
        # assert the change
        user = User.query.filter(User.email == foo_email).first()
        self.assertEqual(user.role_id, int(self.driver_find_elements_by_tag_name("option")[1].get_property("value")))

        # try to change your own admin role
        self.driver_find_element_by_link_text('Dashboard').click()
        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Registered Users"
        ).click()
        self.driver_find_elements_by_class_name("role")[0].click()
        self.driver_find_element_by_link_text('Change account type').click()
        # assert that you cannot change your own role
        self.assertTrue(len(self.driver_find_elements_by_tag_name("option")) == 0)

    def test_change_email_token(self):
        self.logout()
        url = self.url_for_with_port("account.change_email", token="FAKE_TOKEN", _external=True)
        self.driver.get(url)
        self.driver_find_element_by_id("email").send_keys(self.app.config['ADMIN_EMAIL'])
        self.driver_find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver_find_element_by_id("submit").click()
        self.assertEqual(self.url_for_with_port("main.index", _external=True), self.driver.current_url)

    def test_confirm_account(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        url = self.url_for_with_port("account.confirm_request", _external=True)
        self.driver.get(url)
        self.assertEqual(self.url_for_with_port("main.index", _external=True), self.driver.current_url)

    def test_confirm_account_token(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        url = self.url_for_with_port("account.confirm", token="FAKE_TOKEN", _external=True)
        self.driver.get(url)
        self.assertEqual(self.url_for_with_port("main.index", _external=True), self.driver.current_url)

    def test_change_password(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.driver_find_element_by_link_text('Your Account').click()
        self.driver_find_element_by_link_text('Change password').click()
        self.driver_find_element_by_id("old_password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver_find_element_by_id("new_password").send_keys(self.app.config['ADMIN_PASSWORD'] + "new")
        self.driver_find_element_by_id("new_password2").send_keys(self.app.config['ADMIN_PASSWORD'] + "new")
        self.driver_find_element_by_id("submit").click()
        self.logout()
        self.login(foo_email, self.app.config['ADMIN_PASSWORD'] + "new")
        success = self.driver_find_element_by_class_name("alert-success").text
        self.assertTrue(success == "You are now logged in. Welcome back!")

    def test_delete_user(self):
        self.addCorpus("wauchier")
        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, is_owner=True)
        # test that the used is correctly deleted
        self.assertIsNotNone(User.query.filter(User.email == foo_email).first())

        # test that corpora are not deleted when the user is deleted
        self.admin_login()
        self.driver_find_element_by_link_text('Dashboard').click()
        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Registered Users"
        ).click()
        self.driver_find_elements_by_class_name("role")[1].click()
        self.driver_find_element_by_link_text('Delete user').click()
        self.driver_find_element_by_class_name('hidden').click()
        self.driver_find_element_by_class_name("deletion").click()
        self.assertIsNone(User.query.filter(User.email == foo_email).first())

        corpus = Corpus.query.filter(Corpus.name == "Wauchier").first()
        self.assertIsNotNone(corpus)
        self.assertIsNone(CorpusUser.query.filter(CorpusUser.corpus_id == corpus.id).first())

        # assert you cannot delete your own account
        self.driver_find_element_by_link_text('Dashboard').click()
        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Registered Users"
        ).click()
        self.driver_find_elements_by_class_name("role")[0].click()
        self.driver_find_element_by_link_text('Delete user').click()
        self.driver_find_element_by_class_name('hidden').click()
        self.driver_find_element_by_class_name("deletion").click()
        self.assertIsNotNone(User.query.filter(User.email == self.app.config['ADMIN_EMAIL']).first())

    def test_invalid_login(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email + "2")
        danger = self.driver_find_element_by_class_name("alert-danger").text
        self.assertTrue(danger == "Invalid email address.")

    def test_invalid_password(self):
        self.logout()
        foo_email = self.add_user("foo", "bar")
        self.login(foo_email, "wrong_password")
        danger = self.element_find_element_by_class_name(
            self.driver_find_element_by_class_name("alert-danger"),
            "list"
        ).text
        self.assertTrue(danger == "Invalid email or password.")

    def test_invite_new_user(self):
        self.admin_login()
        self.driver_find_element_by_link_text('Dashboard').click()
        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Invite New User"
        ).click()
        self.driver_find_element_by_id("first_name").send_keys("foo")
        self.driver_find_element_by_id("last_name").send_keys("bar")
        self.driver_find_element_by_id("email").send_keys("foo.bar@ppa.fr")
        self.driver_find_element_by_id("submit").click()

        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "foo.bar@ppa.fr",
            User.confirmed.is_(False)
        ).first()
        self.assertTrue(user is not None)
        return user

    def test_join_from_invite(self):
        user = self.test_invite_new_user()
        # being admin
        url = self.url_for_with_port("account.join_from_invite", user_id=user.id, token="FAKE_TOKEN", _external=True)
        self.driver.get(url)

        # being anonymmous
        self.logout()
        self.driver.get(url)
        alert = self.driver_find_element_by_class_name("alert").text
        self.assertTrue(alert == "The confirmation link is invalid or has expired. Another invite email with a new "
                                  "link has been sent to you.")

    def test_unconfirmed(self):
        self.addCorpus("wauchier")
        foo_email = self.add_user("foo", "bar")
        user = User.query.filter(User.first_name == "foo",User.last_name == "bar").first()
        user.confirmed = False
        self.db.session.add(user)
        self.db.session.commit()
        self.login_with_user(foo_email)
        success = self.driver_find_element_by_class_name("alert-success").text
        self.assertTrue(success == "You are now logged in. Welcome back!")
        h3 = self.driver_find_element_by_tag_name("h3").text
        self.assertTrue(h3 == "You need to confirm your account before continuing.")
        # check that you can't nor create corpus nor go to your dashboard while your account is unconfirmed
        self.driver_find_element_by_link_text('New Corpus').click()
        self.driver_find_element_by_link_text('Resend confirmation email')
        self.driver_find_element_by_link_text('Dashboard').click()
        self.driver_find_element_by_link_text('Resend confirmation email')

        self.logout()
        url = self.url_for_with_port("account.unconfirmed", _external=True)
        self.driver.get(url)
        self.assertEqual(self.url_for_with_port("main.index", _external=True), self.driver.current_url)

    def test_admin_add_new_user(self):
        self.admin_login()
        self.driver_find_element_by_link_text('Dashboard').click()

        self.element_find_element_by_partial_link_text(
            self.driver_find_element_by_id('admin-dashboard'),
            "Add New User"
        ).click()
        self.driver_find_element_by_id("first_name").send_keys("foo")
        self.driver_find_element_by_id("last_name").send_keys("bar")
        self.driver_find_element_by_id("email").send_keys("foo.bar@ppa.fr")
        self.driver_find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver_find_element_by_id("password2").send_keys(self.app.config['ADMIN_PASSWORD'])

        self.driver_find_element_by_id("submit").click()

        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "foo.bar@ppa.fr",
            User.confirmed.is_(False)
        ).first()
        self.assertIsNotNone(user)


class TestUserWithMail(TestBase):
    AUTO_LOG_IN = False

    def create_app(self, config_overwrite=None):
        app = super(TestUserWithMail, self).create_app(config_overwrite={"SEND_MAIL_STATUS": True})

        return app

    def test_change_email(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.driver_find_element_by_link_text('Your Account').click()
        self.driver_find_element_by_link_text('Change email address').click()
        self.driver_find_element_by_id("email").send_keys("bar.foo@ppa.fr")
        self.driver_find_element_by_id("password").send_keys(self.app.config['ADMIN_PASSWORD'])
        self.driver_find_element_by_id("submit").click()
        warning = self.driver_find_element_by_class_name("alert-warning").text
        self.assertTrue(warning == "A confirmation link has been sent to %s." % "bar.foo@ppa.fr")

    def test_reset_password(self):
        self.logout()
        self.driver_find_element_by_link_text('Log In').click()
        self.driver_find_element_by_link_text('Forgot password?').click()
        self.driver_find_element_by_id("email").send_keys(self.app.config['ADMIN_EMAIL'])
        self.driver_find_element_by_id("submit").click()
        warning = self.driver_find_element_by_class_name("alert-warning").text
        self.assertTrue(warning == "A password reset link has been sent to %s." % self.app.config['ADMIN_EMAIL'])

        # When anonymous, not redirected to index
        self.driver.get(self.url_for_with_port("account.reset_password_request"))
        self.assertNotEqual(self.url_for_with_port("main.index"), self.driver.current_url)

        # test not being anonymous, you are redirected to the index page
        self.admin_login()
        self.driver.get(self.url_for_with_port("account.reset_password_request"))
        self.assertEqual(self.url_for_with_port("main.index"), self.driver.current_url)
