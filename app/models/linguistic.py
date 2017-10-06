import unidecode

from .. import db
from ..utils.forms import strip_or_none


class Corpus(db.Model):
    """ A corpus is a set of tokens that is independent from others. This allows for multi-text management"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)

    def get_allowed_values(self, allowed_type="lemma", label=None):
        """ Make a query to retrieve

        :param allowed_type: A value from the set "lemma", "POS", "morph"
        :return: Flask SQL Alchemy Query
        :rtype: BaseQuery
        """
        if allowed_type == "lemma":
            cls = AllowedLemma
        elif allowed_type == "POS":
            cls = AllowedPOS
        elif allowed_type == "morph":
            cls = AllowedMorph
        else:
            raise ValueError("Get Allowed value had %s and it's not from the lemma, POS, morph set" % allowed_type)
        if label is not None:
            return db.session.query(cls).filter(
                db.and_(cls.corpus == self.id, cls.label == label)
            ).order_by(cls.label)
        return db.session.query(cls).filter(cls.corpus == self.id).order_by(cls.label)

    def get_unallowed(self, allowed_type="lemma"):
        """ Make a query to retrieve unallowed tokens by allowed_type

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
        :param limit: Hits per page
        :return: Pagination of records
        """
        return ChangeRecord.query.filter_by(corpus=self.id).order_by(ChangeRecord.created_on.desc()).paginate(page=page, per_page=limit)

    @staticmethod
    def create(name, word_tokens_dict, allowed_lemma=None, allowed_POS=None, allowed_morph=None):
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

        WordToken.add_batch(corpus_id=c.id, word_tokens_dict=word_tokens_dict)

        if allowed_lemma is not None and len(allowed_lemma) > 0:
            for item in allowed_lemma:
                current = AllowedLemma(label=item, corpus=c.id, label_uniform=unidecode.unidecode(item))
                db.session.add(current)

        if allowed_POS is not None and len(allowed_POS) > 0:
            for item in allowed_POS:
                current = AllowedPOS(label=item, corpus=c.id)
                db.session.add(current)

        if allowed_morph is not None and len(allowed_morph) > 0:
            for item in allowed_morph:
                current = AllowedMorph(
                    label=item.get("label"),
                    readable=item.get("readable", default=item["label"]),
                    corpus=c.id
                )
                db.session.add(current)

        db.session.commit()
        return c


class AllowedLemma(db.Model):
    """ An allowed lemma is a lemma that is accepted """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    label_uniform = db.Column(db.String(64))
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))


class AllowedPOS(db.Model):
    """ An allowed POS is a POS that is accepted """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))


class AllowedMorph(db.Model):
    """ An allowed POS is a POS that is accepted """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    readable = db.Column(db.String(256))
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))


class WordToken(db.Model):
    """ A word token is a word from a corpus with primary annotation"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))
    order_id = db.Column(db.Integer)  # Id in the corpus
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    label_uniform = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64))
    context = db.Column(db.String(512))

    CONTEXT_LEFT = 3
    CONTEXT_RIGHT = 3

    class ValidityError(ValueError):
        """ Error for values which are not allowed """
        statuses = {}
        msg = ""

    class NothingChangedError(ValueError):
        """ Error for values which are not allowed """
        statuses = {}
        msg = ""

    def to_dict(self):
        """ Export the current lemma to a dict

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
        return 0 < db.session.query(ChangeRecord).filter_by(**{"id": self.token, "corpus": self.corpus}).limit(1).count()

    @staticmethod
    def get_like(corpus_id, form, group_by, type_like="lemma", allowed_list=False):
        """ Get tokens starting with form

        :param corpus_id: Id of the corpus
        :param form: Form to filter with
        :param group_by: Group by the form used
        :param allowed_list: Get from the allowed list
        :return: BaseQuery
        """
        if allowed_list is False:
            if type_like == "POS":
                type_like = WordToken.POS
                retrieve_field = WordToken.POS
            else:
                type_like = WordToken.label_uniform
                retrieve_field = WordToken.lemma
        else:
            if type_like == "POS":
                type_like = AllowedPOS.label
                retrieve_field = AllowedPOS.label
            else:
                type_like = AllowedLemma.label_uniform
                retrieve_field = AllowedLemma.label

        query = db.session.query(retrieve_field)
        if form is None:
            query = query.filter(
            db.and_(
                WordToken.corpus == corpus_id
            )
        )
        else:
            query = query.filter(
            db.and_(
                WordToken.corpus == corpus_id,
                type_like.ilike("{}%".format(form))
            )
        )
        if group_by is True:
            return query.group_by(type_like)
        return query

    @staticmethod
    def is_valid(lemma, POS, morph, corpus):
        """ Check if a token is valid for a given corpus

        :param token: WordToken to check for validity
        :param corpus: Corpus
        :return: Dictionary of status
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
    def add_batch(corpus_id, word_tokens_dict):
        """ Add a batch of tokens to a corpus given a TSV

        :param corpus_id: Id of the corpus
        :param word_tokens_dict: Generator made of dicts of tokens with form, lemma, POS and morph key
        :return:
        """
        word_tokens_dict = list(word_tokens_dict)
        count_tokens = len(word_tokens_dict)
        for i, token in enumerate(word_tokens_dict):

            if i == 0:
                previous_token = []
            elif i < WordToken.CONTEXT_LEFT:
                previous_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[:i]]
            else:
                previous_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[i-WordToken.CONTEXT_LEFT:i]]

            if i == count_tokens-1:
                next_token = []
            elif count_tokens-1-i < WordToken.CONTEXT_RIGHT:
                next_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[i+1:]]
            else:
                next_token = [tok.get("form", tok.get("tokens")) for tok in word_tokens_dict[i+1:i+WordToken.CONTEXT_RIGHT+1]]

            wt = WordToken(
                form=token.get("form", token.get("tokens")),
                lemma=token.get("lemma", token.get("lemmas")),
                label_uniform=unidecode.unidecode(token.get("lemma", token.get("lemmas"))),
                POS=token.get("POS", token.get("pos")),
                morph=token.get("morph"),
                context=" ".join(previous_token + [token.get("form", token.get("tokens"))] + next_token),
                corpus=corpus_id,
                order_id=i
            )
            db.session.add(wt)
        db.session.commit()

    @staticmethod
    def update(corpus_id, token_id, lemma, POS, morph):
        """ Update a given token with lemma, POS and morph value

        :param corpus_id: Id of the corpus
        :param token_id: Id of the token
        :param lemma: Lemma
        :param POS: PartOfSpeech
        :param morph: Morphology tag
        :return: Current token, Record Token
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
        record = ChangeRecord.track(token, lemma, POS, morph)
        token.lemma = lemma
        token.label_uniform = unidecode.unidecode(lemma)
        token.POS = POS
        token.morph = morph
        db.session.add(token)
        db.session.commit()
        return token, record

    @staticmethod
    def get_similar_to(change_record):
        """ Get tokens which shares similarity with ChangeRecord

        :param change_record:
        :type change_record: ChangeRecord
        :return: Word tokens
        :rtype: db.BaseQuery
        """
        return db.session.query(WordToken).filter(
            db.and_(
                WordToken.corpus == change_record.corpus,
                db.or_(
                    db.and_(WordToken.form == change_record.form, WordToken.lemma == change_record.lemma,
                            change_record.lemma != change_record.lemma_new),
                    db.and_(WordToken.form == change_record.form, WordToken.POS == change_record.POS,
                            change_record.POS != change_record.POS_new, change_record.POS_new is not None),
                    db.and_(WordToken.form == change_record.form, WordToken.morph == change_record.morph,
                            change_record.morph != change_record.morph_new, change_record.morph_new is not None),
                )
            )
        )

    @staticmethod
    def get_nearly_similar_to(token):
        """ Get tokens which shares similarity with ChangeRecord

        :param token: Token to find similar
        :type token: WordToken
        :return: Word tokens
        :rtype: db.BaseQuery
        """
        return db.session.query(WordToken).filter(
            db.and_(
                WordToken.corpus == token.corpus,
                db.or_(
                    db.and_(WordToken.form == token.form, WordToken.lemma != token.lemma),
                    db.and_(WordToken.form == token.form, WordToken.POS != token.POS),
                    db.and_(WordToken.form == token.form, WordToken.morph != token.morph),
                )
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
    morph = db.Column(db.String(64))
    lemma_new = db.Column(db.String(64))
    POS_new = db.Column(db.String(64))
    morph_new = db.Column(db.String(64))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    word_token = db.relationship('WordToken', lazy='select')

    @property
    def similar_remaining(self):
        return WordToken.get_similar_to(self).count()

    @staticmethod
    def track(token, lemma_new, POS_new, morph_new):
        tracked = ChangeRecord(
            corpus=token.corpus, word_token_id=token.id,
            form=token.form, lemma=token.lemma, POS=token.POS, morph=token.morph,
            lemma_new=lemma_new, POS_new=POS_new, morph_new=morph_new
        )
        db.session.add(tracked)
        return tracked
