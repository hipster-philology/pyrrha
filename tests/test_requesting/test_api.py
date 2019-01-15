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

    def test_morph_autocomplete(self):
        """ Test that morph autocomplete works fine with accentuated or non accentuated chars """
        self.addCorpus(corpus="floovant", with_token=True, with_allowed_morph=True)
        accentuated = json.loads(self.client.get("/controls/2/api/morph?form=2 plur").data.decode())
        self.assertEqual(accentuated, [
            {'label': 'impératif 2e personne pluriel',
                'value': 'MODE=imp|PERS.=2|NOMB.=p'},
            {'label': '2e personne pluriel masculin régime',
                'value': 'PERS.=2|NOMB.=p|GENRE=m|CAS=r'},
        ])
        non_accentuated = json.loads(self.client.get("/controls/2/api/morph?form=%3Dr %3Dp").data.decode())
        self.assertEqual(
            non_accentuated,
            [{'label': 'pluriel masculin régime', 'value': 'NOMB.=p|GENRE=m|CAS=r'},
             {'label': 'singulier féminin régime positif',
              'value': 'NOMB.=s|GENRE=f|CAS=r|DEGRE=p'},
             {'label': '2e personne pluriel masculin régime',
              'value': 'PERS.=2|NOMB.=p|GENRE=m|CAS=r'},
             {'label': '3e personne pluriel masculin régime',
              'value': 'PERS.=3|NOMB.=p|GENRE=m|CAS=r'}]
        )

    def test_edit_then_apply_similar(self):
        """ Test that lemma autocomplete works fine with accentuated or non accentuated chars """
        self.addCorpus(corpus="wauchier", with_token=True)
        correction = json.loads(
            self.client.post(
                "/corpus/1/tokens/correct/2",
                data={"POS": "ADJqua", "lemma": "martin", "morph": "None"}
            ).data.decode()
        )
        self.assertEqual(
            correction,
            {'token': {'form': 'seint', 'morph': 'None', 'context': 'De seint Martin mout doit', 'lemma': 'martin',
                       'POS': 'ADJqua', 'order_id': 2, 'id': 2, 'corpus': 1},
             'similar': {'count': 3, 'link': '/corpus/1/tokens/changes/similar/1'}}
        )
        corr_similar = json.loads(
            self.client.post(
                "/corpus/1/tokens/similar/1/update",
                data=json.dumps({"word_tokens": [82, 227, 267]}),
                       content_type='application/json'
            ).data.decode()
        )
        self.assertCountEqual(
            corr_similar,
            [{'morph': 'None', 'order_id': 82, 'POS': 'VERcjg', 'id': 82, 'context': 'si com li seint home firent ça',
              'lemma': 'martin', 'form': 'seint', 'corpus': 1},
             {'morph': 'None', 'order_id': 227, 'POS': 'VERcjg', 'id': 227,
              'context': 'se gardent li seint home qi par', 'lemma': 'martin', 'form': 'seint', 'corpus': 1},
             {'morph': 'None', 'order_id': 267, 'POS': 'VERcjg', 'id': 267,
              'context': 'ce regarderent li seint confessors et mes', 'lemma': 'martin', 'form': 'seint', 'corpus': 1}]
        )