from .test_record import SimilarityFixtures
from app.models import ChangeRecord, WordToken, Corpus, ControlLists, ControlListsUser, CorpusUser, Column
from .base import TestModels
import copy
from itertools import combinations


class TestFilters(TestModels):

    def load_fixtures(self):
        for fixture in SimilarityFixtures:
            self.db.session.add(copy.deepcopy(fixture))
        self.db.session.commit()

    def test_filter_allowed_lemma(self):
        """ Ensure that when no filters are registered, everything works as intended """
        self.load_fixtures()
        with self.assertRaises(WordToken.ValidityError):
            token, change_record = WordToken.update(
                user_id=1,
                token_id=1, corpus_id=1,
                lemma="#", morph="smn", POS="u")

    def test_combinatory_regex(self):
        self.load_fixtures()
        tests = [
            ("celui", None),
            ("#", "filter_punct"),
            ("...", "filter_punct"),
            ("7", "filter_numeral"),
            ("7578", "filter_numeral"),
            ("[METADATA:infomation]", "filter_metadata"),
            ("[12.0:blabla]", "filter_metadata"),
            ("[IGNORE]", "filter_ignore")
        ]
        situations = ["filter_punct", "filter_numeral", "filter_metadata", "filter_ignore"]
        cl = ControlLists.query.get(1)
        token = WordToken.query.get(1)
        corpus = Corpus.query.get(1)
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
                    validity = WordToken.is_valid(lemma=category, POS=token.POS, morph=token.morph, corpus=corpus)["lemma"]
                    if filtre in combi:
                        self.assertTrue(validity, "Filters are not working. Some elements that should not match the regex are being matched.")
                    else:
                        self.assertFalse(validity, "Filters are not working. Some elements are not match by the regex filters.")
