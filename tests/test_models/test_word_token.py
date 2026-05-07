from .base import TestModels
from app.models import WordToken, Corpus
from app.utils import ValidationError
import random
import string


class TestGetSimilarForBatch(TestModels):
    """Regression tests for get_similar_for_batch — run before and after the SQL rewrite."""

    def _make_corpus(self):
        """Create a minimal corpus with known token forms for deterministic similarity counts."""
        from app.models import ControlLists, Column
        cl = ControlLists(name="TestCL")
        self.db.session.add(cl)
        self.db.session.flush()
        corpus = Corpus(name="SimTest", control_lists_id=cl.id)
        self.db.session.add(corpus)
        self.db.session.flush()
        for col in ("Lemma", "POS", "Morph"):
            self.db.session.add(Column(heading=col, corpus_id=corpus.id))

        tokens = [
            # form "vos", same lemma → each is similar to the other
            WordToken(corpus=corpus.id, order_id=1, form="vos", lemma="vos1", POS="PRO", morph="PERS.=2"),
            WordToken(corpus=corpus.id, order_id=2, form="vos", lemma="vos1", POS="PRO", morph="PERS.=2"),
            # form "de", appears twice but different lemma/POS/morph → not similar
            WordToken(corpus=corpus.id, order_id=3, form="de", lemma="de1", POS="PRE", morph="_"),
            WordToken(corpus=corpus.id, order_id=4, form="de", lemma="de2", POS="ADV", morph="X"),
            # form "et", appears once → similar == 0
            WordToken(corpus=corpus.id, order_id=5, form="et", lemma="et1", POS="CON", morph="_"),
        ]
        for t in tokens:
            self.db.session.add(t)
        self.db.session.commit()
        return corpus, tokens

    def test_similar_count_matching_form_and_lemma(self):
        """Two tokens with same form and same lemma should each show similar=1."""
        corpus, tokens = self._make_corpus()
        page_tokens = [tokens[0], tokens[1]]  # both "vos" tokens
        WordToken.get_similar_for_batch(corpus, page_tokens)
        self.assertEqual(page_tokens[0].similar, 1)
        self.assertEqual(page_tokens[1].similar, 1)

    def test_similar_count_different_annotation(self):
        """Two tokens with same form but no overlapping annotation should each show similar=0."""
        corpus, tokens = self._make_corpus()
        page_tokens = [tokens[2], tokens[3]]  # both "de", different lemma/POS/morph
        WordToken.get_similar_for_batch(corpus, page_tokens)
        self.assertEqual(page_tokens[0].similar, 0)
        self.assertEqual(page_tokens[1].similar, 0)

    def test_similar_count_unique_form(self):
        """A token whose form appears only once should show similar=0."""
        corpus, tokens = self._make_corpus()
        page_tokens = [tokens[4]]  # "et" — only one occurrence
        WordToken.get_similar_for_batch(corpus, page_tokens)
        self.assertEqual(page_tokens[0].similar, 0)

    def test_similar_count_empty_batch(self):
        """Empty token list should not raise."""
        corpus, _ = self._make_corpus()
        WordToken.get_similar_for_batch(corpus, [])  # must not raise


