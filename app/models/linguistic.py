import csv
import io

import unidecode
from werkzeug.exceptions import BadRequest

from .. import db
from ..utils.forms import strip_or_none


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

    def get_allowed_values(self, allowed_type="lemma", label=None, order_by="label"):
        """ List values that are allowed (without label) or checks that given label is part
        of the existing corpus

        :param allowed_type: A value from the set "lemma", "POS", "morph"
        :param label: Value to match with as the POS, lemma or morph
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
                db.and_(cls.corpus == self.id, cls.label == label)
            ).order_by(order_by)
        return db.session.query(cls).filter(cls.corpus == self.id).order_by(order_by)

    def get_unallowed(self, allowed_type="lemma"):
        """ Search for WordToken that would not comply with Allowed Values (in AllowedLemma,
        AllowedPOS, AllowedMorph)

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

        allowed = db.session.query(cls.label).filter(cls.corpus == self.id)
        return db.session.query(WordToken).filter(
            db.and_(
                WordToken.corpus == self.id,
                prop.notin_(allowed)
            )
        ).order_by(WordToken.order_id)

    @property
    def tokens_count(self):
        """ Count the number of tokens

        :rtype: int
        """
        return WordToken.query.filter_by(corpus=self.id).count()

    def get_tokens(self):
        """ Retrieve WordTokens from the Corpus

        :return: Tokens Query
        """
        return WordToken.query.filter_by(corpus=self.id).order_by(WordToken.order_id)

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
            context_left=None, context_right=None
    ):
        """ Create a corpus

        :param name: Name of the corpus
        :param word_tokens_dict: Generator yielding a dictionaries of tokens
        :param allowed_lemma: List of allowed lemma
        :param allowed_POS: List of allowed POS
        :param allowed_morph: list of Allowed Morph in the form of dict with keys (label, readable)
        :return:
        """
        c = Corpus(name=name)
        db.session.add(c)
        db.session.commit()
        WordToken.add_batch(
            corpus_id=c.id, word_tokens_dict=word_tokens_dict,
            context_left=context_left, context_right=context_right
        )

        if allowed_lemma is not None and len(allowed_lemma) > 0:
            AllowedLemma.add_batch(allowed_lemma, c.id)

        if allowed_POS is not None and len(allowed_POS) > 0:
            AllowedPOS.add_batch(allowed_POS, c.id)

        if allowed_morph is not None and len(allowed_morph) > 0:
            AllowedMorph.add_batch(allowed_morph, c.id)
        db.session.commit()
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
        data = db.session.query(cls).filter_by(corpus=self.id).delete()
        cls.add_batch(allowed_values, self.id, _commit=True)
        return data


class AllowedLemma(db.Model):
    """ An allowed lemma is a lemma that is accepted

    :param id: ID of the Allowed Lemma (Optional)
    :param label: Allowed Lemma Value
    :param label_uniform: Normalized value of label, which allows for plaintext search
    :param corpus: ID of the corpus this AllowedLemma is related to
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    label_uniform = db.Column(db.String(64))
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))

    @staticmethod
    def add_batch(allowed_values, corpus_id, _commit=False):
        """ Add a batch of allowed values

        :param allowed_values: List of dictionary with label and readable keys
        :param corpus_id: Id of the corpus
        :param _commit: Force commit (Default: false)
        """
        for item in allowed_values:
            current = AllowedLemma(label=item, corpus=corpus_id, label_uniform=unidecode.unidecode(item))
            db.session.add(current)
        if _commit:
            db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: Query on AllowedLemma
        :type query: AllowedLemma.query
        :return: String representation of the data
        """
        return "\n".join(
            [
                allowed.label
                for allowed in query.order_by(AllowedLemma.id).all()
            ]
        )


