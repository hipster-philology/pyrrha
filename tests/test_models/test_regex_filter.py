from app.models import ChangeRecord, WordToken, Corpus, ControlLists, Column, AllowedLemma
from .base import TestModels
import copy
from itertools import combinations


SimilarityFixtures = [
    ControlLists(id=1, name="CL Fixture"),
    Corpus(id=1, name="Fixtures !", control_lists_id=1),
    Column(heading="Lemma", corpus_id=1),
    Column(heading="POS", corpus_id=1),
    Column(heading="Morph", corpus_id=1),
    Column(heading="Similar", corpus_id=1),
    WordToken(corpus=1, form="Cil", lemma="celui", left_context="_", right_context="_", label_uniform="celui", morph="smn", POS="p"),  # 1
    WordToken(corpus=1, form="[METADATA:blabla]", lemma="celle", left_context="_", right_context="_", label_uniform="celle", morph="smn", POS="n"),  # 2
    WordToken(corpus=1, form="Cil", lemma="cil", left_context="_", right_context="_", label_uniform="cil", morph="smn", POS="p"),      # 3
    WordToken(corpus=1, form="Cil", lemma="celui", left_context="_", right_context="_", label_uniform="celui", morph="mmn", POS="p"),  # 4
    WordToken(corpus=1, form="Cil", lemma="celui", left_context="_", right_context="_", label_uniform="celui", morph="mmn", POS="n"),  # 5
    WordToken(corpus=1, form="Cil", lemma="cel", left_context="_", right_context="_", label_uniform="cel", morph="smn", POS="p"),      # 6
    WordToken(corpus=1, form="Cil", lemma="cel", left_context="_", right_context="_", label_uniform="cel", morph="smn", POS="p"),      # 7
    WordToken(corpus=1, form="Cil", lemma="cel", left_context="_", right_context="_", label_uniform="cel", morph="smn", POS="p"),      # 8
    AllowedLemma(id=1, label="celui", label_uniform="celui", control_list=1)
]

class TestFilters(TestModels):

    def load_fixtures(self):
        for fixture in SimilarityFixtures:
            self.db.session.add(copy.deepcopy(fixture))
            self.db.session.flush()
        self.db.session.commit()

    def test_filter_allowed_lemma(self):
        """ Ensure that when no filters are registered, everything works as intended """
        self.load_fixtures()
        with self.assertRaises(WordToken.ValidityError):
            token, change_record = WordToken.update(
                user_id=1,
                token_id=1, corpus_id=1,
                form = "Cil", lemma="#", morph="smn", POS="u")

    def test_combinatory_regex(self):
        self.load_fixtures()
        tests = [
            ("celui", None),
            ("#", "filter_punct"),
            ("...", "filter_punct"),
            ("7", "filter_numeral"),
            ("7578", "filter_numeral"),
            ("[IGNORE]", "filter_ignore")
        ]
        situations = ["filter_punct", "filter_numeral", "filter_ignore"]
        cl = self.db.session.get(ControlLists, 1)
        token = self.db.session.get(WordToken, 1)
        corpus = self.db.session.get(Corpus, 1)
        for i in range(len(situations)+1):
            for combi in combinations(situations, i):
                for filtre in situations:
                    setattr(cl, filtre, False)
                for filtre in combi:
                    setattr(cl, filtre, True)
                self.db.session.add(cl)
                self.db.session.commit()
                self.db.session.refresh(token)
                self.db.session.refresh(corpus)
                for category, filtre in tests:
                    validity = WordToken.is_valid(form = token.form, lemma=category, POS=token.POS, morph=token.morph, corpus=corpus)["lemma"]
                    if filtre and filtre in combi or 'celui' in category:
                        self.assertTrue(validity, f"Filters are not working. `{category}` should be matched by `{filtre}` in {', '.join(combi) or 'absence of filters'}")
                    else:
                        self.assertFalse(validity, f"Filters are not working. `{category}` should not be matched by `{filtre}` in {', '.join(combi) or 'absence of filters'}")

    def test_metadata_filter(self):
        self.load_fixtures()
        corpus = self.db.session.get(Corpus, 1)
        cl = self.db.session.get(ControlLists, 1)
        token = corpus.get_unallowed().first()
        self.assertEqual(token.form, "[METADATA:blabla]", f'Metadata are considered as unallowed token when there is no filter metadata.')
        setattr(cl, "filter_metadata", True)
        self.db.session.add(cl)
        self.db.session.commit()
        self.db.session.refresh(corpus)
        token = corpus.get_unallowed().first()
        self.assertNotEqual(token.form, "[METADATA:blabla]", f'Metadata filter is not working. [METADATA:blabla] should not be considered as unallowed.')
        
        token = self.db.session.get(WordToken, 2)
        validity_lemma = WordToken.is_valid(form = token.form, lemma="blabla", POS=token.POS, morph=token.morph,corpus=corpus)["lemma"]
        self.assertTrue(validity_lemma, f"Filter metadata is not working for lemma")
        validity_pos = WordToken.is_valid(form = token.form, lemma=token.lemma, POS="blabla", morph=token.morph,corpus=corpus)["POS"]
        validity_morph = WordToken.is_valid(form = token.form, lemma=token.lemma, POS=token.POS, morph="blabla",corpus=corpus)["morph"]




