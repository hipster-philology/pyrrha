# Base Python
import csv
import io
import enum
from typing import Iterable, Optional, Dict, List
# PIP Packages
import unidecode
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref
import sqlalchemy.exc
from sqlalchemy import func, literal, not_
from werkzeug.exceptions import BadRequest
from flask import url_for
# Application imports
from .. import db
from ..utils import validate_length
from ..utils.forms import strip_or_none
from ..utils.tsv import TSV_CONFIG
from ..errors import MissingTokenColumnValue, NoTokensInput
from app.utils import PreferencesUpdateError
# Models
from .user import User
from .control_lists import ControlLists, AllowedPOS, AllowedMorph, AllowedLemma, PublicationStatus


from collections import namedtuple


CorpusStatistics = namedtuple("CorpusStatistics",
                              field_names=["word_count", "changes", "forms_edited", "unallowed",
                                           "lemma_acc", "pos_acc", "morph_acc",
                                           "lemma_count", "pos_count", "morph_count"])


class CorpusUser(db.Model):
    """
        Association proxy that link users to corpora
        :param corpus_id: a corpus ID
        :param user_id: a user ID
    """
    corpus_id = db.Column(db.Integer, db.ForeignKey("corpus.id", ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    is_owner = db.Column(db.Boolean, default=False)

    corpus = db.relationship("Corpus", backref=backref("corpus_users", cascade="all, delete"))
    user = db.relationship(User, backref=backref("corpus_users", cascade="all, delete-orphan"))

    def __init__(self, user, corpus, is_owner=False):
        self.user = user
        self.corpus = corpus
        self.is_owner = is_owner


class Column(db.Model):
    """Column."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus_id = db.Column(db.Integer, db.ForeignKey("corpus.id"))
    heading = db.Column(db.String(32))
    hidden = db.Column(db.Boolean, default=False)


class Corpus(db.Model):
    """ A corpus is a set of tokens that is independent from others.
    This allows for multi-text management

    :param id: ID of the corpus
    :type id: int
    :param name: Name of the corpus
    :type name: str

    :ivar id: ID of the corpus
    :type id: int
    :ivar name: Name of the corpus
    :type name: str
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)
    context_left = db.Column(db.SmallInteger, default=3)
    context_right = db.Column(db.SmallInteger, default=3)
    control_lists_id = db.Column(db.Integer, db.ForeignKey('control_lists.id'), nullable=False)
    delimiter_token = db.Column(db.String(12), default=None)

    control_lists = db.relationship("ControlLists")
    word_token_history = db.relationship('TokenHistory', lazy='select', cascade="all, delete-orphan")
    users = association_proxy('corpus_users', 'user')
    word_token = db.relationship("WordToken", cascade="all,delete", lazy="select")
    changes = db.relationship("ChangeRecord", cascade="all,delete")
    columns = db.relationship("Column", cascade="all,delete")

    @property
    def last_change(self):
        return ChangeRecord.query.filter(
            ChangeRecord.corpus == self.id
        ).order_by(ChangeRecord.id.desc()).first()

    def allowed_search_route(self, allowed_type):
        """ Returns the API search routes and parameters

        :param allowed_type: Allowed Type to search values for
        :return: Search route
        """
        if self.control_lists:
            if self.control_lists.has_list(allowed_type):
                return url_for("control_lists_bp.search_api", control_list_id=self.control_lists_id,
                               allowed_type=allowed_type)
        return url_for("main.search_value_api", corpus_id=self.id, allowed_type=allowed_type)

    def custom_dictionary_search_route(self, category):
        """ Returns the API search routes and parameters

        :param category: category to search values for
        :return: Corpus Custom Dictionary Search route
        """
        return url_for("main.custom_dictionary_search_value_api", corpus_id=self.id, category=category)

    @staticmethod
    def static_has_access(corpus_id, user):
        """
        Can this corpus be accessed by the given user ?
        :param user:
        :return: True or False
        """
        if not user.is_admin():
            return db.session.query(literal(True)).filter(
                CorpusUser.query.filter(
                    db.and_(
                        CorpusUser.user_id == user.id,
                        CorpusUser.corpus_id == corpus_id
                    )
                ).exists()
            ).scalar()
        return True

    def changes_per_day(self):
        return list([
            tuple(elem)
            for elem in db.session.query(
                    db.func.count(ChangeRecord.id), db.func.strftime("%Y-%m-%d", ChangeRecord.created_on)
                ).filter(
                    ChangeRecord.corpus == self.id
                ).group_by(
                    db.func.strftime("%Y-%m-%d", ChangeRecord.created_on)
                ).all()
        ])

    def has_access(self, user):
        """ Can this corpus be accessed by the given user ?

        :param user: User to check access rights for
        :return: True or False
        """
        if not user.is_admin():
            return db.session.query(literal(True)).filter(
                CorpusUser.query.filter(
                    db.and_(
                        CorpusUser.user_id == user.id,
                        CorpusUser.corpus_id == self.id
                    )
                ).exists()
            ).scalar()
        return True

    @property
    def statistics(self) -> CorpusStatistics:
        """ Returns some nice statistics on the dashboard
        """
        total = self.tokens_count
        changes = ChangeRecord.query.filter(ChangeRecord.corpus == self.id).count()

        forms_edited = TokenHistory.query.filter(TokenHistory.corpus == self.id).count()

        lemma_acc = pos_acc = morph_acc = None
        all_type = all_lemma = all_morph = False

        if "lemma" in self.displayed_columns_by_name:
            lemma_acc = ChangeRecord.query.distinct(ChangeRecord.word_token_id).filter(
                db.and_(
                    ChangeRecord.corpus == self.id,
                    ChangeRecord.lemma != ChangeRecord.lemma_new
                )
            ).count()
            # Todo: Make sure this is optimized.
            all_lemma = db.session.query(
                AllowedLemma.label).filter(AllowedLemma.control_list == self.control_lists_id)

        if "POS" in self.displayed_columns_by_name:
            pos_acc = ChangeRecord.query.distinct(ChangeRecord.word_token_id).filter(
                db.and_(
                    ChangeRecord.corpus == self.id,
                    ChangeRecord.POS != ChangeRecord.POS_new
                )
            ).count()
            # Todo: Make sure this is optimized.
            all_type = db.session.query(AllowedPOS.label).filter(AllowedPOS.control_list == self.control_lists_id)

        if "morph" in self.displayed_columns_by_name:
            morph_acc = ChangeRecord.query.distinct(ChangeRecord.word_token_id).filter(
                db.and_(
                    ChangeRecord.corpus == self.id,
                    ChangeRecord.morph != ChangeRecord.morph_new
                )
            ).count()
            # Todo: Make sure this is optimized.
            all_morph = db.session.query(AllowedMorph.label).filter(AllowedMorph.control_list == self.control_lists_id)

        unallowed = db.session.query(WordToken.id).filter(
            db.and_(
                WordToken.corpus == self.id,
                db.or_(
                    WordToken.morph.notin_(all_morph) if all_morph else False,
                    WordToken.lemma.notin_(all_lemma) if all_lemma else False,
                    WordToken.POS.notin_(all_type) if all_type else False,
                )
            )
        ).count()

        return CorpusStatistics(
            total, changes, forms_edited, unallowed,
            lemma_acc and lemma_acc / total * 100 if total > 0 else 0,
            pos_acc and pos_acc / total * 100 if total > 0 else 0,
            morph_acc and morph_acc / total * 100 if total > 0 else 0,
            lemma_acc, pos_acc, morph_acc
        )

    @staticmethod
    def fav_for_user(current_user, _all=True):
        corpora = db.session.query(Corpus).filter(
            db.and_(
                CorpusUser.corpus_id == Corpus.id,
                CorpusUser.user_id == current_user.id,
                Favorite.user_id == CorpusUser.user_id,
                Favorite.corpus_id == Corpus.id
            )
        )
        if _all:
            return corpora.all()
        else:
            return corpora

    @staticmethod
    def for_user(current_user, _all=True):
        corpora = Corpus.query.filter(
            db.and_(
                CorpusUser.corpus_id == Corpus.id,
                CorpusUser.user_id == current_user.id
            )
        )
        if _all:
            return corpora.all()
        else:
            return corpora

    def is_owned_by(self, user):
        return db.session.query(literal(True)).filter(
            CorpusUser.query.filter(
                db.and_(
                    CorpusUser.user_id == user.id,
                    CorpusUser.corpus_id == self.id,
                    CorpusUser.is_owner == True
                )
            ).exists()
        ).scalar()

    def get_allowed_values(self, allowed_type="lemma", label=None, order_by="label", extend_to_custom: bool = True):
        """ List values that are allowed (without label) or checks that given label is part
        of the existing corpus

        :param allowed_type: A value from the set "lemma", "POS", "morph"
        :param label: Value to match with as the POS, lemma or morph
        :param extend_to_custom: Whether to use custom dictionary
        :return: Flask SQL Alchemy Query
        :rtype: BaseQuery
        """
        if allowed_type == "lemma":
            cls = AllowedLemma
            order_by = getattr(cls, order_by)
        elif allowed_type == "POS":
            cls = AllowedPOS
            order_by = getattr(cls, order_by)
        elif allowed_type == "morph":
            cls = AllowedMorph
            order_by = getattr(cls, order_by)
        else:
            raise ValueError("Get Allowed value had %s and it's not from the lemma, POS, morph set" % allowed_type)

        if label is not None:
            return db.session.query(cls).filter(
                db.and_(cls.control_list == self.control_lists_id, cls.label == label)
            ).order_by(order_by)
        return db.session.query(cls).filter(cls.control_list == self.control_lists_id).order_by(order_by)

    def get_unallowed(self, allowed_type="lemma"):
        """ Search for WordToken that would not comply with Allowed Values (in AllowedLemma,
        AllowedPOS, AllowedMorph) nor with a corpus custom dictionary

        :param allowed_type: A value from the set "lemma", "POS", "morph"
        :return: Flask SQL Alchemy Query
        :rtype: BaseQuery
        """
        if allowed_type == "lemma":
            cls = AllowedLemma
            prop = WordToken.lemma
        elif allowed_type == "POS":
            cls = AllowedPOS
            prop = WordToken.POS
        elif allowed_type == "morph":
            cls = AllowedMorph
            prop = WordToken.morph
        else:
            raise ValueError("Get Allowed value had %s and it's not from the lemma, POS, morph set" % allowed_type)

        allowed = db.session.query(cls).filter(
            cls.control_list == self.control_lists_id,
            cls.label == prop
        )
        custom_dict = db.session.query(CorpusCustomDictionary).filter(
            CorpusCustomDictionary.corpus == self.id,
            CorpusCustomDictionary.category == allowed_type,
            CorpusCustomDictionary.label == prop
        )
        return db.session.query(WordToken).filter(
            db.and_(
                WordToken.corpus == self.id,
                not_(allowed.exists()),
                not_(custom_dict.exists())
            )
        ).order_by(WordToken.order_id)

    @property
    def tokens_count(self):
        """ Count the number of tokens

        :rtype: int
        """
        # ToDo: This is so slow that it is impossible to use it on the Dashboard page
        return db.session.query(db.func.count()).filter(WordToken.corpus==self.id).scalar()

    @property
    def displayed_columns_by_name(self):
        displayed_columns_by_name = {}
        for column in self.columns:
            if column.hidden:
                continue
            if column.heading != "POS":
                displayed_columns_by_name[column.heading.lower()] = column
            else:
                displayed_columns_by_name["POS"] = column
        return displayed_columns_by_name

    def get_columns_headings(self, ignore=("Similar", )):
        return [
            col.heading
            for col in self.columns
            if not col.hidden and col.heading not in ignore
        ]

    def get_tokens(self):
        """ Retrieve WordTokens from the Corpus

        :return: Tokens Query
        """
        return WordToken.query.filter_by(corpus=self.id).order_by(WordToken.order_id)

    def changed(self, tokens):
        if db.session.bind.dialect.name != "postgresql":
            data = db.session.query(ChangeRecord.word_token_id).group_by(ChangeRecord.word_token_id).filter(
                ChangeRecord.word_token_id.in_([tok.id for tok in tokens])
            ).all()
        else:
            data = db.session.query(ChangeRecord.word_token_id).distinct(ChangeRecord.word_token_id).filter(
                ChangeRecord.word_token_id.in_([tok.id for tok in tokens])
            ).all()
        return set([token for token, *_ in data])

    def get_history(self, page=1, limit=100):
        """ Retrieve ChangeRecord from the Corpus

        :param page: Page to retrieve
        :type page: int
        :param limit: Hits per page
        :type limit: int
        :return: Pagination of records
        """
        return ChangeRecord.query.filter_by(corpus=self.id).order_by(ChangeRecord.created_on.desc()).paginate(page=page, per_page=limit)

    @staticmethod
    def create(
            name, word_tokens_dict,
            allowed_lemma=None, allowed_POS=None, allowed_morph=None,
            context_left=None, context_right=None, control_list: ControlLists = None,
            delimiter_token=None, columns=None
    ):
        """ Create a corpus

        :param name: Name of the corpus
        :param word_tokens_dict: Generator yielding a dictionaries of tokens
        :param allowed_lemma: List of allowed lemma
        :param allowed_POS: List of allowed POS
        :param allowed_morph: list of Allowed Morph in the form of dict with keys (label, readable)
        :param context_left: Number of tokens to keep on the left
        :param context_right: Number of tokens to keep on the right
        :param control_list: Control list to reuse
        :param delimiter_token: Token used for separating passages
        :return: Created Corpus
        :rtype: Corpus
        """
        try:
            if not control_list:
                control_list = ControlLists(name="Control List {}".format(name), public=PublicationStatus.private)
                db.session.add(control_list)
                db.session.flush()

                if allowed_lemma is not None and len(allowed_lemma) > 0:
                    AllowedLemma.add_batch(allowed_lemma, control_list.id)

                if allowed_POS is not None and len(allowed_POS) > 0:
                    AllowedPOS.add_batch(allowed_POS, control_list.id)

                if allowed_morph is not None and len(allowed_morph) > 0:
                    AllowedMorph.add_batch(allowed_morph, control_list.id)

            c = Corpus(
                name=name,
                control_lists_id=control_list.id,
                delimiter_token=delimiter_token,
                context_left=context_left,
                context_right=context_right,
                columns=columns
            )
            db.session.add(c)
            db.session.commit()
        except (sqlalchemy.exc.StatementError, sqlalchemy.exc.IntegrityError) as e:
            db.session.rollback()
            raise e

        token_count = WordToken.add_batch(
            corpus_id=c.id, word_tokens_dict=word_tokens_dict,
            context_left=context_left, context_right=context_right
        )

        if token_count == 0:
            raise NoTokensInput("No tokens were given")

        return c

    def update_allowed_values(self, allowed_type, allowed_values):
        """ Update allowed values of the current corpus

        :param allowed_type: Allowed Value Type (lemma, morph, POS)
        :param allowed_values: New values
        :return: Bool of success
        """
        if allowed_type == "lemma":
            cls = AllowedLemma
        elif allowed_type == "POS":
            cls = AllowedPOS
        elif allowed_type == "morph":
            cls = AllowedMorph
        else:
            raise BadRequest("The type is not of lemma, morph or POS")

        data = db.session.query(cls).filter_by(control_list=self.control_lists_id).delete()
        cls.add_batch(allowed_values, self.id, _commit=True)
        return data

    def get_bookmark(self, user: User) -> Optional["Bookmark"]:
        """ Retrieve a bookmark for a given user. None if not found
        """
        return Bookmark.query.filter(db.and_(
            Bookmark.user_id == user.id,
            Bookmark.corpus_id == self.id
        )).first()

    def toggle_favorite(self, user_id: int) -> bool:
        fav = Favorite.query.filter(db.and_(
            Favorite.corpus_id == self.id,
            Favorite.user_id == user_id
        ))
        if fav.first():
            db.session.delete(fav.first())
        else:
            db.session.add(
                Favorite(corpus_id=self.id, user_id=user_id)
            )
        db.session.commit()

    def update_delimiter_token(self, delimiter_token: Optional[str] = None):
        """Update delimiter token.

        :param str delimiter_token: token
        """
        if delimiter_token != self.delimiter_token:
            try:
                self.delimiter_token = delimiter_token
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise PreferencesUpdateError(
                    f"cannot set delimiter token to '{delimiter_token}'"
                )

    def update_contexts(self, context_left: int, context_right: int):
        if context_left == self.context_left and context_right == self.context_right:
            return

        try:
            self.context_left = context_left
            self.context_right = context_right
            WordToken.update_batch_context(self.id, context_left, context_right)
        except Exception:
            db.session.rollback()
            raise PreferencesUpdateError(
                f"Cannot set context to 'left: {context_left}, right: {context_right}'"
            )

    def update_columns(self, columns):
        """Update columns.

        :param dict columns: column states (hidden or not hidden)
        """
        if columns.get("lemma") and columns.get("pos") and columns.get("morph"):
            raise PreferencesUpdateError(
                "You can't disable Lemma and POS and Morph. Keep at least one of them."
            )
        for column in self.columns:
            try:
                column.hidden = columns.get(column.heading.lower(), False)
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise PreferencesUpdateError(
                    f"cannot toggle hiding column '{column.heading}'"
                )

    def get_custom_dictionary(self, category: str, formatted: bool = False):
        """ Retrieve custom dictionary's values
        """
        values = CorpusCustomDictionary.query.filter(
            db.and_(
                CorpusCustomDictionary.corpus == self.id,
                CorpusCustomDictionary.category == category
            )
        ).all()
        if not formatted:
            return values

        if category == "lemma":
            return "\n".join([token.label for token in values])
        elif category == "POS":
            return ",".join([token.label for token in values])
        elif category == "morph":
            return "\n".join(["{}\t{}".format(token.label, token.secondary_label) for token in values])

    def custom_dictionaries_update(self, category: str, values: str, _commit: bool = True):
        splits = {"POS": ",", "lemma": "\n", "morph": "\n"}
        preproc = getattr(CorpusCustomDictionary, category+"_preproc")
        values = [
            preproc(x.strip(), self.id)
            for x in values.split(splits[category])
            if x.strip()
        ]
        CorpusCustomDictionary.query.filter(
            db.and_(
                CorpusCustomDictionary.corpus == self.id,
                CorpusCustomDictionary.category == category,
            )
        ).delete()
        if values:
            db.session.bulk_insert_mappings(
                CorpusCustomDictionary,
                values
            )
        if _commit:
            db.session.commit()
        return len(values)

    def has_custom_dictionary_value(self, category: str, string: str) -> bool:
        return CorpusCustomDictionary.query.filter(
            db.and_(
                CorpusCustomDictionary.corpus == self.id,
                CorpusCustomDictionary.category == category,
                CorpusCustomDictionary.label == string
            )
        ).count() >= 1

    def insert_custom_dictionary_value(self, category: str, string: str) -> bool:
        preproc = getattr(CorpusCustomDictionary, category+"_preproc")
        db.session.add(CorpusCustomDictionary(
            **preproc(string, self.id)
        ))
        db.session.commit()


class WordToken(db.Model):
    """ A word token is a word from a corpus with primary annotation

    :param id: ID of the word token
    :type id: int
    :param corpus: ID Of the corpus
    :type corpus: int
    :param order_id: Position identifier of the token in the corpus
    :type order_id: int
    :param form: Form, in the text, of the word token
    :type form: str
    :param lemma: Lemma assigned to the word token
    :type lemma: str
    :param POS: Part-Of-Speech tag assigned to the word token
    :type POS: str
    :param morph: Morphology label assigned to the word token
    :type morph: str
    :param context: Quotation of the text around this word
    :type context: str

    :cvar CONTEXT_LEFT: Number of word at the left of the current word to put in \
     context when adding WordToken in batch
    :cvar CONTEXT_RIGHT: Number of word at the right of the current word to put in \
     context when adding WordToken in batch

    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id', ondelete='CASCADE'))
    order_id = db.Column(db.Integer)  # Id in the corpus
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    label_uniform = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64))
    left_context = db.Column(db.String(512))
    right_context = db.Column(db.String(512))

    _changes = db.relationship("ChangeRecord", cascade="all,delete")

    CONTEXT_LEFT = 3
    CONTEXT_RIGHT = 3

    class ValidityError(ValueError):
        """ Error for values which are not allowed """
        def __init__(self, *args, **kwargs):
            self.statuses: Dict[str, bool] = {}
            self.msg: str = ""
            self.invalid_columns: List[str] = []
            super(WordToken.ValidityError, self).__init__()

    class NothingChangedError(ValueError):
        """ Error when an update is triggered and nothing is updated """
        statuses = {}
        msg = ""

    def to_dict(self):
        """ Export the current lemma to a dict (Most useful for jsonify)

        :return: Dict version of the lemma
        """
        return {
            "id": self.id,
            "corpus": self.corpus,
            "order_id": self.order_id,
            "form": self.form,
            "lemma": self.lemma,
            "POS": self.POS,
            "morph": self.morph,
            "context": self.context
        }

    def update_context_around(self, corpus, added=0, tokens=None, delete=None, _commit=True):
        """ Recomputes the context of tokens around the current token

        :param corpus: Corpus object to look for settings
        :param added: Number of token added
        :param tokens: Dictionary of tokens that should not be retrieved because they are updated
        :param _commit: Autocommit
        """

        token_count = corpus.tokens_count
        select_range = (
            # Start is the current order id minus the context
            # But we need this context twice because we will need also the tokens around it
            max(self.order_id - corpus.context_left * 2, 1),
            min(self.order_id + corpus.context_right * 2 + 1 + added, token_count)
        )
        edit_range = (
            # Start is the current order id minus the context
            # But we need this context twice because we will need also the tokens around it
            max(self.order_id - corpus.context_left, 1),
            min(self.order_id + corpus.context_right + 1 + added, token_count)
        )

        tokens = tokens or {}
        # Get the required tokens
        tokens.update({
            tok.order_id: tok
            for tok in WordToken.query.filter(
                db.and_(
                    WordToken.corpus == self.corpus,
                    WordToken.order_id.between(
                        *select_range
                    )
                )
            ).all()
            if not delete or tok.id != delete
        })

        for token_id in range(*edit_range):
            if token_id == self.order_id and added:
                pass
            tok = tokens[token_id]

            tok.left_context = " ".join([
                tokens[order_id].form for order_id in range(
                    max(token_id - corpus.context_left, 1),
                    token_id
                )
            ])

            tok.right_context = " ".join([
                tokens[order_id].form for order_id in range(
                    # We need max on both because editing the last one would make the range fail
                    min(token_count, token_id + 1),
                    min(token_count, corpus.context_right + token_id + 1)
                )
            ])
            db.session.add(tok)
        if _commit:
            db.session.commit()

    def edit_form(self, form, corpus, user):
        """ Edit the form of a token, recompute the context of neighbors, adds a recording

        :param form: New form
        :param corpus: Corpus object
        :param user: User editing the form
        """

        db.session.add(TokenHistory(
            corpus=corpus.id,
            new=form,
            old=self.form,
            action_type=TokenHistory.TYPES.Edition,
            user_id=user.id,
            word_token_id=self.id
        ))
        self.form = form
        db.session.add(self)

        self.update_context_around(corpus, tokens={
            self.order_id: self
        })

        db.session.commit()

    def add_form(self, form, corpus, user):
        """ Add a new token after the current one

        :param form: Form to record
        :param corpus: Corpus in which the token is
        :param user: User doing the correction
        """

        # Update the order ids
        WordToken.query.filter(db.and_(
            WordToken.corpus == corpus.id,
            WordToken.order_id > self.order_id
        )).update({WordToken.order_id: WordToken.order_id + 1})

        # Add the new token
        new_token = WordToken(
            corpus=corpus.id,
            form=form,
            order_id=self.order_id + 1
        )
        db.session.add(new_token)
        db.session.flush()

        # Record the change
        db.session.add(TokenHistory(
            corpus=corpus.id,
            new=form,
            action_type=TokenHistory.TYPES.Addition,
            user_id=user.id,
            word_token_id=new_token.id
        ))

        # Update the contexts
        self.update_context_around(corpus, added=2, tokens={
            self.order_id: self,
            self.order_id + 1: new_token
        })

        db.session.commit()

    def del_form(self, corpus, user):
        """ Add a new token after the current one

        :param form: Form to record
        :param corpus: Corpus in which the token is
        :param user: User doing the correction
        """
        # Remove
        db.session.delete(self)

        # Update the order ids
        WordToken.query.filter(db.and_(
            WordToken.corpus == corpus.id,
            WordToken.order_id > self.order_id
        )).update({WordToken.order_id: WordToken.order_id - 1})

        # Record the change
        db.session.add(TokenHistory(
            corpus=corpus.id,
            new="",
            old=self.form,
            action_type=TokenHistory.TYPES.Deletion,
            user_id=user.id,
            word_token_id=self.id
        ))

        # Update the contexts
        self.update_context_around(corpus, delete=self.id)

        db.session.commit()

    @property
    def tsv(self):
        """ Export the current token as a TSV line

        :return:  Current token as a TSV line (Order : form, lemma, POS, Morph)
        """
        return "\t".join([self.form, self.lemma, self.POS or "_", self.morph or "_"])

    @classmethod
    def similar_as(cls, corpus: Corpus, form: str, lemma: str, POS: str, morph: str):
        if corpus is None:
            return 0
        else:
            cnt = 0
            visible_columns = corpus.displayed_columns_by_name
            for w in corpus.word_token:
                if w.form == form:
                    if (
                        "lemma" in visible_columns and w.lemma == lemma
                    ) or (
                        "POS" in visible_columns and w.POS == POS
                    ) or (
                        "morph" in visible_columns and w.morph == morph
                    ) or visible_columns == ("similar",):
                        cnt += 1
            return cnt - 1

    @staticmethod
    def get_similar_for_batch(corpus: Corpus, tokens: Iterable["WordToken"]):
        forms = {token.form: [] for token in tokens}
        for token in tokens:
            token.similar = 0
            forms[token.form].append(token)

        for w in WordToken.query.filter(
                db.and_(WordToken.corpus == corpus.id, WordToken.form.in_(list(forms.keys())))
        ).all():
            if w.form in forms:
                for token in forms[w.form]:
                    if w.lemma == token.lemma or w.POS == token.POS or w.morph == token.morph:
                        token.similar += 1
        for token in tokens:
            token.similar = token.similar - 1 if token.similar > 0 else 0

    @staticmethod
    def get_like(filter_id, form, group_by, type_like="lemma", allowed_list=False):
        """ Get values starting with given form

        :param filter_id: Id of the corpus
        :type filter_id: int
        :param form: Plaintext string to search for
        :type form: str
        :param group_by: Group by the form used (Avoid duplicate values)
        :type group_by: bool
        :param type_like: Type of value to match on (lemma, POS, morph)
        :type type_like: str
        :param allowed_list: Retrieve possible values from Allowed[Type] tables
        :type allowed_list: bool
        :return: BaseQuery
        """
        normalised = unidecode.unidecode(form)
        split = False
        retrieve_fields = []
        if allowed_list is False:
            control_field = "corpus"  # Filter on corpus.id
            if type_like == "POS":
                cls = WordToken
                query_fields = [WordToken.POS]
                retrieve_fields = [WordToken.POS]
            elif type_like == "morph":
                cls = WordToken
                query_fields = [WordToken.morph]
                retrieve_fields = [WordToken.morph]
            else:
                cls = WordToken
                # If the normalisation is the same as the original form, we look in normalised label
                if normalised == form:
                    query_fields = [WordToken.label_uniform]
                # If there is accents however, we look into original accentued value
                else:
                    query_fields = [WordToken.lemma]
                retrieve_fields = [WordToken.lemma]
        else:
            control_field = "control_list"  # Filter on corpus.id
            if type_like == "POS":
                cls = AllowedPOS
                query_fields = [AllowedPOS.label]
                retrieve_fields = [AllowedPOS.label]
            elif type_like == "morph":
                cls = AllowedMorph
                split = True
                query_fields = [AllowedMorph.readable, AllowedMorph.label]
                retrieve_fields = [AllowedMorph.label, AllowedMorph.readable]
            else:
                cls = AllowedLemma
                if normalised == form:
                    query_fields = [AllowedLemma.label_uniform]
                # If there is accents however, we look into original accentued value
                else:
                    query_fields = [AllowedLemma.label]
                retrieve_fields = [AllowedLemma.label]

        query = cls.query.with_entities(*retrieve_fields)

        if form == "":
            query = query.filter(
                db.and_(
                    getattr(cls, control_field) == filter_id
                )
            )
        elif split:
            form = form.split()
            query = query.filter(
                db.and_(
                    getattr(cls, control_field) == filter_id,
                    # This or is applied on the different field : you can either have readable or label with a match
                    db.or_(*[
                        # But all the values that are given should match !
                        db.and_(*[
                            query_field.ilike("%{}%".format(fsplitted))
                            for fsplitted in form
                        ])
                        for query_field in query_fields
                    ])
                )
            )
        else:
            query = query.filter(
                db.and_(
                    getattr(cls, control_field) == filter_id,
                    *[
                        query_field.ilike("{}%".format(form))
                        for query_field in query_fields
                    ]
                )
            )
        if group_by is True:
            return query.group_by(retrieve_fields[0])
        return query

    @staticmethod
    def is_valid(lemma, POS, morph, corpus):
        """ Check if a token is valid for a given corpus

        :param lemma: Lemma value of the token to validate
        :type lemma: str
        :param POS: POS value of the token to validate
        :type POS: str
        :param morph: Morphology tag of the token to validate
        :type morph: str
        :param corpus: Corpus
        :type corpus: Corpus
        :return: Dictionary of status
        :rtype: dict
        """
        allowed_lemma, allowed_POS, allowed_morph = corpus.get_allowed_values("lemma"), \
                                                    corpus.get_allowed_values("POS"), \
                                                    corpus.get_allowed_values("morph")

        statuses = {
            "lemma": True,
            "POS": True,
            "morph": True
        }

        allowed_column = corpus.displayed_columns_by_name

        if lemma is not None \
                and "lemma" in allowed_column \
                and allowed_lemma.count() > 0 \
                and corpus.get_allowed_values("lemma", label=lemma).count() == 0:
            if not corpus.has_custom_dictionary_value("lemma", lemma):
                statuses["lemma"] = False

        if POS is not None \
                and "POS" in allowed_column \
                and allowed_POS.count() > 0 \
                and corpus.get_allowed_values("POS", label=POS).count() == 0:
            if not corpus.has_custom_dictionary_value("POS", POS):
                statuses["POS"] = False

        if morph is not None \
                and "morph" in allowed_column \
                and allowed_morph.count() > 0 \
                and corpus.get_allowed_values("morph", label=morph).count() == 0:
            if not corpus.has_custom_dictionary_value("morph", morph):
                statuses["morph"] = False
        return statuses

    @staticmethod
    def add_batch(corpus_id, word_tokens_dict, context_left=None, context_right=None):
        """ Add a batch of tokens to a corpus given a TSV

        :param corpus_id: Id of the corpus
        :type corpus_id: int
        :param word_tokens_dict: Generator made of dicts of tokens with form, lemma, POS and morph key
        :type word_tokens_dict: list of dict
        :param context_left: Length of the context to keep on the left
        :type context_left: int
        :param context_right: Length of the context to keep on the right
        :type context_right: int
        """
        if context_right:
            context_right = int(context_right)
        else:
            context_right = WordToken.CONTEXT_RIGHT

        if context_left:
            context_left = int(context_left)
        else:
            context_left = WordToken.CONTEXT_LEFT

        word_tokens_dict = list(word_tokens_dict)
        count_tokens = len(word_tokens_dict)
        tokens = []

        # stop right now if there's nothing to add
        if count_tokens == 0:
            return 0

        _keys = word_tokens_dict[0]
        form_key = "form" if "form" in _keys else "token" if "token" in _keys else "tokens"
        lemma_key = "lemma" if "lemma" in _keys else "lemmas"
        pos_key = "pos" if "pos" in _keys else "POS"
        morph_key = "morph"

        for i, token in enumerate(word_tokens_dict):

            if i == 0:
                previous_token = []
            elif i < context_left:
                previous_token = [tok.get(form_key) for tok in word_tokens_dict[:i]]
            else:
                previous_token = [tok.get(form_key) for tok in word_tokens_dict[i-context_left:i]]

            if i == count_tokens-1:
                next_token = []
            elif count_tokens-1-i < context_right:
                next_token = [tok.get(form_key) for tok in word_tokens_dict[i+1:]]
            else:
                next_token = [tok.get(form_key) for tok in word_tokens_dict[i+1:i+context_right+1]]

            form = token.get(form_key)
            if not form:
                error = MissingTokenColumnValue()
                error.line = i+1
                raise error
            lemma = token.get(lemma_key)
            label_uniform = ""
            if lemma:
                label_uniform = unidecode.unidecode(lemma)
            POS = token.get(pos_key, None)
            morph = token.get(morph_key, None)

            wt = dict(
                form=form,
                lemma=lemma,
                label_uniform=label_uniform,
                POS=POS,
                morph=morph,
                left_context=" ".join(previous_token),
                right_context=" ".join(next_token),
                corpus=corpus_id,
                order_id=i+1  # Asked by JB Camps...
            )
            for k in ("form",):
                validate_length(k, wt[k], {"form": 64})
            tokens.append(wt)

        db.session.bulk_insert_mappings(WordToken, tokens)
        return len(tokens)

    @staticmethod
    def update_batch_context(
            corpus_id: int,
            context_left: int,
            context_right: int,
            _commit: bool = True
    ):
        """
        Recomputes the context around each tokens of a given corpus.
        This method is called after changing corpus left and right context.
        :param corpus_id: identifier of the corpus
        :param context_left: left context length
        :param context_right: right context length
        :param _commit: Autocommit
        """
        tokens = WordToken.query.filter_by(
            corpus=corpus_id
        ).order_by(
            WordToken.order_id
        ).with_entities(
            WordToken.id, WordToken.order_id, WordToken.form
        ).all()
        token_count = len(tokens)

        updated_tokens = []
        for i, token in enumerate(tokens):
            left_context = " ".join([
                tokens[order_id].form for order_id in range(
                    max(i - context_left, 1), i
                )
            ])
            right_context = " ".join([
                tokens[order_id].form for order_id in range(
                    min(token_count, i + 1),
                    min(token_count, context_right + i + 1)
                )
            ])
            updated_tokens.append(
                dict(
                    id=token.id,
                    left_context=left_context,
                    right_context=right_context,
                )
            )

        db.session.bulk_update_mappings(WordToken, updated_tokens)

        if _commit:
            db.session.commit()

        return len(updated_tokens)

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: List of tokens from a query
        :type query: WordToken.query
        :return: String representation of the data
        """
        csv_file = io.StringIO()
        writer = csv.writer(csv_file, **TSV_CONFIG)
        writer.writerow(["token_id", "form", "lemma", "POS", "morph"])
        for token in query.order_by(WordToken.order_id).all():
            writer.writerow([token.id, token.form, token.lemma, token.POS or "_", token.morph or "_"])

        return csv_file.getvalue()

    @staticmethod
    def update(user_id, corpus_id, token_id, lemma=None, POS=None, morph=None):
        """ Update a given token with lemma, POS and morph value

        :param user_id: ID of the user who performs the update
        :type user_id: int
        :param corpus_id: Id of the corpus
        :type corpus_id: int
        :param token_id: Id of the token
        :type token_id: int
        :param lemma: Lemma
        :type lemma: str
        :param POS: PartOfSpeech
        :type POS: str
        :param morph: Morphology tag
        :type morph: str
        :return: Current token, Record Token
        :rtype: (WordToken, ChangeRecord)
        """
        user = User.query.filter_by(**{"id": user_id}).first_or_404()
        corpus = Corpus.query.filter_by(**{"id": corpus_id}).first_or_404()
        token = WordToken.query.filter_by(**{"id": token_id, "corpus": corpus_id}).first_or_404()
        # Strip if things are not None
        lemma = strip_or_none(lemma)
        POS = strip_or_none(POS)
        morph = strip_or_none(morph)

        # Avoid updating for the same
        if token.lemma == lemma and token.POS == POS and token.morph == morph:
            error = WordToken.NothingChangedError("No value where changed")
            error.msg = "No value where changed"
            raise error

        # Check if values are correct regarding allowed values
        validity = WordToken.is_valid(lemma=lemma, POS=POS, morph=morph, corpus=corpus)
        if False in list(validity.values()):
            error_msg = "Invalid value in {}".format(
                ", ".join([key for key in validity.keys() if validity[key] is False])
            )
            error = WordToken.ValidityError(error_msg)
            error.msg = error_msg
            error.statuses = validity
            error.invalid_columns = [key for key in validity.keys() if validity[key] is False]
            raise error

        # Updating
        if not lemma:
            lemma = token.lemma
        if not POS:
            POS = token.POS
        if not morph:
            morph = token.morph

        record = ChangeRecord.track(user, token, lemma, POS, morph)
        token.lemma = lemma
        token.label_uniform = unidecode.unidecode(lemma) if lemma else None
        token.POS = POS
        token.morph = morph
        db.session.add(token)
        db.session.commit()
        return token, record

    @property
    def context(self):
        """ Reformed version of former code for the context column"""
        return " ".join([
            tok
            for tok in [self.left_context, self.form, self.right_context]
            if tok
        ])

    @staticmethod
    def get_similar_to_record(change_record):
        """ Get tokens which shares similarity with ChangeRecord

        :param change_record: Change Record that we want to match against
        :type change_record: ChangeRecord
        :return: Word tokens
        :rtype: db.BaseQuery
        """
        changed = change_record.changed
        # if we have changed more than the lemma, but lemma was changed
        # We might want to include in the batch change corrected POS and/or Morph
        if "lemma" in changed and len(changed) > 0:
            lemma_match = db.or_(WordToken.lemma == change_record.lemma, WordToken.lemma == change_record.lemma_new)
        else:
            lemma_match = WordToken.lemma == change_record.lemma

        return db.session.query(WordToken).filter(
            db.and_(
                WordToken.corpus == change_record.corpus,
                WordToken.form == change_record.form,
                lemma_match,
                db.or_(
                    *[
                        getattr(WordToken, attr) == getattr(change_record, attr)
                        for attr in changed
                    ]
                )
            )
        )

    @staticmethod
    def get_nearly_similar_to(token, mode):
        """ Get tokens which shares similarity with ChangeRecord

        :param token: Token to find similar
        :type token: WordToken
        :param mode: Mode to use (partial, complete, lemma, POS, morph)
        :type mode: str
        :return: Word tokens
        :rtype: db.BaseQuery
        """
        filtering = None
        if mode not in ["partial", "complete", "lemma", "POS", "morph", "POS_ex", "lemma_ex", "morph_ex"]:
            raise BadRequest(description="Mode is not from the list partial, complete, "
                                         "lemma, POS, morph, lemma_ex, morph_ex, POS_ex")
        elif mode == "partial":
            filtering = (
                WordToken.form == token.form,
                db.or_(
                    WordToken.lemma == token.lemma,
                    WordToken.POS == token.POS,
                    WordToken.morph == token.morph,
                )
            )
        elif mode == "complete":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.lemma == token.lemma,
                    WordToken.POS == token.POS,
                    WordToken.morph == token.morph
                )
        elif mode == "lemma":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.lemma == token.lemma,
                )
        elif mode == "lemma_ex":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.lemma != token.lemma,
                )
        elif mode == "POS":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.POS == token.POS,
                )
        elif mode == "POS_ex":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.POS != token.POS,
                )
        elif mode == "morph":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.morph == token.morph,
                )
        elif mode == "morph_ex":
            filtering = (
                    WordToken.form == token.form,
                    WordToken.morph != token.morph,
                )
        return db.session.query(WordToken).filter(
                db.and_(
                    WordToken.corpus == token.corpus,
                    WordToken.id != token.id,
                    *filtering
                )
            )


