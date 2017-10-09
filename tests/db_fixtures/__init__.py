from .wauchier import WauchierAllowedPOS, WauchierAllowedLemma, WauchierTokens, Wauchier
from .floovant import FloovantTokens, FloovantAllowedPOS, FloovantAllowedLemma, Floovant
import copy
import time

DB_CORPORA = {
    "wauchier": {
        "corpus": Wauchier,
        "tokens": WauchierTokens,
        "lemma": WauchierAllowedLemma,
        "POS": WauchierAllowedPOS,
        "morph": []
    },
    "floovant": {
        "corpus": Floovant,
        "tokens": FloovantTokens,
        "lemma": FloovantAllowedLemma,
        "POS": FloovantAllowedPOS,
        "morph": []
    }
}


def add_corpus(
        corpus, db, with_token=True, tokens_up_to=None,
        with_allowed_lemma=False, partial_allowed_lemma=False,
        with_allowed_pos=False, partial_allowed_pos=False
):
    """ Add the Wauchier Corpus to fixtures

    :param corpus: Corpus to use
    :param db: Database object
    :param with_token: Add tokens as well
    :param with_allowed_lemma: Add allowed lemma to db
    :param partial_allowed_lemma: Restrict to first three allowed lemma (de saint martin)
    :param with_allowed_pos: Add allowed POS to db
    :param partial_allowed_pos: Restrict to first three allowed POS (ADJqua, NOMpro, CONcoo)
    """
    db.session.add(copy.deepcopy(DB_CORPORA[corpus]["corpus"]))
    db.session.commit()
    add = []
    if with_token is True:
        if tokens_up_to is not None:
            add += DB_CORPORA[corpus]["tokens"][:tokens_up_to]
        else:
            add += DB_CORPORA[corpus]["tokens"]

    if with_allowed_lemma is True:
        if partial_allowed_lemma:
            add += DB_CORPORA[corpus]["lemma"][:3]
        else:
            add += DB_CORPORA[corpus]["lemma"]

    if with_allowed_pos is True:
        if partial_allowed_pos:
            add += DB_CORPORA[corpus]["POS"][:3]
        else:
            add += DB_CORPORA[corpus]["POS"]
    for x in add:
        db.session.add(copy.deepcopy(x))
    db.session.commit()
    time.sleep(1)
