from .wauchier import WauchierAllowedPOS, WauchierAllowedLemma, WauchierTokens, Wauchier, WauchierAllowedMorph, WCL
from .floovant import FloovantTokens, FloovantAllowedPOS, FloovantAllowedLemma, Floovant, FloovantAllowedMorph, FCL
import copy
import unidecode


DB_CORPORA = {
    "wauchier": {
        "corpus": Wauchier,
        "tokens": WauchierTokens,
        "lemma": WauchierAllowedLemma,
        "POS": WauchierAllowedPOS,
        "morph": WauchierAllowedMorph,
        "control_list": WCL
    },
    "floovant": {
        "corpus": Floovant,
        "tokens": FloovantTokens,
        "lemma": FloovantAllowedLemma,
        "POS": FloovantAllowedPOS,
        "morph": FloovantAllowedMorph,
        "control_list": FCL
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
    db.session.flush()
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
    db.session.add(corpus_object)
    db.session.flush()
    if with_token is True:
        if tokens_up_to is not None:
            add = DB_CORPORA[corpus]["tokens"][:tokens_up_to]
        else:
            add = DB_CORPORA[corpus]["tokens"]
        db.session.bulk_save_objects(add)
    db.session.commit()
    return corpus_object
