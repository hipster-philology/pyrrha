import json
from .base import TestBase
from app.models import AllowedLemma


class TestAddExistingLemmas(TestBase):
    """ Adding lemmas that already exist must not fail (issue #358) """

    def _add(self, lemmas):
        return self.client.open("/controls/1/read/lemma", method="UPDATE",
                                json={"lemmas": lemmas})

    def test_existing_lemmas_are_skipped(self):
        self.addCorpus("wauchier", with_token=True)
        self.assertEqual(self._add("alpha beta").status_code, 200)
        resp = self._add("beta gamma delta")
        self.assertEqual(resp.status_code, 200, resp.data)
        labels = sorted(l.label for l in AllowedLemma.query.filter_by(control_list=1))
        self.assertEqual(labels, ["alpha", "beta", "delta", "gamma"])
        self.assertIn("1", json.loads(resp.data)["message"])