class AllowedPOS(db.Model):
    """ An allowed POS is a POS that is accepted

    :param id: ID of the Allowed POS (Optional)
    :param label: Allowed POS Value
    :param corpus: ID of the corpus this AllowedPOS is related to
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))

    @staticmethod
    def add_batch(allowed_values, corpus_id, _commit=False):
        """ Add a batch of allowed values

        :param allowed_values: List of dictionary with label and readable keys
        :param corpus_id: Id of the corpus
        :param _commit: Force commit (Default: false)
        """
        for item in allowed_values:
            current = AllowedPOS(label=item, corpus=corpus_id)
            db.session.add(current)
        if _commit:
            db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: Query on AllowedPOS
        :type query: AllowedPOS.query
        :return: String representation of the data
        """
        return ",".join(
            [
                allowed.label
                for allowed in query.order_by(AllowedPOS.id).all()
            ]
        )


class AllowedMorph(db.Model):
    """ An allowed Morph is a Morph that is accepted

    :param id: ID of the Allowed Morph (Optional)
    :param label: Allowed Morph Value
    :param readable: Human Readable value of the label. *iei* v--1s-pi becomes Verb, 1st Singular Present Indicative
    :param corpus: ID of the corpus this AllowedMorph is related to
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    readable = db.Column(db.String(256))
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))

    @staticmethod
    def add_batch(allowed_values, corpus_id, _commit=False):
        """ Add a batch of allowed values

        :param allowed_values: List of dictionary with label and readable keys
        :param corpus_id: Id of the corpus
        :param _commit: Force commit (Default: false)
        """
        for item in allowed_values:
            current = AllowedMorph(
                label=item.get("label"),
                readable=item.get("readable", item["label"]),
                corpus=corpus_id
            )
            db.session.add(current)
        if _commit:
            db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: Query on AllowedMorph
        :type query: AllowedMorph.query
        :return: String representation of the data
        """
        csv_file = io.StringIO()
        writer = csv.writer(csv_file, dialect="excel-tab")
        writer.writerow(["label", "readable"])
        for morph in query.order_by(AllowedMorph.id).all():
            writer.writerow([morph.label, morph.readable])

        return csv_file.getvalue()


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
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))
    order_id = db.Column(db.Integer)  # Id in the corpus
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    label_uniform = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64))
    left_context = db.Column(db.String(512))
    right_context = db.Column(db.String(512))

    CONTEXT_LEFT = 3
    CONTEXT_RIGHT = 3

    class ValidityError(ValueError):
        """ Error for values which are not allowed """
        statuses = {}
        msg = ""

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

    @property
    def tsv(self):
        """ Export the current token as a TSV line

        :return:  Current token as a TSV line (Order : form, lemma, POS, Morph)
        """
        return "\t".join([self.form, self.lemma, self.POS or "_", self.morph or "_"])

    @property
    def changed(self):
        """ Tells whether this token has already been edited

        :return: If the token has been edited
        :rtype: bool
        """
        return 0 < db.session.query(ChangeRecord).filter_by(**{"word_token_id": self.id, "corpus": self.corpus}).limit(1).count()

    @property
    def similar(self):
        """ Number of partial match this token has

        :return: Number of partial match this token has
        :rtype: int
        """
        return WordToken.get_nearly_similar_to(self, mode="partial").count()

    @staticmethod
    def get_like(corpus_id, form, group_by, type_like="lemma", allowed_list=False):
        """ Get values starting with given form

        :param corpus_id: Id of the corpus
        :type corpus_id: int
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

        if form is None:
            query = query.filter(
                db.and_(
                    cls.corpus == corpus_id
                )
            )
        elif split:
            form = form.split()
            query = query.filter(
                db.and_(
                    cls.corpus == corpus_id,
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
                    cls.corpus == corpus_id,
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
        if lemma is not None \
                and allowed_lemma.count() > 0 \
                and corpus.get_allowed_values("lemma", label=lemma).count() == 0:
            statuses["lemma"] = False

        if POS is not None \
                and allowed_POS.count() > 0 \
                and corpus.get_allowed_values("POS", label=POS).count() == 0:
            statuses["POS"] = False

        if morph is not None and allowed_morph.count() > 0 and \
                        corpus.get_allowed_values("morph", label=morph).count() == 0:
            statuses["morph"] = False
        return statuses

    @staticmethod
    def add_batch(corpus_id, word_tokens_dict, context_left=None, context_right=None):
        """ Add a batch of tokens to a corpus given a TSV

        :param corpus_id: Id of the corpus
        :type corpus_id: int
        :param word_tokens_dict: Generator made of dicts of tokens with form, lemma, POS and morph key
        :type word_tokens_dict: list of dict
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
        for i, token in enumerate(word_tokens_dict):

            if i == 0:
                previous_token = []
            elif i < context_left:
                previous_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[:i]]
            else:
                previous_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[i-context_left:i]]

            if i == count_tokens-1:
                next_token = []
            elif count_tokens-1-i < context_right:
                next_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[i+1:]]
            else:
                next_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[i+1:i+context_right+1]]

            wt = WordToken(
                form=token.get("form", token.get("tokens")),
                lemma=token.get("lemma", token.get("lemmas")),
                label_uniform=unidecode.unidecode(token.get("lemma", token.get("lemmas"))),
                POS=token.get("POS", token.get("pos")),
                morph=token.get("morph", None),
                #context=" ".join(previous_token + [token.get("form")] + next_token),
                left_context=" ".join(previous_token),
                right_context=" ".join(next_token),
                corpus=corpus_id,
                order_id=i
            )
            db.session.add(wt)
        db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: List of tokens from a query
        :type query: WordToken.query
        :return: String representation of the data
        """
        csv_file = io.StringIO()
        writer = csv.writer(csv_file, dialect="excel-tab")
        writer.writerow(["token_id", "form", "lemma", "POS", "morph"])
        for token in query.order_by(WordToken.order_id).all():
            writer.writerow([token.id, token.form, token.lemma, token.POS or "_", token.morph or "_"])

        return csv_file.getvalue()

    @staticmethod
    def update(corpus_id, token_id, lemma=None, POS=None, morph=None):
        """ Update a given token with lemma, POS and morph value

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
            raise error

        # Updating
        if not lemma:
            lemma = token.lemma
        if not POS:
            POS = token.POS
        if not morph:
            morph = token.morph

        record = ChangeRecord.track(token, lemma, POS, morph)

        token.lemma = lemma
        token.label_uniform = unidecode.unidecode(lemma)
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
            filtering = db.or_(
                    db.and_(WordToken.form == token.form, WordToken.lemma == token.lemma),
                    db.and_(WordToken.form == token.form, WordToken.POS == token.POS),
                    db.and_(WordToken.form == token.form, WordToken.morph == token.morph),
                )
        elif mode == "complete":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.lemma == token.lemma,
                    WordToken.POS == token.POS,
                    WordToken.morph == token.morph
                )
        elif mode == "lemma":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.lemma == token.lemma,
                )
        elif mode == "lemma_ex":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.lemma != token.lemma,
                )
        elif mode == "POS":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.POS == token.POS,
                )
        elif mode == "POS_ex":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.POS != token.POS,
                )
        elif mode == "morph":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.morph == token.morph,
                )
        elif mode == "morph_ex":
            filtering = db.and_(
                    WordToken.form == token.form,
                    WordToken.morph != token.morph,
                )
        return db.session.query(WordToken).filter(
                db.and_(
                    WordToken.corpus == token.corpus,
                    WordToken.id != token.id,
                    filtering
                )
            )


class ChangeRecord(db.Model):
    """ A change record keep track of lemma, POS or morph that have been changed for a particular form"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))
    word_token_id = db.Column(db.Integer, db.ForeignKey('word_token.id'))
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64), nullable=True)
    lemma_new = db.Column(db.String(64))
    POS_new = db.Column(db.String(64))
    morph_new = db.Column(db.String(64))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    word_token = db.relationship('WordToken', lazy='select')

    @property
    def similar_remaining(self):
        """ Count similar token that look like the original form of the token recorded

        :return: Count similar token that look like the original form of the token recorded
        :rtype: int
        """
        return WordToken.get_similar_to_record(self).count()

    @staticmethod
    def track(token, lemma_new, POS_new, morph_new):
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

    def apply_changes_to(self, token_ids):
        """ Apply the changes recorded by this instance to other tokens

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
            apply = {"token_id": token.id, "corpus_id": token.corpus}
            apply.update({attr: val[1] for attr, val in watch.items() if val[0] == getattr(token, attr)})
            WordToken.update(**apply)
            changed.append(token)
        return changed
