"""Tests for the token annotation endpoints, focused on the Gloss column."""
import json
from .base import TestBase


class TestGlossAPI(TestBase):

    def setUp(self):
        super().setUp()
        self.addCorpus("wauchier", with_token=True)

    def _correct(self, token_id, **fields):
        return self.client.post(f"/corpus/1/tokens/correct/{token_id}", data=fields)

    def test_gloss_saved_via_api(self):
        """POST with gloss field persists the value and returns it in the response."""
        resp = self._correct(2, lemma="saint", POS="ADJqua", morph="None", gloss="holy")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["token"]["gloss"], "holy")

    def test_gloss_in_to_dict_response(self):
        """The token dict returned by the save endpoint always contains a gloss key."""
        resp = self._correct(2, lemma="saint", POS="ADJqua", morph="None")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertIn("gloss", body["token"])

    def test_gloss_cleared_to_none(self):
        """Submitting an empty gloss sets it to None."""
        # First set a gloss
        self._correct(2, lemma="saint", POS="ADJqua", morph="None", gloss="holy")
        # Then clear it
        resp = self._correct(2, lemma="saint", POS="ADJqua", morph="None", gloss="")
        body = json.loads(resp.data)
        self.assertIsNone(body["token"]["gloss"])

    def test_gloss_only_change_not_rejected(self):
        """Updating only the gloss field (lemma/POS/morph unchanged) returns 200."""
        # Establish a baseline
        self._correct(2, lemma="saint", POS="ADJqua", morph="None", gloss="first")
        # Change only gloss
        resp = self._correct(2, lemma="saint", POS="ADJqua", morph="None", gloss="second")
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body["token"]["gloss"], "second")
