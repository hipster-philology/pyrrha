from .base import TestModels
from app.models import Bookmark, WordToken
from app import db


class TestBookmarkMark(TestModels):
    """Tests for Bookmark.mark() after the PK simplification to (corpus_id, user_id).

    With the old three-column PK (corpus_id, user_id, token_id), re-bookmarking
    the same token from two concurrent requests caused a UniqueViolation because
    both sessions ran DELETE before either committed, then both tried to INSERT
    the same row.  The fix is to make (corpus_id, user_id) the PK so that
    re-bookmarking is always a plain UPDATE.
    """

    def setUp(self):
        super().setUp()
        self.addCorpus("wauchier")
        self.token = WordToken.query.first()
        self.corpus_id = self.token.corpus
        self.user_id = 1  # admin created by add_default_users()

    def test_mark_creates_bookmark(self):
        bm = Bookmark.mark(self.corpus_id, self.user_id, self.token.id, page=1)
        self.assertEqual(bm.token_id, self.token.id)
        self.assertEqual(bm.page, 1)

    def test_mark_same_token_twice_updates_in_place(self):
        """Re-bookmarking the same token must update the existing row, not crash."""
        Bookmark.mark(self.corpus_id, self.user_id, self.token.id, page=1)
        bm = Bookmark.mark(self.corpus_id, self.user_id, self.token.id, page=3)
        self.assertEqual(bm.page, 3)
        self.assertEqual(
            Bookmark.query.filter_by(
                corpus_id=self.corpus_id, user_id=self.user_id
            ).count(),
            1,
        )

    def test_mark_different_token_replaces_bookmark(self):
        """Bookmarking a different token updates the single bookmark row."""
        tokens = WordToken.query.filter_by(corpus=self.corpus_id).limit(2).all()
        self.assertEqual(len(tokens), 2)
        Bookmark.mark(self.corpus_id, self.user_id, tokens[0].id, page=1)
        bm = Bookmark.mark(self.corpus_id, self.user_id, tokens[1].id, page=2)
        self.assertEqual(bm.token_id, tokens[1].id)
        self.assertEqual(
            Bookmark.query.filter_by(
                corpus_id=self.corpus_id, user_id=self.user_id
            ).count(),
            1,
        )
