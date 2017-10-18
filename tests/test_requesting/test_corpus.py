from tests.test_requesting.base import TestBase
from flask import url_for
from app.models import WordToken, Corpus


class TestCorpus(TestBase):
    def test_reach_index(self):
        response = self.client.get(url_for("main.index"))
        self.assertEqual(response.status_code, 200, "Display of index should work")

    def test_reach_creation_page(self):
        response = self.client.get(url_for("main.corpus_new"))
        self.assertEqual(response.status_code, 200, "Display of form should work")
