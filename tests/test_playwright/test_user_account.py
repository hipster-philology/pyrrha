"""Tests for user account management (AUTO_LOG_IN=False)."""
import pytest

from app.models import User, Corpus, CorpusUser
from app import create_app
from tests.test_playwright.base import Helpers
from tests.test_playwright.conftest import PORT


class TestUserAccount(Helpers):
    @pytest.fixture
    def auto_login(self):
        return False

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_user_info(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.page.get_by_role("link", name="Your Account").click()
        self.page.wait_for_load_state("networkidle")
        tds = self.page.locator("table td").all()
        info = {}
        last_key = None
        for i, td in enumerate(tds):
            text = td.text_content().strip()
            if i % 2 == 0:
                info[text] = ""
                last_key = text
            else:
                info[last_key] = text

        assert info["Full name"] == "foo bar"
        assert info["Email address"] == "foo.bar@ppa.fr"
        assert info["Account type"] == "User"

    def test_registration(self):
        self.logout()
        self.page.get_by_role("link", name="Register").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#first_name").fill("john")
        self.page.locator("#last_name").fill("doe")
        self.page.locator("#email").fill("john.doe@ppa.fr")
        self.page.locator("#password").fill(self.app.config["ADMIN_PASSWORD"] + "testcase01!")
        self.page.locator("#password2").fill(self.app.config["ADMIN_PASSWORD"] + "testcase01!")
        self.page.evaluate("const s = document.querySelector('#submit'); if(s) s.removeAttribute('disabled');")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        user = User.query.filter(
            User.first_name == "john",
            User.last_name == "doe",
            User.email == "john.doe@ppa.fr",
            User.confirmed.is_(False),
        ).first()
        assert user is not None

    def test_reset_password_token(self):
        self.logout()
        url = self.url_for("account.reset_password", token="FAKE_TOKEN")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#email").fill(self.app.config["ADMIN_EMAIL"])
        self.page.locator("#new_password").fill(self.app.config["ADMIN_PASSWORD"] + "testcase01!")
        self.page.locator("#new_password2").fill(self.app.config["ADMIN_PASSWORD"] + "testcase01!")
        self.page.evaluate("const s = document.querySelector('#submit'); if(s) s.removeAttribute('disabled');")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.index") in self.page.url

    def test_admin_change_user_email(self):
        foo_email = self.add_user("foo", "bar")
        self.admin_login()
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Registered Users").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".role").nth(1).click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Change email address").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#email").fill("bar.foo@ppa.fr")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "bar.foo@ppa.fr",
        ).first()
        assert user is not None

    def test_admin_change_role(self):
        foo_email = self.add_user("foo", "bar")
        self.admin_login()
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Registered Users").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".role").nth(1).click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Change account type").click()
        self.page.wait_for_load_state("networkidle")
        select = self.page.locator("select").first
        option = select.locator("option").nth(1)
        expected_role_id = int(option.get_attribute("value"))
        select.select_option(value=str(expected_role_id))
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        user = User.query.filter(User.email == foo_email).first()
        assert user.role_id == expected_role_id

        # try to change your own admin role
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Registered Users").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".role").nth(0).click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Change account type").click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator("option").count() == 0

    def test_change_email_token(self):
        self.logout()
        url = self.url_for("account.change_email", token="FAKE_TOKEN")
        self.page.goto(url)
        self.page.locator("#email").fill(self.app.config["ADMIN_EMAIL"])
        self.page.locator("#password").fill(self.app.config["ADMIN_PASSWORD"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.index") in self.page.url

    def test_confirm_account(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        url = self.url_for("account.confirm_request")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.index") in self.page.url

    def test_confirm_account_token(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        url = self.url_for("account.confirm", token="FAKE_TOKEN")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.index") in self.page.url

    def test_change_password(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.page.get_by_role("link", name="Your Account").click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Change password").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#old_password").fill(self.app.config["ADMIN_PASSWORD"])
        self.page.locator("#new_password").fill(self.app.config["ADMIN_PASSWORD"] + "new")
        self.page.locator("#new_password2").fill(self.app.config["ADMIN_PASSWORD"] + "new")
        self.page.evaluate("const s = document.querySelector('#submit'); if(s) s.removeAttribute('disabled');")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        self.logout()
        self.login(foo_email, self.app.config["ADMIN_PASSWORD"] + "new")
        assert self.page.locator(".alert-success").text_content().strip() == "You are now logged in. Welcome back!"

    def test_delete_user(self):
        self.addCorpus("wauchier")
        foo_email = self.add_user("foo", "bar")
        self.addCorpusUser("Wauchier", foo_email, is_owner=True)
        foo_user = User.query.filter(User.email == foo_email).first()
        assert foo_user is not None
        foo_id = foo_user.id

        self.admin_login()
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Registered Users").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".role").nth(1).click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Delete user").click()
        self.page.wait_for_load_state("networkidle")
        # checkbox is display:none — trigger change via jQuery to get href, then navigate
        self.page.evaluate("$('input[type=checkbox]').prop('checked', true).trigger('change');")
        delete_href = self.page.locator(".deletion").get_attribute("href")
        self.page.goto(f"http://localhost:{PORT}{delete_href}")
        self.page.wait_for_load_state("networkidle")

        assert User.query.filter(User.email == foo_email).first() is None
        corpus = Corpus.query.filter(Corpus.name == "Wauchier").first()
        assert corpus is not None
        assert CorpusUser.query.filter(CorpusUser.user_id == foo_id).first() is None

        # assert you cannot delete your own account
        self.page.locator("#main-nav").get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Registered Users").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".role").nth(0).click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Delete user").click()
        self.page.wait_for_load_state("networkidle")
        self.page.evaluate(
            "$('input[type=checkbox]').prop('checked', true).trigger('change');"
            "window.location.href = $('.deletion').attr('href');"
        )
        self.page.wait_for_load_state("networkidle")
        assert User.query.filter(User.email == self.app.config["ADMIN_EMAIL"]).first() is not None

    def test_invalid_login(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email + "2")
        assert self.page.locator(".alert-danger").text_content().strip() == "Invalid email address."

    def test_invalid_password(self):
        self.logout()
        foo_email = self.add_user("foo", "bar")
        self.login(foo_email, "wrong_password")
        assert (
            self.page.locator(".alert-danger .list").text_content().strip()
            == "Invalid email or password."
        )

    def test_invite_new_user(self):
        self.admin_login()
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Invite New User").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#first_name").fill("foo")
        self.page.locator("#last_name").fill("bar")
        self.page.locator("#email").fill("foo.bar@ppa.fr")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "foo.bar@ppa.fr",
            User.confirmed.is_(False),
        ).first()
        assert user is not None
        return user

    def test_join_from_invite(self):
        user = self.test_invite_new_user()
        url = self.url_for("account.join_from_invite", user_id=user.id, token="FAKE_TOKEN")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

        self.logout()
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        alert = self.page.locator(".alert").first.text_content().strip()
        assert alert == (
            "The confirmation link is invalid or has expired. "
            "Another invite email with a new link has been sent to you."
        )

    def test_unconfirmed(self):
        from app import db
        self.addCorpus("wauchier")
        foo_email = self.add_user("foo", "bar")
        user = User.query.filter(User.first_name == "foo", User.last_name == "bar").first()
        user.confirmed = False
        db.session.add(user)
        db.session.commit()
        self.login_with_user(foo_email)
        assert self.page.locator(".alert-success").text_content().strip() == "You are now logged in. Welcome back!"
        assert self.page.locator("h3").first.text_content().strip() == "You need to confirm your account before continuing."

        self.page.get_by_role("link", name="New Corpus").click()
        self.page.get_by_role("link", name="Resend confirmation email")
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.get_by_role("link", name="Resend confirmation email")

        self.logout()
        url = self.url_for("account.unconfirmed")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.index") in self.page.url

    def test_admin_add_new_user(self):
        self.admin_login()
        self.page.get_by_role("link", name="Dashboard").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#admin-dashboard").get_by_role("link", name="Add New User").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#first_name").fill("foo")
        self.page.locator("#last_name").fill("bar")
        self.page.locator("#email").fill("foo.bar@ppa.fr")
        self.page.locator("#password").fill(self.app.config["ADMIN_PASSWORD"])
        self.page.locator("#password2").fill(self.app.config["ADMIN_PASSWORD"])
        self.page.evaluate("const s = document.querySelector('#submit'); if(s) s.removeAttribute('disabled');")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        user = User.query.filter(
            User.first_name == "foo",
            User.last_name == "bar",
            User.email == "foo.bar@ppa.fr",
            User.confirmed.is_(False),
        ).first()
        assert user is not None

    def _fill_register_form(self, first, last, email, password):
        self.page.get_by_role("link", name="Register").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#first_name").fill(first)
        self.page.locator("#last_name").fill(last)
        self.page.locator("#email").fill(email)
        self.page.locator("#password").fill(password)
        self.page.locator("#password2").fill(password)
        self.page.evaluate("const s = document.querySelector('#submit'); if(s) s.removeAttribute('disabled');")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

    def test_register_same_address(self):
        pw = self.app.config["ADMIN_PASSWORD"] + "testcase01!"
        self._fill_register_form("john", "doe", "john.doe@ppa.fr", pw)
        self._fill_register_form("john", "doe", "john.doe@ppa.fr", pw)

        assert sorted(
            [e.text_content().strip() for e in self.page.locator(".alert.alert-danger").all()]
        ) == sorted(["Unable to register a user with the provided information. Link to password reset"])

        self._fill_register_form("john", "doe", "John.Doe@ppa.fr", pw)

        assert sorted(
            [e.text_content().strip() for e in self.page.locator(".alert.alert-danger").all()]
        ) == sorted(["Unable to register a user with the provided information. Link to password reset"])

        users = User.query.filter(
            User.first_name == "john", User.last_name == "doe", User.confirmed.is_(False)
        ).all()
        assert len(users) == 1

    def test_connexion_with_different_cases(self):
        pw = self.app.config["ADMIN_PASSWORD"] + "testcase01!"
        self._fill_register_form("john", "doe", "john.doe@ppa.fr", pw)
        self.logout()

        self.page.get_by_role("link", name="Log In").click()
        self.page.locator("#email").fill("John.Doe@ppa.fr")
        self.page.locator("#password").fill(self.app.config["ADMIN_PASSWORD"] + "testcase01!")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        assert sorted(
            [e.text_content().strip() for e in self.page.locator(".alert.alert-success").all()]
        ) == sorted(["You are now logged in. Welcome back!"])


