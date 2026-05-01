"""Shared helper mixin for Playwright tests.

Test classes inherit from one of the Helpers classes below and set
self.page / self.url_for / self.app in an autouse setup fixture.
"""
import csv
from typing import Union, Optional

import flask_login
from playwright.sync_api import expect

from app import db
from app.models import (
    Column,
    ControlLists,
    ControlListsUser,
    Corpus,
    CorpusUser,
    Favorite,
    User,
    WordToken,
)
from tests.db_fixtures import add_control_lists, add_corpus

LOREM_IPSUM = (
    "form\tlemma\tPOS\tmorph\n"
    "Lorem\t\t\t\n"
    "ipsum\t\t\t\n"
    "dolor\t\t\t\n"
    "sit\t\t\t\n"
    "amet\t\t\t\n"
    ",\t\t\t\n"
    "consectetur\t\t\t\n"
    "adipiscing\t\t\t\n"
    "elit\t\t\t\n"
    ".\t\t\t"
)


class Helpers:
    """Browser + ORM helpers shared across all test classes.

    :property page:
    """

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self, email, password):
        self.page.goto(self.url_for("account.login"))
        self.page.locator("#email").fill(email)
        self.page.locator("#password").fill(password)
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

    def logout(self):
        self.page.goto(self.url_for("account.logout"))

    def login_with_user(self, email):
        self.logout()
        self.login(email, self.app.config["ADMIN_PASSWORD"])

    def admin_login(self):
        self.login_with_user(self.app.config["ADMIN_EMAIL"])

    def go_to_control_list_curation(self, name):
        self.page.locator("#cl-dd").click()
        self.page.locator("#cl-dd").get_by_role("link", name="Manage", exact=False).click()

        controllists_dashboard = self.page.locator("#list-browser-cl")
        controllists_dashboard.get_by_role("link", name=name).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_admin_corpus_page(self):
        self.page.get_by_role("link", name="Admin", exact=False).first.click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="All Corpora", exact=False).click()
        self.page.wait_for_load_state("networkidle")

    def get_corpus_names_in_list_browser(self, admin: bool = False, get_next: bool = False):
        self.page.wait_for_load_state("networkidle")
        corpora_dashboard = self.page.locator("#list-browser-corpora table")
        if admin:
            td_for_name_nth = 1
        else:
            td_for_name_nth = 2
        current_page = sorted(
            [
                el.text_content().strip()
                for el in corpora_dashboard.locator(f"tbody tr td:nth-child({td_for_name_nth})").all()
            ]
        )
        if get_next is False:
            return current_page
        next_link = self.page.locator(".pagination .page-item:not(.disabled) .next-link")
        if next_link.count() == 0:
            return current_page
        else:
            next_link.first.click()
            self.page.wait_for_load_state("networkidle")
            return sorted(
                current_page + self.get_corpus_names_in_list_browser(admin=admin, get_next=get_next)
            )
    # ------------------------------------------------------------------
    # ORM helpers
    # ------------------------------------------------------------------

    def addCorpus(self, corpus, cl=True, **kwargs):
        corpus_obj = add_corpus(corpus.lower(), db, cl, **kwargs)
        if not kwargs.get("no_corpus_user", False):
            self.addCorpusUser(
                corpus_obj.name,
                self.app.config["ADMIN_EMAIL"],
                is_owner=kwargs.get("is_owner", True),
            )
        self.page.goto(self.url_for("main.index"))
        return corpus_obj

    def addCorpusUser(self, corpus_name, email, is_owner=False, _commit=True):
        corpus = Corpus.query.filter(Corpus.name == corpus_name).first()
        user = User.query.filter(User.email == email).first()
        new_cu = CorpusUser(corpus=corpus, user=user, is_owner=is_owner)
        db.session.add(new_cu)
        if _commit:
            db.session.commit()
        return new_cu

    def addControlLists(self, cl_name, **kwargs):
        cl = add_control_lists(cl_name, db, **kwargs)
        self.page.goto(self.url_for("main.index"))
        if not kwargs.get("no_corpus_user", False):
            self.addControlListsUser(
                cl.name,
                self.app.config["ADMIN_EMAIL"],
                is_owner=kwargs.get("is_owner", True),
            )
        for entry in kwargs.get("for_users", []):
            user_email = entry.user if hasattr(entry, "user") else entry[0]
            owner = entry.owner if hasattr(entry, "owner") else entry[1]
            self.addControlListsUser(cl.name, user_email, is_owner=owner)
        return cl

    def addControlListsUser(self, cl_name: Union[str, int], email, is_owner=False):
        if isinstance(cl_name, str):
            cl = ControlLists.query.filter(ControlLists.name == cl_name).first()
        else:
            cl = ControlLists.query.filter(ControlLists.id == cl_name).first()
        user = User.query.filter(User.email == email).first()
        new_clu = ControlListsUser(control_lists_id=cl.id, user_id=user.id, is_owner=is_owner)
        db.session.add(new_clu)
        db.session.commit()
        return new_clu

    def add_user(self, first_name, last_name, is_admin=False):
        email = f"{first_name}.{last_name}@ppa.fr"
        new_user = User(
            confirmed=True,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=self.app.config["ADMIN_PASSWORD"],
            role_id=2 if is_admin else 1,
        )
        db.session.add(new_user)
        db.session.commit()
        return email

    def add_favorite_via_db(self, user_id, corpora_ids, reset: bool = True):
        if reset:
            Favorite.query.filter_by(user_id=user_id).delete()
        for corpus_id in corpora_ids:
            db.session.add(Favorite(user_id=user_id, corpus_id=corpus_id))
        db.session.commit()
        self.page.reload()

    def get_admin_id(self):
        user = User.query.filter(User.email == self.app.config["ADMIN_EMAIL"]).first()
        return user.id

    def add_control_lists(self):
        ControlLists.add_default_lists()
        db.session.commit()

    def add_n_corpora(self, n_corpus):
        user = User.query.filter(User.email == self.app.config["ADMIN_EMAIL"]).first()
        for n in range(n_corpus):
            corpus = Corpus(
                name="a" * (n + 1),
                control_lists_id=1,
                columns=[
                    Column(heading="Lemma"),
                    Column(heading="POS"),
                    Column(heading="Morph"),
                    Column(heading="Similar"),
                ],
            )
            new_cu = CorpusUser(corpus=corpus, user=user, is_owner=True)
            db.session.add(corpus)
            db.session.add(new_cu)
            db.session.flush()
        db.session.commit()

    # ------------------------------------------------------------------
    # Browser helpers
    # ------------------------------------------------------------------

    def token_dropdown_link(self, tok_id, link, corpus_id="1"):
        self.page.goto(self.url_for("main.tokens_correct", corpus_id=corpus_id))
        self.page.locator(f"[data-token-order='{tok_id}'] .at-dd-toggle").click()
        dd = self.page.locator(f"[data-token-order='{tok_id}'] .at-dd-menu:visible")
        dd.get_by_role("link", name=link).click()
        self.page.wait_for_load_state("networkidle")

    def writeMultiline(self, locator, text):
        locator.fill(text)

    def write_lorem_ipsum_tokens(self):
        self.page.locator("#tokens").fill(LOREM_IPSUM)

    def wait_until_shown(self, element_id):
        self.page.locator(f"#{element_id}").wait_for(state="visible", timeout=5000)

    def wait_until_count(self, selector, cnt):
        expect(self.page.locator(selector)).to_have_count(cnt, timeout=5000)

    def create_temp_example_file(self, tmp_path):
        file_path = tmp_path / "test.csv"
        with open(file_path, "wt", newline="") as fp:
            writer = csv.writer(fp, delimiter=",")
            writer.writerow(["form", "lemma", "POS", "morph"])
            writer.writerow(["SOIGNORS", "seignor", "NOMcom", "NOMB.=p|GENRE=m|CAS=n"])
        return file_path


