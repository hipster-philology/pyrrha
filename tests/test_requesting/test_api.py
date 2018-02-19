from .base import TestBase
import json


class TestAPI(TestBase):
    def test_lemma_autocomplete_allowed_lemma(self):
        """ Test that lemma autocomplete works fine with accentuated or non accentuated chars (AllowedLemma loaded)"""
        self.addCorpus(corpus="wauchier", with_token=True, with_allowed_lemma=True)
        accentuated = json.loads(self.client.get("/corpus/1/api/lemma?form=öi").data.decode())
        self.assertEqual(accentuated, ["öir"])
        non_accentuated = json.loads(self.client.get("/corpus/1/api/lemma?form=oir").data.decode())
        self.assertEqual(non_accentuated, ["öir"])

    def test_lemma_autocomplete(self):
        """ Test that lemma autocomplete works fine with accentuated or non accentuated chars """
        self.addCorpus(corpus="wauchier", with_token=True)
        accentuated = json.loads(self.client.get("/corpus/1/api/lemma?form=öi").data.decode())
        self.assertEqual(accentuated, ["öir"])
        non_accentuated = json.loads(self.client.get("/corpus/1/api/lemma?form=oir").data.decode())
        self.assertEqual(non_accentuated, ["öir"])
