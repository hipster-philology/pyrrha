from app.models import Corpus, WordToken, AllowedLemma, AllowedPOS
import time
import copy

Wauchier = Corpus(name="Wauchier", id=1)

WauchierTokens = [
    WordToken(corpus=Wauchier.id, form="De", lemma="de", label_uniform="de", POS="PRE"),
    WordToken(corpus=Wauchier.id, form="seint", lemma="saint", label_uniform="saint", POS="ADJqua"),
    WordToken(corpus=Wauchier.id, form="Martin", lemma="martin", label_uniform="martin", POS="NOMpro"),
    WordToken(corpus=Wauchier.id, form="mout", lemma="mout", label_uniform="mout", POS="ADVgen"),
    WordToken(corpus=Wauchier.id, form="doit", lemma="devoir", label_uniform="devoir", POS="VERcjg"),
    WordToken(corpus=Wauchier.id, form="on", lemma="un", label_uniform="un", POS="PRE"),
    WordToken(corpus=Wauchier.id, form="doucement", lemma="doucement", label_uniform="doucement", POS="ADVgen"),
    WordToken(corpus=Wauchier.id, form="et", lemma="et", label_uniform="et", POS="CONcoo"),
    WordToken(corpus=Wauchier.id, form="volentiers", lemma="volentiers", label_uniform="volentiers", POS="ADVgen"),
    WordToken(corpus=Wauchier.id, form="le", lemma="le", label_uniform="le", POS="DETdef"),
    WordToken(corpus=Wauchier.id, form="bien", lemma="bien", label_uniform="bien", POS="ADVgen"),
    WordToken(corpus=Wauchier.id, form="oïr", lemma="öir", label_uniform="öir", POS="VERinf"),
    WordToken(corpus=Wauchier.id, form="et", lemma="et", label_uniform="et", POS="CONcoo"),
    WordToken(corpus=Wauchier.id, form="entendre", lemma="entendre", label_uniform="entendre", POS="VERinf"),
    WordToken(corpus=Wauchier.id, form=",", lemma=",", label_uniform=",", POS="PONfbl"),
    WordToken(corpus=Wauchier.id, form="car", lemma="car", label_uniform="car", POS="CONcoo"),
    WordToken(corpus=Wauchier.id, form="par", lemma="par", label_uniform="par", POS="PRE"),
    WordToken(corpus=Wauchier.id, form="le", lemma="le", label_uniform="le", POS="DETdef"),
    WordToken(corpus=Wauchier.id, form="bien", lemma="bien", label_uniform="bien", POS="ADVgen"),
    WordToken(corpus=Wauchier.id, form="savoir", lemma="savoir", label_uniform="savoir", POS="VERinf"),
    WordToken(corpus=Wauchier.id, form="et", lemma="et", label_uniform="et", POS="CONcoo"),
    WordToken(corpus=Wauchier.id, form="retenir", lemma="retenir", label_uniform="retenir", POS="VERinf"),
    WordToken(corpus=Wauchier.id, form="puet", lemma="pöoir", label_uniform="pöoir", POS="VERcjg"),
    WordToken(corpus=Wauchier.id, form="l", lemma="il", label_uniform="il", POS="PROper"),
    WordToken(corpus=Wauchier.id, form="en", lemma="en1", label_uniform="en1", POS="PRE")
]

WauchierAllowedLemma = [
    AllowedLemma(label="de", label_uniform="de", corpus=Wauchier.id),
    AllowedLemma(label="saint", label_uniform="saint", corpus=Wauchier.id),
    AllowedLemma(label="martin", label_uniform="martin", corpus=Wauchier.id),
    AllowedLemma(label="öir", label_uniform="öir", corpus=Wauchier.id),
    AllowedLemma(label="car", label_uniform="car", corpus=Wauchier.id),
    AllowedLemma(label="devoir", label_uniform="devoir", corpus=Wauchier.id),
    AllowedLemma(label="entendre", label_uniform="entendre", corpus=Wauchier.id),
    AllowedLemma(label=",", label_uniform=",", corpus=Wauchier.id),
    AllowedLemma(label="par", label_uniform="par", corpus=Wauchier.id),
    AllowedLemma(label="un", label_uniform="un", corpus=Wauchier.id),
    AllowedLemma(label="pöoir", label_uniform="pöoir", corpus=Wauchier.id),
    AllowedLemma(label="il", label_uniform="il", corpus=Wauchier.id),
    AllowedLemma(label="doucement", label_uniform="doucement", corpus=Wauchier.id),
    AllowedLemma(label="en1", label_uniform="en1", corpus=Wauchier.id),
    AllowedLemma(label="le", label_uniform="le", corpus=Wauchier.id),
    AllowedLemma(label="mout", label_uniform="mout", corpus=Wauchier.id),
    AllowedLemma(label="bien", label_uniform="bien", corpus=Wauchier.id),
    AllowedLemma(label="retenir", label_uniform="retenir", corpus=Wauchier.id),
    AllowedLemma(label="volentiers", label_uniform="volentiers", corpus=Wauchier.id),
    AllowedLemma(label="et", label_uniform="et", corpus=Wauchier.id),
    AllowedLemma(label="savoir", label_uniform="savoir", corpus=Wauchier.id)
]

WauchierAllowedPOS = [
    AllowedPOS(label='ADJqua', corpus=Wauchier.id),
    AllowedPOS(label='NOMpro', corpus=Wauchier.id),
    AllowedPOS(label='CONcoo', corpus=Wauchier.id),
    AllowedPOS(label='DETdef', corpus=Wauchier.id),
    AllowedPOS(label='PROper', corpus=Wauchier.id),
    AllowedPOS(label='ADVgen', corpus=Wauchier.id),
    AllowedPOS(label='PONfbl', corpus=Wauchier.id),
    AllowedPOS(label='VERcjg', corpus=Wauchier.id),
    AllowedPOS(label='PRE', corpus=Wauchier.id),
    AllowedPOS(label='VERinf', corpus=Wauchier.id)
]


def add_wauchier(
        db, with_token=True,
        with_allowed_lemma=False, partial_allowed_lemma=False,
        with_allowed_pos=False, partial_allowed_pos=False
):
    """ Add the Wauchier Corpus to fixtures

    :param with_token: Add tokens as well
    :param with_allowed_lemma: Add allowed lemma to db
    :param partial_allowed_lemma: Restrict to first three allowed lemma (de saint martin)
    :param with_allowed_pos: Add allowed POS to db
    :param partial_allowed_pos: Restrict to first three allowed POS (ADJqua, NOMpro, CONcoo)
    """
    db.session.add(copy.deepcopy(Wauchier))
    db.session.commit()
    add = []
    if with_token is True:
        add += WauchierTokens

    if with_allowed_lemma is True:
        if partial_allowed_lemma:
            add += WauchierAllowedLemma[:3]
        else:
            add += WauchierAllowedLemma

    if with_allowed_pos is True:
        if partial_allowed_pos:
            add += WauchierAllowedPOS[:3]
        else:
            add += WauchierAllowedPOS
    for x in add:
        db.session.add(copy.deepcopy(x))
    db.session.commit()
    time.sleep(1)
