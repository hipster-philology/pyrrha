from .wauchier import WauchierAllowedPOS, WauchierAllowedLemma, WauchierTokens, Wauchier, WauchierAllowedMorph, WCL, WauchierColumns
from .floovant import FloovantTokens, FloovantAllowedPOS, FloovantAllowedLemma, Floovant, FloovantAllowedMorph, FCL, FloovantColumns
from . import priapees
import copy
import unidecode
from app.models.corpus import WordToken


DB_CORPORA = {
    "wauchier": {
        "corpus": Wauchier,
        "tokens": WauchierTokens,
        "lemma": WauchierAllowedLemma,
        "POS": WauchierAllowedPOS,
        "morph": WauchierAllowedMorph,
        "control_list": WCL,
        "columns": WauchierColumns
    },
    "floovant": {
        "corpus": Floovant,
        "tokens": FloovantTokens,
        "lemma": FloovantAllowedLemma,
        "POS": FloovantAllowedPOS,
        "morph": FloovantAllowedMorph,
        "control_list": FCL,
        "columns": FloovantColumns
    },
    "priapees": {
        "corpus": priapees.corpus,
        "tokens": priapees.tokens,
        "lemma": [],
        "POS": [],
        "morph": [],
        "control_list": priapees.control_list,
        "columns": priapees.PriapeeColumns
    }
}


def add_control_lists(
        corpus, db,
        with_allowed_lemma=True, partial_allowed_lemma=True,
        with_allowed_pos=True, partial_allowed_pos=True,
        with_allowed_morph=True, partial_allowed_morph=True,
        **nobodycares
):
    """ Add the Wauchier Corpus to fixtures

    :param corpus: Corpus to use
    :param db: Database object
    :param with_allowed_lemma: Add allowed lemma to db
    :param partial_allowed_lemma: Restrict to first three allowed lemma (de saint martin)
    :param with_allowed_pos: Add allowed POS to db
    :param partial_allowed_pos: Restrict to first three allowed POS (ADJqua, NOMpro, CONcoo)
    :param with_allowed_morph: Add allowed Morph to db
    :param partial_allowed_morph: Restrict to first few Morphs
    """
    cl = copy.deepcopy(DB_CORPORA[corpus]["control_list"])
    db.session.add(cl)
    db.session.commit()
    add = []

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

    if with_allowed_morph is True:
        if partial_allowed_morph:
            add += DB_CORPORA[corpus]["morph"][:3]
        else:
            add += DB_CORPORA[corpus]["morph"]
    for x in add:
        z = copy.deepcopy(x)
        if hasattr(z, "label_uniform"):
            z.label_uniform = unidecode.unidecode(z.label_uniform)
        db.session.add(z)
    db.session.commit()
    return cl


def add_corpus(
        corpus, db, with_token=True, tokens_up_to=None,
        with_allowed_lemma=False, partial_allowed_lemma=False,
        with_allowed_pos=False, partial_allowed_pos=False,
        with_allowed_morph=False, partial_allowed_morph=False,
        with_delimiter=False, with_columns=True,
        **nobodycares
):
    """ Add the Wauchier Corpus to fixtures

    :param corpus: Corpus to use
    :param db: Database object
    :param with_token: Add tokens as well
    :param with_allowed_lemma: Add allowed lemma to db
    :param partial_allowed_lemma: Restrict to first three allowed lemma (de saint martin)
    :param with_allowed_pos: Add allowed POS to db
    :param partial_allowed_pos: Restrict to first three allowed POS (ADJqua, NOMpro, CONcoo)
    :param with_allowed_morph: Add allowed Morph to db
    :param partial_allowed_morph: Restrict to first few Morphs
    :param with_delimiter: Add delimiters to the corpus
    """
    add_control_lists(
        corpus, db,
        with_allowed_lemma=with_allowed_lemma,
        partial_allowed_lemma=partial_allowed_lemma,
        with_allowed_pos=with_allowed_pos,
        partial_allowed_pos=partial_allowed_pos,
        with_allowed_morph=with_allowed_morph,
        partial_allowed_morph=partial_allowed_morph
    )
    corpus_object = copy.deepcopy(DB_CORPORA[corpus]["corpus"])
    DELIMITER = "____"

    if with_delimiter:
        corpus_object.delimiter_token = DELIMITER

    db.session.add(corpus_object)
    db.session.flush()
    if with_columns is True:
        for col in copy.deepcopy(DB_CORPORA[corpus]["columns"]):
            db.session.add(col)
    if with_token is True:
        if tokens_up_to is not None:
            add = DB_CORPORA[corpus]["tokens"][:tokens_up_to]
        else:
            add = DB_CORPORA[corpus]["tokens"]
        index = 0
        for real_index, x in enumerate(add):
            if with_delimiter and real_index > 0 and real_index % 2 == 0:
                db.session.add(WordToken(corpus=corpus_object.id, form=DELIMITER, order_id=index))
                index += 1

            z = copy.deepcopy(x)
            if with_delimiter:
                z.order_id = index + 1  # Because base 1 !
            else:
                z.order_id = real_index + 1  # Because base 1 !
            if hasattr(z, "label_uniform"):
                z.label_uniform = unidecode.unidecode(z.label_uniform)
            db.session.add(z)
            index += 1

    db.session.commit()
    return corpus_object