class TokenCorrectHelpers(Helpers):
    """Helpers for token correction tests."""

    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def addCorpus(self, **kwargs):
        return super().addCorpus(self.CORPUS, **kwargs)

    def go_to_edit_token_page(self, corpus_id=None, as_callback=True):
        if corpus_id is None:
            corpus_id = self.CORPUS_ID

        def callback():
            self.page.goto(self.url_for("main.tokens_correct", corpus_id=corpus_id))

        if as_callback:
            return callback
        return callback()

    def assert_token_has_values(self, token, lemma=None, POS=None, morph=None):
        if lemma:
            assert token.lemma == lemma, f"[Lemma] {token.lemma!r} should be {lemma!r}"
        if POS:
            assert token.POS == POS, f"[POS] {token.POS!r} should be {POS!r}"
        if morph:
            assert token.morph == morph, f"[Morph] {token.morph!r} should be {morph!r}"

    def _get_badge_text(self, row, badge_class):
        row_id = row.get_attribute("id")
        return self.page.locator(f"[rel='{row_id}'] {badge_class}").text_content().strip()

    def get_similar_badge(self, row):
        row_id = row.get_attribute("id")
        return self.page.locator(f"[rel='{row_id}'] .similar-link")

    def get_similar_hint(self, token_id):
        return self.page.locator(f"#token_{token_id}_similar_hint span").first

    def assert_saved(self, row):
        assert row.locator(".save-status.save-ok:visible").count() == 1

    def assert_invalid_value(self, row, category):
        assert row.locator(f'[data-field="{category}"] .field-error-popdown').count() == 1

    def assert_unchanged(self, row):
        assert row.locator(".save-status.save-unchanged:visible").count() == 1

    def first_token_id(self, corpus_id):
        return (
            db.session.query(WordToken.id)
            .filter_by(corpus=corpus_id)
            .order_by(WordToken.order_id)
            .limit(1)
            .first()[0]
        )

    def _get_td_input(self, id_row: str, value_type: str):
        row = self.page.locator(f"#token_{id_row}_row")
        if value_type == "POS":
            td = row.locator("[data-field='POS'] .anno-field-input")
        elif value_type == "morph":
            td = row.locator("[data-field='morph'] .anno-field-input")
        elif value_type == "gloss":
            td = row.locator("[data-field='gloss'] .anno-field-input")
        else:
            td = row.locator("[data-field='lemma'] .anno-field-input")
        return row, td

    def edith_nth_row_value(
        self,
        value,
        value_type="lemma",
        id_row="1",
        corpus_id=None,
        autocomplete_selector=None,
        additional_action_before=None,
        go_to_edit_token_page=None,
    ):
        if corpus_id is None:
            corpus_id = self.CORPUS_ID

        if go_to_edit_token_page is None:
            go_to_edit_token_page = self.go_to_edit_token_page(corpus_id)
        go_to_edit_token_page()
        self.page.wait_for_load_state("networkidle")

        if additional_action_before is not None:
            additional_action_before()

        if autocomplete_selector:
            return self._edit_nth_row_value_autocomplete(
                value=value,
                id_row=id_row,
                value_type=value_type,
                autocomplete_selector=autocomplete_selector,
            )

        row, td = self._get_td_input(id_row, value_type)
        td.click()
        td.fill("")
        td.type(value)

        row.locator("button.save-btn").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(f"#token_{id_row}_row .save-status").wait_for(
            state="visible", timeout=10000
        )

        token = db.session.get(WordToken, int(id_row))
        db.session.refresh(token)

        return (
            token,
            row,
        )

    def _edit_nth_row_value_autocomplete(
        self, value, id_row="1", value_type="lemma", autocomplete_selector=None
    ):
        row, td = self._get_td_input(id_row, value_type)
        td.click()
        td.fill("")
        td.type(value)

        self.page.wait_for_load_state("networkidle")
        autocomplete_el = self.page.locator(autocomplete_selector)
        autocomplete_el.wait_for(state="visible", timeout=5000)
        autocomplete_el.click()

        row.locator("button.save-btn").click()

        self.page.locator(f"#token_{id_row}_row .save-ok").wait_for(
            state="visible", timeout=10000
        )

        token = db.session.get(WordToken, int(id_row))
        db.session.refresh(token)

        return (
            token,
            row,
        )