class TestWordToken(TestModels):
    def test_to_input_format(self):
        """ Test that export to input format works correctly """
        self.addCorpus("floovant", tokens_up_to=3)
        self.assertEqual(
            WordToken.to_input_format(
                WordToken.query.filter(WordToken.corpus == 2)
            ),
            "token_id\tform\tlemma\tPOS\tmorph\r\n"
            "1\tSOIGNORS\tseignor\t_\tNOMB.=p|GENRE=m|CAS=n\r\n"
            "2\tor\tor4\t_\tDEGRE=-\r\n"
            "3\tescoutez\tescouter\t_\tMODE=imp|PERS.=2|NOMB.=p\r\n"
        )

    def test_add_batch_invalid(self):
        """Test adding a batch of tokens.

        Trying: one token violates length constraint
        Expecting: ValidationError
        """
        self.addCorpus("floovant", tokens_up_to=3)
        corpus_id = Corpus.query.one().id
        form = "".join(
            string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)] for i in range(200)
        )
        with self.assertRaises(ValidationError):
            WordToken.add_batch(corpus_id, [{"form": form}])

    def test_add_batch_valid(self):
        """Test adding a batch of tokens.

        Trying: one token respecting length constraint
        Expecting: number of tokens is returned
        """
        self.addCorpus("floovant", tokens_up_to=3)
        corpus_id = Corpus.query.one().id
        form = "".join(
            string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)]
            for i in range(64)
        )
        self.assertEqual(WordToken.add_batch(corpus_id, [{"form": form}]), 1)

    def test_add_batch_chunked_order_ids_are_sequential(self):
        """Sending tokens in multiple chunks must produce strictly sequential order_ids.

        Regression: before the fix, each chunk reset order_id to 1, causing duplicates.
        """
        self.addCorpus("floovant", tokens_up_to=0)
        corpus_id = Corpus.query.one().id

        chunk1 = [{"form": f"w{i}"} for i in range(3)]
        chunk2 = [{"form": f"w{i}"} for i in range(3, 6)]

        WordToken.add_batch(corpus_id, chunk1)
        self.db.session.commit()
        offset = WordToken.query.filter_by(corpus=corpus_id).count()
        WordToken.add_batch(corpus_id, chunk2, order_id_offset=offset)
        self.db.session.commit()

        order_ids = [
            t.order_id
            for t in WordToken.query.filter_by(corpus=corpus_id).order_by(WordToken.order_id).all()
        ]
        self.assertEqual(order_ids, list(range(1, 7)))

    def test_update_batch_context(self):
        """Test updating left and right context.

        Trying: set right and left context to 4.
        """
        self.addCorpus("floovant", tokens_up_to=0)
        corpus_id = Corpus.query.one().id
        form_list = [
            {
                "form": "".join(
                    string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)]
                    for i in range(16)
                )
            } for j in range(200)
        ]
        WordToken.add_batch(corpus_id, form_list)
        self.assertEqual(WordToken.update_batch_context(corpus_id, 4, 4), len(form_list))
        token = WordToken.query.filter_by(corpus=corpus_id, order_id=15).first()
        left_context = token.left_context.split(" ")
        right_context = token.right_context.split(" ")
        self.assertEqual(len(left_context), 4)
        self.assertEqual(len(right_context), 4)
        # WordToken order_id starts at 1, form_list indices starts at 0
        self.assertEqual(left_context[0], form_list[10]["form"])
        self.assertEqual(left_context[3], form_list[13]["form"])
        self.assertEqual(right_context[0], form_list[15]["form"])
        self.assertEqual(right_context[3], form_list[18]["form"])

    def test_remove_corpus(self):
        self.addCorpus("wauchier")
        self.assertEqual(self.db.session.get(Corpus, 1).name, "Wauchier", "The corpus exists")
        self.db.session.delete(self.db.session.get(Corpus, 1))
        self.db.session.commit()
        self.assertEqual(self.db.session.get(Corpus, 1), None, "The corpus does not exist")

    def test_remove_corpus_with_custom_dict(self):
        self.addCorpus("wauchier")
        corpus: Corpus = self.db.session.get(Corpus, 1)
        self.assertEqual(corpus.name, "Wauchier", "The corpus exists")
        # Add connections
        corpus.custom_dictionaries_update("lemma", "test")
        self.assertEqual(corpus.get_custom_dictionary("lemma", formatted=True), "test")
        # Delete the corpus
        self.db.session.delete(self.db.session.get(Corpus, 1))
        self.db.session.commit()
        self.assertEqual(self.db.session.get(Corpus, 1), None, "The corpus does not exist")

