import copy
from app.models import ChangeRecord, WordToken, Corpus, ControlLists, Column
from .base import TestModels


_FIXTURES = [
    ControlLists(id=1, name="GlossCL"),
    Corpus(id=1, name="GlossCorpus", control_lists_id=1),
    Column(heading="Lemma", corpus_id=1),
    Column(heading="POS", corpus_id=1),
    Column(heading="Morph", corpus_id=1),
    Column(heading="Gloss", corpus_id=1),
    WordToken(corpus=1, order_id=1, form="mot", lemma="mot1", POS="NOM", morph="sg", label_uniform="mot1", gloss=None),
    WordToken(corpus=1, order_id=2, form="mot", lemma="mot1", POS="NOM", morph="sg", label_uniform="mot1", gloss="word"),
]


class TestGloss(TestModels):

    def load(self):
        for obj in _FIXTURES:
            self.db.session.add(copy.deepcopy(obj))
        self.db.session.commit()

    # ── WordToken ──────────────────────────────────────────────────────────

    def test_update_saves_gloss(self):
        """update() persists a new gloss value."""
        self.load()
        token, _ = WordToken.update(
            user_id=1, corpus_id=1, token_id=1,
            lemma="mot1", POS="NOM", morph="sg", gloss="a word"
        )
        self.assertEqual(token.gloss, "a word")
        refreshed = self.db.session.get(WordToken, 1)
        self.assertEqual(refreshed.gloss, "a word")

    def test_update_gloss_no_validity_error(self):
        """Any string is accepted for gloss — no control-list validation."""
        self.load()
        token, _ = WordToken.update(
            user_id=1, corpus_id=1, token_id=1,
            lemma="mot1", POS="NOM", morph="sg", gloss="anything goes ¡™£"
        )
        self.assertEqual(token.gloss, "anything goes ¡™£")

    def test_update_gloss_accepts_none(self):
        """Passing gloss=None clears an existing gloss."""
        self.load()
        # token 2 has gloss="word"; clear it
        token, _ = WordToken.update(
            user_id=1, corpus_id=1, token_id=2,
            lemma="mot1", POS="NOM", morph="sg", gloss=None
        )
        self.assertIsNone(token.gloss)

    def test_update_gloss_alone_not_nothing_changed(self):
        """Changing only gloss does NOT raise NothingChangedError."""
        self.load()
        # token 1 has gloss=None; change only gloss
        token, _ = WordToken.update(
            user_id=1, corpus_id=1, token_id=1,
            lemma="mot1", POS="NOM", morph="sg", gloss="new gloss"
        )
        self.assertEqual(token.gloss, "new gloss")

    def test_update_nothing_changed_includes_gloss(self):
        """NothingChangedError is raised when lemma/POS/morph/gloss all unchanged."""
        self.load()
        with self.assertRaises(WordToken.NothingChangedError):
            WordToken.update(
                user_id=1, corpus_id=1, token_id=2,
                lemma="mot1", POS="NOM", morph="sg", gloss="word"
            )

    def test_to_dict_includes_gloss(self):
        """to_dict() exposes the gloss field."""
        self.load()
        token = self.db.session.get(WordToken, 2)
        d = token.to_dict()
        self.assertIn("gloss", d)
        self.assertEqual(d["gloss"], "word")

    # ── ChangeRecord ───────────────────────────────────────────────────────

    def test_change_record_tracks_gloss(self):
        """ChangeRecord stores old and new gloss after an update."""
        self.load()
        _, record = WordToken.update(
            user_id=1, corpus_id=1, token_id=1,
            lemma="mot1", POS="NOM", morph="sg", gloss="annotated"
        )
        self.assertIsNone(record.gloss)           # old value
        self.assertEqual(record.gloss_new, "annotated")  # new value

    def test_change_record_changed_includes_gloss(self):
        """ChangeRecord.changed lists 'gloss' when gloss was modified."""
        self.load()
        _, record = WordToken.update(
            user_id=1, corpus_id=1, token_id=1,
            lemma="mot1", POS="NOM", morph="sg", gloss="annotated"
        )
        self.assertIn("gloss", record.changed)

    def test_change_record_changed_excludes_gloss_when_unchanged(self):
        """ChangeRecord.changed does not list 'gloss' when gloss stayed the same."""
        self.load()
        # Change POS (not gloss) so update() doesn't raise NothingChangedError
        _, record = WordToken.update(
            user_id=1, corpus_id=1, token_id=2,
            lemma="mot1", POS="VER", morph="sg", gloss="word"
        )
        self.assertNotIn("gloss", record.changed)