class TokenCorrect2CorporaHelpers(TokenCorrectHelpers):
    def addCorpus(self, **kwargs):
        Helpers.addCorpus(self, "wauchier", **kwargs)
        Helpers.addCorpus(self, "floovant", **kwargs)


class TokensSearchHelpers(Helpers):
    CORPUS_ID = 1

    def go_to_search_tokens_page(self, corpus_id, as_callback=True):
        def callback():
            self.page.goto(self.url_for("main.tokens_search_through_fields", corpus_id=corpus_id))

        if as_callback:
            return callback
        return callback()

    def fill_filter_row(self, form, lemma, pos, morph):
        row = self.page.locator("#filter_row")
        for field_name, field_value in (
            ("lemma", lemma),
            ("form", form),
            ("POS", pos),
            ("morph", morph),
        ):
            td = row.locator(f"[name='{field_name}']")
            td.click()
            td.fill("" if field_value is None else str(field_value))

    def search(self, form="", lemma="", pos="", morph="", case_insensitivity=False,
               corpus_id: Optional[int] = None):
        self.go_to_search_tokens_page(corpus_id or self.CORPUS_ID, as_callback=False)
        self.fill_filter_row(form, lemma, pos, morph)
        if case_insensitivity:
            self.page.locator("#caseBox").click()
        self.page.locator("#submit_search").click()

        result = []

        self.page.wait_for_load_state("networkidle")

        def get_field(row_loc, f):
            return row_loc.locator(f".anno-field[data-field='{f}'] .anno-field-input").first.input_value().strip()

        while True:
            # Wait until the loading indicator is gone before reading rows
            self.page.locator(".at-table-wrap .at-loading").wait_for(state="hidden", timeout=10000)
            res_table = self.page.locator(".at-table-wrap")
            for row_loc in res_table.locator(".at-row").all():
                result.append(
                    {
                        "form": row_loc.locator(".at-cell--form").text_content().strip(),
                        "lemma": get_field(row_loc, "lemma"),
                        "morph": get_field(row_loc, "morph"),
                        "pos": get_field(row_loc, "POS"),
                    }
                )
            if self.page.locator(".at-pagination").first.locator(".page-next.disabled").count() > 0:
                break
            else:
                self.page.locator(".at-pagination").first.locator(".page-next a").click()

        return result