class TestUserWithMail(Helpers):
    @pytest.fixture
    def auto_login(self):
        return False

    @pytest.fixture
    def app(self, auto_login):
        flask_app = create_app("test")
        flask_app.config.update(
            SEND_MAIL_STATUS=True,
            JSONIFY_PRETTYPRINT_REGULAR=False,
            LIVESERVER_PORT=PORT,
        )
        flask_app.DEBUG = True
        flask_app.client = flask_app.test_client()
        return flask_app

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_change_email(self):
        foo_email = self.add_user("foo", "bar")
        self.login_with_user(foo_email)
        self.page.get_by_role("link", name="Your Account").click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Change email address").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#email").fill("bar.foo@ppa.fr")
        self.page.locator("#password").fill(self.app.config["ADMIN_PASSWORD"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert-warning").text_content().strip()
            == "A confirmation link has been sent to %s." % "bar.foo@ppa.fr"
        )

    def test_reset_password(self):
        self.logout()
        self.page.get_by_role("link", name="Log In").click()
        self.page.get_by_role("link", name="Forgot password?").click()
        self.page.locator("#email").fill(self.app.config["ADMIN_EMAIL"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        assert (
            self.page.locator(".alert-warning").text_content().strip()
            == "A password reset link has been sent to %s." % self.app.config["ADMIN_EMAIL"]
        )

        # When anonymous, not redirected to index
        self.page.goto(self.url_for("account.reset_password_request"))
        self.page.wait_for_load_state("networkidle")
        assert self.page.url != self.url_for("main.index")

        # When logged in, redirected to index
        self.admin_login()
        self.page.goto(self.url_for("account.reset_password_request"))
        self.page.wait_for_load_state("networkidle")
        assert self.url_for("main.index") in self.page.url
