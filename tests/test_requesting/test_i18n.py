"""Localization: locale selection, French catalog, translated messages and catalog health."""
import re
from glob import glob
from unittest import mock

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from flask import url_for
from flask_babel import force_locale, lazy_gettext

from app.email import send_email_async
from app.models import User
from .base import TestBase

CATALOGS = sorted(glob("translations/*/LC_MESSAGES/messages.po"))


def compile_catalogs():
    """ Compiled catalogs (*.mo) are not versioned: build them like `translate compile` does """
    for po in CATALOGS:
        with open(po, "rb") as src, open(po[:-3] + ".mo", "wb") as dst:
            write_mo(dst, read_po(src))


compile_catalogs()

PLACEHOLDERS = re.compile(r"%\(\w+\)\w|\$\w+\$")


class TestLocaleSelection(TestBase):

    def anonymous(self):
        return self.app.test_client()

    def test_switching_language_through_the_menu(self):
        client = self.anonymous()
        self.assertEqual(client.get("/locale/fr").status_code, 302)
        html = client.get(url_for("account.login")).get_data(as_text=True)
        self.assertIn("Se connecter", html)
        self.assertIn('<html lang="fr">', html)

    def test_logged_in_choice_is_stored_on_the_user(self):
        self.assertEqual(self.client.get("/locale/fr").status_code, 302)
        user = User.query.filter_by(email=self.app.config["ADMIN_EMAIL"]).first()
        self.db.session.refresh(user)
        self.assertEqual(user.locale, "fr")
        html = self.client.get(url_for("main.index")).get_data(as_text=True)
        self.assertIn("Se déconnecter", html)

    def test_unsupported_stored_locale_falls_back_to_english(self):
        user = User.query.filter_by(email=self.app.config["ADMIN_EMAIL"]).first()
        user.locale = "zz"
        self.db.session.add(user)
        self.db.session.commit()
        resp = self.client.get(url_for("main.index"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<html lang="en">', resp.get_data(as_text=True))

    def test_browser_language_is_used_for_visitors(self):
        resp = self.anonymous().get(url_for("account.login"), headers={"Accept-Language": "fr-FR,fr;q=0.9"})
        self.assertIn('<html lang="fr">', resp.get_data(as_text=True))
        resp = self.anonymous().get(url_for("account.login"), headers={"Accept-Language": "de"})
        self.assertIn('<html lang="en">', resp.get_data(as_text=True))

    def test_every_configured_language_can_be_selected(self):
        for code in self.app.config["LANGUAGES"]:
            client = self.anonymous()
            self.assertEqual(client.get(f"/locale/{code}").status_code, 302, code)
            html = client.get(url_for("account.login")).get_data(as_text=True)
            self.assertIn('lang="%s"' % code.replace("_", "-"), html)

    def test_language_menu_lists_every_language(self):
        html = self.client.get(url_for("main.index")).get_data(as_text=True)
        for code, name in self.app.config["LANGUAGES"].items():
            self.assertIn(url_for("main.locale", language=code), html)
            self.assertIn(name, html)


class TestTranslatedMessages(TestBase):

    def test_flash_message_is_translated(self):
        client = self.app.test_client()
        client.get("/locale/fr")
        resp = client.post(url_for("account.login"), data=dict(email="nobody@example.org", password="nope"))
        self.assertIn("Adresse e-mail ou mot de passe incorrect.", resp.get_data(as_text=True))

    def test_flash_message_stays_english_by_default(self):
        client = self.app.test_client()
        resp = client.post(url_for("account.login"), data=dict(email="nobody@example.org", password="nope"))
        self.assertIn("Invalid email or password.", resp.get_data(as_text=True))

    def test_form_labels_are_translated(self):
        client = self.app.test_client()
        client.get("/locale/fr")
        html = client.get(url_for("account.register")).get_data(as_text=True)
        self.assertIn("Prénom", html)
        self.assertIn("Mot de passe", html)

    def test_wtforms_builtin_errors_are_translated(self):
        client = self.app.test_client()
        client.get("/locale/fr")
        html = client.post(url_for("account.register"), data={}).get_data(as_text=True)
        self.assertNotIn("This field is required.", html)

    def test_duplicate_email_error_keeps_a_clickable_link_in_french(self):
        client = self.app.test_client()
        client.get("/locale/fr")
        html = client.post(url_for("account.register"), data=dict(
            first_name="A", last_name="B", email=self.app.config["ADMIN_EMAIL"],
            password="correct horse battery", password2="correct horse battery")).get_data(as_text=True)
        self.assertIn('<a href="/account/reset-password">réinitialisation du mot de passe</a>', html)

    def test_json_message_is_translated(self):
        self.client.get("/locale/fr")
        self.addCorpus("wauchier", with_token=True)
        resp = self.client.post("/corpus/1/tokens/correct/2", data=dict(lemma="", POS="", morph="", form=""))
        self.assertNotIn("No value where changed", resp.get_data(as_text=True))

    def test_pluralised_message(self):
        self.client.get("/locale/fr")
        from flask_babel import ngettext
        with self.app.test_request_context("/"), mock.patch("app.ext_config.get_locale", return_value="fr"):
            from flask_babel import force_locale
            with force_locale("fr"):
                self.assertEqual(ngettext("There is %(num)d lemma.", "There are %(num)d lemmas.", 1), "Il y a 1 lemme.")
                self.assertEqual(ngettext("There is %(num)d lemma.", "There are %(num)d lemmas.", 3), "Il y a 3 lemmes.")


class TestEmailLanguage(TestBase):

    def build_message(self, locale):
        user = User(first_name="Ada", last_name="Lovelace", email="ada@example.org",
                    password="correct horse battery", confirmed=True)
        with self.app.test_request_context("/"), force_locale(locale), mock.patch("app.email.Thread") as thread:
            send_email_async(
                app=self.app, recipient=user.email, subject=lazy_gettext("Confirm Your Account"),
                template="account/email/confirm", user=user, mailTriggerStatus=True,
                confirm_link="http://localhost/confirm/x")
            return thread.call_args.kwargs["args"][1]

    def test_email_is_written_in_the_language_of_the_person_who_triggers_it(self):
        french = self.build_message("fr")
        self.assertIn("Confirmez votre compte", french.subject)
        self.assertIn("Cordialement", french.body)

    def test_email_defaults_to_english(self):
        english = self.build_message("en")
        self.assertIn("Confirm Your Account", english.subject)
        self.assertIn("Sincerely", english.body)


class TestCatalogs(TestBase):

    def test_there_is_a_catalog_for_every_configured_language_but_english(self):
        codes = {po.split("/")[1] for po in CATALOGS}
        self.assertEqual(codes, set(self.app.config["LANGUAGES"]) - {"en"})

    def test_catalogs_are_valid(self):
        for po in CATALOGS:
            with open(po, "rb") as f:
                catalog = read_po(f)
            errors = [(str(m.id)[:60], str(e)) for m, e in catalog.check()]
            self.assertEqual(errors, [], po)

    def test_french_is_complete(self):
        with open("translations/fr/LC_MESSAGES/messages.po", "rb") as f:
            catalog = read_po(f, locale="fr")
        untranslated = [str(m.id)[:60] for m in catalog if m.id and (m.fuzzy or not all(
            m.string if isinstance(m.string, tuple) else [m.string]))]
        self.assertEqual(untranslated, [])

    def test_translations_keep_the_placeholders_of_their_source(self):
        for po in CATALOGS:
            with open(po, "rb") as f:
                catalog = read_po(f)
            for message in catalog:
                if not message.id or message.fuzzy:
                    continue
                sources = message.id if isinstance(message.id, tuple) else (message.id,)
                targets = message.string if isinstance(message.string, tuple) else (message.string,)
                for source, target in zip(sources, targets):
                    if target:
                        self.assertEqual(
                            sorted(PLACEHOLDERS.findall(source)), sorted(PLACEHOLDERS.findall(target)),
                            "%s: %r" % (po, source))
