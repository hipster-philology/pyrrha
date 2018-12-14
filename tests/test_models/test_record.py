from app.models import ChangeRecord, WordToken, Corpus, ControlLists
from .base import TestModels
import copy


SimilarityFixtures = [
    ControlLists(id=1, name="CL Fixture"),
    Corpus(id=1, name="Fixtures !", control_lists_id=1),
    WordToken(corpus=1, form="Cil", lemma="celui", left_context="_", right_context="_", label_uniform="celui", morph="smn", POS="p"),  # 1
    WordToken(corpus=1, form="Cil", lemma="celle", left_context="_", right_context="_", label_uniform="celle", morph="smn", POS="n"),  # 2
    WordToken(corpus=1, form="Cil", lemma="cil", left_context="_", right_context="_", label_uniform="cil", morph="smn", POS="p"),      # 3
    WordToken(corpus=1, form="Cil", lemma="celui", left_context="_", right_context="_", label_uniform="celui", morph="mmn", POS="p"),  # 4
    WordToken(corpus=1, form="Cil", lemma="celui", left_context="_", right_context="_", label_uniform="celui", morph="mmn", POS="n"),  # 5
    WordToken(corpus=1, form="Cil", lemma="cel", left_context="_", right_context="_", label_uniform="cel", morph="smn", POS="p"),      # 6
    WordToken(corpus=1, form="Cil", lemma="cel", left_context="_", right_context="_", label_uniform="cel", morph="smn", POS="p"),      # 7
    WordToken(corpus=1, form="Cil", lemma="cel", left_context="_", right_context="_", label_uniform="cel", morph="smn", POS="p"),      # 8
]


class TestChangeRecord(TestModels):
    def test_changed_property(self):
        """ Ensure current change property is working correction """
        record = ChangeRecord(
            user_id=1,
            lemma="1", morph="2", POS="3",
            lemma_new="1", morph_new="2", POS_new="3"
        )
        record.lemma_new = "2"
        self.assertEqual(record.changed, ["lemma"])
        record.lemma_new = "1"
        record.morph_new = "3"
        self.assertEqual(record.changed, ["morph"])
        record.morph_new = "2"
        record.POS_new = "2"
        self.assertEqual(record.changed, ["POS"])
        record.morph_new = "1"
        self.assertCountEqual(record.changed, ["POS", "morph"])
        record.morph_new = "2"
        record.lemma_new = "2"
        self.assertCountEqual(record.changed, ["POS", "lemma"])
        record.morph_new = "4"
        self.assertCountEqual(record.changed, ["POS", "lemma", "morph"])

    def load_fixtures(self):
        for fixture in SimilarityFixtures:
            self.db.session.add(copy.deepcopy(fixture))
        self.db.session.commit()

    def tok_with_id(self, list_of_tokens, _id):
        """ Return the token with given id

        :param list_of_tokens:
        :return:
        """
        return [t for t in list_of_tokens if t.id == _id][0]

    def test_similar_lemma_single_change(self):
        """ Ensure only similar features are fixed """
        self.load_fixtures()
        token, change_record = WordToken.update(
            user_id=1,
            token_id=1, corpus_id=1,
            lemma="cil", morph="smn", POS="p"
        )
        self.assertEqual(
            (token.lemma, token.morph, token.POS),
            ("cil", "smn", "p"),
            "All that was None was not changed"
        )
        similar = WordToken.get_similar_to_record(change_record)
        self.assertEqual(
            [t.id for t in sorted(similar, key=lambda x:x.id)],
            [4, 5],
            "4 and 5 are similar"
        )

        tokens = change_record.apply_changes_to(user_id=1, token_ids=[4, 5])
        tok_4 = self.tok_with_id(tokens, 4)
        self.assertEqual(tok_4.lemma, "cil", "Lemma was updated")
        self.assertEqual(tok_4.morph, "mmn", "Morph stayed the same as it was not changed")
        self.assertEqual(tok_4.POS, "p", "POS stayed the same as it was not changed")

        tok_5 = self.tok_with_id(tokens, 5)
        self.assertEqual(tok_5.lemma, "cil", "Lemma was updated")
        self.assertEqual(tok_5.morph, "mmn", "Morph stayed the same as it was not changed")
        self.assertEqual(tok_5.POS, "n", "POS stayed the same as it was not changed")

    def test_similar_lemma_double_change(self):
        """ Ensure only similar features are fixed """
        self.load_fixtures()
        token, change_record = WordToken.update(
            user_id=1,
            token_id=1, corpus_id=1,
            lemma="cil", morph="smn", POS="u"
        )
        self.assertEqual(
            (token.lemma, token.morph, token.POS),
            ("cil", "smn", "u"),
            "All that was different was changed"
        )
        similar = WordToken.get_similar_to_record(change_record)
        self.assertEqual(
            [t.id for t in sorted(similar, key=lambda x:x.id)],
            [3, 4, 5],
            "4 and 5 are similar; 3 has a common lemma with the new lemma created"
        )

        tokens = change_record.apply_changes_to(user_id=1, token_ids=[3, 4, 5])
        # 3 : Common lemma new with already "cil" in this token, but different P that needs to be updated
        tok_3 = self.tok_with_id(tokens, 3)
        self.assertEqual(tok_3.lemma, "cil", "Lemma was already the same")
        self.assertEqual(tok_3.morph, "smn", "Morph stayed the same as it was not changed")
        self.assertEqual(tok_3.POS, "u", "POS was changed")

        # 4 : Common old lemma, lemma updated + pos updated; morph ignored even if different
        tok_4 = self.tok_with_id(tokens, 4)
        self.assertEqual(tok_4.lemma, "cil", "Lemma was updated")
        self.assertEqual(tok_4.morph, "mmn", "Morph stayed the same as it was not changed")
        self.assertEqual(tok_4.POS, "u", "POS was updated")

        # 4 : Common old lemma, lemma updated updated; morph + POS ignored even if different
        tok_5 = self.tok_with_id(tokens, 5)
        self.assertEqual(tok_5.lemma, "cil", "Lemma was updated")
        self.assertEqual(tok_5.morph, "mmn", "Morph stayed the same as it was not changed")
        self.assertEqual(tok_5.POS, "n", "POS stayed the same as it was not common with original token")

        # Check number of change record ands IDS of lemmas
        crs = self.db.session.query(ChangeRecord).all()
        self.assertEqual(len(crs), 4, "There has been 1 original change and 3 others")
        self.assertEqual(
            [cr.word_token_id for cr in sorted(crs, key=lambda t: t.word_token_id)], [1, 3, 4, 5],
            "Changed record should be about the right records"
        )
        cr5 = [cr for cr in crs if cr.word_token_id == 5][0]
        self.assertEqual(
            (cr5.lemma, cr5.morph, cr5.POS, cr5.lemma_new, cr5.morph_new, cr5.POS_new),
            ("celui", "mmn", "n", "cil", "mmn", "n"),
            "Change record should be correct"
        )
        self.assertEqual(cr5.changed, ["lemma"])

        cr4 = [cr for cr in crs if cr.word_token_id == 4][0]
        self.assertEqual(
            (cr4.lemma, cr4.morph, cr4.POS, cr4.lemma_new, cr4.morph_new, cr4.POS_new),
            ("celui", "mmn", "p", "cil", "mmn", "u"),
            "Change record should be correct"
        )
        self.assertCountEqual(cr4.changed, ["lemma", "POS"])
