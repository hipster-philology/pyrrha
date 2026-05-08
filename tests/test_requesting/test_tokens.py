"""Tests for the token annotation endpoints, focused on the Gloss column and review feature."""
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


class TestReviewAPI(TestBase):

    def setUp(self):
        super().setUp()
        self.addCorpus("wauchier", with_token=True)

    def _mark_review(self, token_id, needs_review, comment=None):
        data = {'needs_review': 'true' if needs_review else 'false'}
        if comment:
            data['review_comment'] = comment
        return self.client.post(f'/corpus/1/tokens/review/{token_id}', data=data)

    def test_mark_for_review(self):
        resp = self._mark_review(2, True, comment='Check this form')
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertTrue(body['token']['needs_review'])
        self.assertEqual(body['token']['review_comment'], 'Check this form')

    def test_unmark_review_clears_comment(self):
        self._mark_review(2, True, comment='Check this form')
        resp = self._mark_review(2, False)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertFalse(body['token']['needs_review'])
        self.assertIsNone(body['token']['review_comment'])

    def test_needs_review_keys_in_to_dict(self):
        resp = self._mark_review(2, True)
        body = json.loads(resp.data)
        self.assertIn('needs_review', body['token'])
        self.assertIn('review_comment', body['token'])

    def test_needs_review_filter_data_endpoint(self):
        self._mark_review(2, True, comment='check')
        resp = self.client.get('/corpus/1/tokens/needs-review/data')
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body['total'], 1)
        self.assertTrue(body['tokens'][0]['needs_review'])

    def test_needs_review_filter_page(self):
        resp = self.client.get('/corpus/1/tokens/needs-review')
        self.assertEqual(resp.status_code, 200)