class TokenHistory(db.Model):
    """ A change record keep track of tokens row edition, deletion and addition"""

    class TYPES(enum.Enum):
        Addition = 1
        Deletion = -1
        Edition = 0

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id', ondelete="CASCADE"))
    word_token_id = db.Column(db.Integer, db.ForeignKey('word_token.id'))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    action_type = db.Column(db.Enum(TYPES), nullable=False)
    new = db.Column(db.String(100), nullable=True)
    old = db.Column(db.String(100), nullable=True)
    created_on = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship(User, lazy='select')


class CorpusCustomDictionary(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'), nullable=False)
    label = db.Column(db.String(64), nullable=False)
    secondary_label = db.Column(db.String(64))
    category = db.Column(db.String(10), nullable=False)

    search_index = db.Index("ccd-search", "corpus", "label", "secondary_label", "category")
    retrieve_index = db.Index("ccd-retrieve", "corpus", "category")

    @staticmethod
    def lemma_preproc(string: str, corpus: int) -> Dict[str, str]:
        return {"label": string, "corpus": corpus, "secondary_label": unidecode.unidecode(string), "category": "lemma"}

    @staticmethod
    def morph_preproc(string: str, corpus: int) -> Dict[str, str]:
        if "\t" in string:
            morph, readable = string.split("\t")
        elif "    " in string:
            morph, readable = string.split("    ")
        else:
            morph, readable = string, ""
        return {"label": morph, "corpus": corpus, "secondary_label": readable, "category": "morph"}

    @staticmethod
    def POS_preproc(string: str, corpus: int) -> Dict[str, str]:
        return {"label": string, "corpus": corpus, "secondary_label": "", "category": "POS"}

    @staticmethod
    def get_like(corpus_id, form, group_by, category="lemma"):
        """ Get values starting with given form

        :param corpus_id: Id of the corpus
        :type corpus_id: int
        :param form: Plaintext string to search for
        :type form: str
        :param group_by: Group by the form used (Avoid duplicate values)
        :type group_by: bool
        :param category: Type of value to match on (lemma, POS, morph)
        :type category: str
        :return: BaseQuery
        """
        if category == "morph":
            query_fields = [CorpusCustomDictionary.label, CorpusCustomDictionary.secondary_label]
            retrieve_fields = [CorpusCustomDictionary.label, CorpusCustomDictionary.secondary_label]
        elif category == "POS":
            retrieve_fields = [CorpusCustomDictionary.secondary_label]
            query_fields = [CorpusCustomDictionary.label]
        else:
            retrieve_fields = [CorpusCustomDictionary.label]
            normalised = unidecode.unidecode(form)
            if normalised == form:
                query_fields = [CorpusCustomDictionary.secondary_label]

        query = CorpusCustomDictionary.query.with_entities(*retrieve_fields)
        query = query.filter(
            db.and_(
                CorpusCustomDictionary.category == category
            )
        )

        if form is None:
            query = query.filter(
                db.and_(
                    CorpusCustomDictionary.corpus == corpus_id
                )
            )
        else:
            if category == "morph":
                form = form.split()
                query = query.filter(
                    db.and_(
                        CorpusCustomDictionary.corpus == corpus_id,
                        # This or is applied on the different field : you can either have readable or label with a match
                        db.or_(*[
                            # But all the values that are given should match !
                            db.and_(*[
                                query_field.ilike("%{}%".format(fsplitted))
                                for fsplitted in form
                            ])
                            for query_field in query_fields
                        ])
                    )
                )
            else:
                query = query.filter(
                    db.and_(
                        CorpusCustomDictionary.corpus == corpus_id,
                        *[
                            query_field.ilike("{}%".format(form))
                            for query_field in query_fields
                        ]
                    )
                )
        if group_by is True:
            return query.group_by(retrieve_fields[0])

        return query


class ChangeRecord(db.Model):
    """ A change record keep track of lemma, POS or morph that have been changed for a particular form"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))
    word_token_id = db.Column(db.Integer, db.ForeignKey('word_token.id'))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64), nullable=True)
    lemma_new = db.Column(db.String(64))
    POS_new = db.Column(db.String(64))
    morph_new = db.Column(db.String(64))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    word_token = db.relationship('WordToken', lazy='select', viewonly=True)
    user = db.relationship(User, lazy='select', viewonly=True)

    @property
    def similar_remaining(self):
        """ Count similar token that look like the original form of the token recorded

        :return: Count similar token that look like the original form of the token recorded
        :rtype: int
        """
        return WordToken.get_similar_to_record(self).count()

    @staticmethod
    def track(user, token, lemma_new, POS_new, morph_new):
        """ Save the history of change for the token

        :param token: Token that has been updated
        :type token: WordToken
        :param lemma_new: New lemma assigned to the token
        :type lemma_new: str
        :param POS_new: New POS assigned to the token
        :type POS_new: str
        :param morph_new: New morphology assigned to the token
        :type morph_new: str
        :return: Change Record history item
        :rtype: ChangeRecord
        """
        tracked = ChangeRecord(
            user_id=user.id,
            corpus=token.corpus, word_token_id=token.id,
            form=token.form, lemma=token.lemma, POS=token.POS, morph=token.morph,
            lemma_new=lemma_new, POS_new=POS_new, morph_new=morph_new
        )
        db.session.add(tracked)
        return tracked

    @property
    def changed(self):
        """ Make a list of attributes names that were changed in the current record

        :return: List of attributes changed
        :rtype: [str]
        """
        return [
            attr
            for attr in ["lemma", "morph", "POS"]
            if getattr(self, attr) != getattr(self, attr+"_new")
        ]

    def apply_changes_to(self, user_id, token_ids):
        """ Apply the changes recorded by this instance to other tokens

        :param user_id: The ID of the user performing the change
        :type user_id: int
        :param token_ids: List of tokens ID to be updated
        :type token_ids: [str]
        :return: List of updated tokens
        """
        changed = []
        if not len(token_ids):
            return changed
        watch = {attr: (getattr(self, attr), getattr(self, attr+"_new")) for attr in self.changed}
        for token in db.session.query(WordToken).filter(
            db.and_(
                WordToken.id.in_(tuple([int(i) for i in token_ids])),
                WordToken.corpus == self.corpus
            )
        ).all():
            apply = {"user_id": user_id, "token_id": token.id, "corpus_id": token.corpus}
            apply.update({attr: val[1] for attr, val in watch.items() if val[0] == getattr(token, attr)})
            WordToken.update(**apply)
            changed.append(token)
        return changed


class Bookmark(db.Model):
    corpus_id = db.Column(db.Integer, db.ForeignKey("corpus.id", ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey(WordToken.id, ondelete="CASCADE"), primary_key=True)
    page = db.Column(db.Integer, nullable=False)

    @staticmethod
    def mark(corpus: int, user: int, token_id: int, page: int):
        bm = Bookmark(
            corpus_id=corpus,
            user_id=user,
            token_id=token_id,
            page=page
        )
        Bookmark.clear(corpus, user, _commit=False)
        db.session.add(bm)
        db.session.commit()
        return bm

    @staticmethod
    def clear(corpus: int, user: int, _commit: bool = False):
        bm = Bookmark.query.filter(db.and_(
            Bookmark.corpus_id == corpus,
            Bookmark.user_id == user
        )).first()
        if bm:
            db.session.delete(bm)
            if _commit:
                db.session.commit()


class Favorite(db.Model):
    corpus_id = db.Column(db.Integer, db.ForeignKey("corpus.id", ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), primary_key=True)

