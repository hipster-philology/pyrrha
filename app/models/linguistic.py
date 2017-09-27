from .. import db


class Corpus(db.Model):
    """ A corpus is a set of tokens that is independent from others. This allows for multi-text management"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)

    @property
    def tokens_count(self):
        return WordToken.query.filter_by(corpus=self.id).count()

    def get_tokens(self, page=0, limit=100):
        return WordToken.query.filter_by(corpus=self.id).paginate(page=page, per_page=limit)

    def get_all_tokens(self):
        return WordToken.query.filter_by(corpus=self.id).order_by(WordToken.order_id).all()

    @staticmethod
    def create(name, word_tokens_dict):
        c = Corpus(name=name)
        db.session.add(c)
        db.session.commit()

        WordToken.add_batch(corpus_id=c.id, word_tokens_dict=word_tokens_dict)
        return c


class AllowedLemma(db.Model):
    """ An allowed lemma is a lemma that is accepted """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
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
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))


class WordToken(db.Model):
    """ A word token is a word from a corpus with primary annotation"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))
    order_id = db.Column(db.Integer)  # Id in the corpus
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64))
    context = db.Column(db.String(512))

    CONTEXT_LEFT = 3
    CONTEXT_RIGHT = 3

    def to_dict(self):
        return {
            "id": self.id,
            "corpus": self.corpus,
            "order_id": self.order_id,
            "form": self.form,
            "lemma": self.lemma,
            "POS": self.morph,
            "context": self.context
        }

    @property
    def tsv(self):
        return "\t".join([self.form, self.lemma, self.POS, self.morph])

    @staticmethod
    def add_batch(corpus_id, word_tokens_dict):
        """ Add a batch of tokens to a corpus given a TSV """
        word_tokens_dict = list(word_tokens_dict)
        count_tokens = len(word_tokens_dict)
        for i, token in enumerate(word_tokens_dict):

            if i == 0:
                previous_token = []
            elif i < WordToken.CONTEXT_LEFT:
                previous_token = [tok.get("form") for tok in word_tokens_dict[:i]]
            else:
                previous_token = [tok.get("form") for tok in word_tokens_dict[i-WordToken.CONTEXT_LEFT:i]]

            if i == count_tokens-1:
                next_token = []
            elif count_tokens-1-i < WordToken.CONTEXT_RIGHT:
                next_token = [tok.get("form") for tok in word_tokens_dict[i:]]
            else:
                next_token = [tok.get("form") for tok in word_tokens_dict[i+1:i+WordToken.CONTEXT_RIGHT]]

            wt = WordToken(
                form=token.get("form"),
                lemma=token.get("lemma"),
                POS=token.get("POS"),
                morph=token.get("morph"),
                context=" ".join(previous_token + [token.get("form")] + next_token),
                corpus=corpus_id,
                order_id=i
            )
            db.session.add(wt)
        db.session.commit()

    @staticmethod
    def update(corpus_id, token_id, lemma, POS, morph):
        token = WordToken.query.filter_by(**{"id": token_id, "corpus": corpus_id}).first_or_404()
        ChangeRecord.track(token)
        token.lemma = lemma
        token.POS = POS
        token.morph = morph
        db.session.add(token)
        db.session.commit()
        return token


class ChangeRecord(db.Model):
    """ A change record keep track of lemma, POS or morph that have been changed for a particular form"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))
    word_token = db.Column(db.Integer, db.ForeignKey('word_token.id'))
    form = db.Column(db.String(64))
    lemma = db.Column(db.String(64))
    POS = db.Column(db.String(64))
    morph = db.Column(db.String(64))
    created_on = db.Column(db.DateTime, server_default=db.func.now())

    @staticmethod
    def track(token):
        tracked = ChangeRecord(
            corpus=token.corpus, word_token=token.id,
            form=token.form, lemma=token.lemma, POS=token.POS, morph=token.morph
        )
        db.session.add(tracked)
        return tracked
