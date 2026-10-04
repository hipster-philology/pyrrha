"""Regression tests for the security hardening pass."""
from flask import url_for

from app.models import ChangeRecord, Corpus, CorpusUser, Favorite, User, WordToken
from .base import TestBase

XSS = '<img src=x onerror=alert(1)>'


class TestNavEscaping(TestBase):

    def test_corpus_name_is_escaped_in_nav(self):
        self.addCorpus("wauchier", with_token=False)
        corpus = self.db.session.get(Corpus, 1)
        corpus.name = XSS
        self.db.session.add(corpus)
        self.db.session.commit()
        user = User.query.filter_by(email=self.app.config["ADMIN_EMAIL"]).first()
        self.db.session.add(CorpusUser(user=user, corpus=corpus, is_owner=True))
        self.db.session.add(Favorite(corpus_id=1, user_id=user.id))
        self.db.session.commit()
        html = self.client.get(url_for("main.index")).get_data(as_text=True)
        self.assertNotIn(XSS, html)


class TestChangeRecordIsolation(TestBase):
    """A user with access to corpus 1 must not reach change records of corpus 2."""

    def setUp(self):
        super().setUp()
        self.addCorpus("wauchier", with_token=True)
        self.addCorpus("floovant", with_token=True)
        admin = User.query.filter_by(email=self.app.config["ADMIN_EMAIL"]).first()
        bob = User(first_name="Bob", last_name="Test", email="bob@example.org",
                   password="correct horse battery", confirmed=True)
        self.db.session.add(bob)
        self.db.session.commit()
        self.db.session.add(CorpusUser(user=bob, corpus=self.db.session.get(Corpus, 1), is_owner=True))
        self.foreign_token = WordToken.query.filter_by(corpus=2).first()
        self.foreign_record = ChangeRecord(
            corpus=2, user_id=admin.id, form=self.foreign_token.form,
            lemma=self.foreign_token.lemma, lemma_new="changed-lemma",
            POS=self.foreign_token.POS, POS_new=self.foreign_token.POS,
            morph=self.foreign_token.morph, morph_new=self.foreign_token.morph,
        )
        self.db.session.add(self.foreign_record)
        self.db.session.commit()
        self.record_id = self.foreign_record.id
        self.token_id = self.foreign_token.id
        self.original_lemma = self.foreign_token.lemma

        self.bob = self.app.test_client()
        self.bob.post(url_for("account.login"), data=dict(
            email="bob@example.org", password="correct horse battery"))

    def test_record_page_is_not_reachable_through_other_corpus(self):
        resp = self.bob.get(f"/corpus/1/tokens/changes/similar/{self.record_id}")
        self.assertEqual(resp.status_code, 404)

    def test_record_data_is_not_reachable_through_other_corpus(self):
        resp = self.bob.get(f"/corpus/1/tokens/changes/similar/{self.record_id}/data")
        self.assertEqual(resp.status_code, 404)

    def test_record_cannot_be_applied_through_other_corpus(self):
        resp = self.bob.post(
            f"/corpus/1/tokens/similar/{self.record_id}/update",
            json={"word_tokens": [self.token_id]}
        )
        self.assertEqual(resp.status_code, 404)
        self.db.session.expire_all()
        self.assertEqual(self.db.session.get(WordToken, self.token_id).lemma, self.original_lemma)

    def test_invalid_token_payload_is_rejected(self):
        record = ChangeRecord(
            corpus=1, user_id=1, form="x", lemma="a", lemma_new="b",
            POS="p", POS_new="p", morph=None, morph_new=None
        )
        self.db.session.add(record)
        self.db.session.commit()
        for payload in ({"word_tokens": "1"}, {"word_tokens": [{"a": 1}]}, {}):
            resp = self.bob.post(f"/corpus/1/tokens/similar/{record.id}/update", json=payload)
            self.assertEqual(resp.status_code, 400, payload)
