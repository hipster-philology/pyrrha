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


Floovant = Corpus(name="Floovant", id=2)
FloovantTokens = [
    WordToken(corpus=Floovant.id, form="SOIGNORS", lemma="seignor", context="SOIGNORS or escoutez que", label_uniform="seignor", morph="|||p|m|n|"),
    WordToken(corpus=Floovant.id, form="or", lemma="or4", context="SOIGNORS or escoutez que Dés", label_uniform="or4", morph="||||||-"),
    WordToken(corpus=Floovant.id, form="escoutez", lemma="escouter", context="SOIGNORS or escoutez que Dés vos", label_uniform="escouter", morph="imp||2|p|||"),
    WordToken(corpus=Floovant.id, form="que", lemma="que4", context="SOIGNORS or escoutez que Dés vos soit", label_uniform="que4", morph="||||||"),
    WordToken(corpus=Floovant.id, form="Dés", lemma="dieu", context="or escoutez que Dés vos soit amis", label_uniform="dieu", morph="|||s|m|n|"),
    WordToken(corpus=Floovant.id, form="vos", lemma="vos1", context="escoutez que Dés vos soit amis III", label_uniform="vos1", morph="||2|p|m|r|"),
    WordToken(corpus=Floovant.id, form="soit", lemma="estre1", context="que Dés vos soit amis III vers", label_uniform="estre1", morph="sub|pst|3|s|||"),
    WordToken(corpus=Floovant.id, form="amis", lemma="ami", context="Dés vos soit amis III vers de", label_uniform="ami", morph="|||s|m|n|"),
    WordToken(corpus=Floovant.id, form="III", lemma="trois1", context="vos soit amis III vers de bone", label_uniform="trois1", morph="|||p|m|r|"),
    WordToken(corpus=Floovant.id, form="vers", lemma="vers1", context="soit amis III vers de bone estoire", label_uniform="vers1", morph="|||p|m|r|"),
    WordToken(corpus=Floovant.id, form="de", lemma="de", context="amis III vers de bone estoire se", label_uniform="de", morph="||||||"),
    WordToken(corpus=Floovant.id, form="bone", lemma="bon", context="III vers de bone estoire se je", label_uniform="bon", morph="|||s|f|r|p"),
    WordToken(corpus=Floovant.id, form="estoire", lemma="estoire1", context="vers de bone estoire se je les", label_uniform="estoire1", morph="|||s|f|r|"),
    WordToken(corpus=Floovant.id, form="se", lemma="si", context="de bone estoire se je les vos", label_uniform="si", morph="||||||-"),
    WordToken(corpus=Floovant.id, form="je", lemma="je", context="bone estoire se je les vos devis", label_uniform="je", morph="||1|s|m|n|"),
    WordToken(corpus=Floovant.id, form="les", lemma="il", context="estoire se je les vos devis Dou", label_uniform="il", morph="||3|p|m|r|"),
    WordToken(corpus=Floovant.id, form="vos", lemma="vos1", context="se je les vos devis Dou premier", label_uniform="vos1", morph="||2|p|m|r|"),
    WordToken(corpus=Floovant.id, form="devis", lemma="deviser", context="je les vos devis Dou premier roi", label_uniform="deviser", morph="ind|pst|1|s|||"),
    WordToken(corpus=Floovant.id, form="Dou", lemma="de+le", context="les vos devis Dou premier roi de", label_uniform="de+le", morph="|||s|m|r|"),
    WordToken(corpus=Floovant.id, form="premier", lemma="premier", context="vos devis Dou premier roi de France", label_uniform="premier", morph="|||s|m|r|"),
    WordToken(corpus=Floovant.id, form="roi", lemma="roi2", context="devis Dou premier roi de France qui", label_uniform="roi2", morph="|||s|m|r|"),
    WordToken(corpus=Floovant.id, form="de", lemma="de", context="Dou premier roi de France qui crestïens", label_uniform="de", morph="||||||"),
    WordToken(corpus=Floovant.id, form="France", lemma="france", context="premier roi de France qui crestïens devint", label_uniform="france", morph="|||s|f|r|"),
    WordToken(corpus=Floovant.id, form="qui", lemma="qui", context="roi de France qui crestïens devint Cil", label_uniform="qui", morph="|||s|m|n|"),
    WordToken(corpus=Floovant.id, form="crestïens", lemma="crestiien", context="de France qui crestïens devint Cil ot", label_uniform="crestiien", morph="|||s|m|n|"),
    WordToken(corpus=Floovant.id, form="devint", lemma="devenir", context="France qui crestïens devint Cil ot non", label_uniform="devenir", morph="ind|psp|3|s|||"),
    WordToken(corpus=Floovant.id, form="Cil", lemma="cel", context="qui crestïens devint Cil ot non Cloovis", label_uniform="cel", morph="|||s|m|n|"),
    WordToken(corpus=Floovant.id, form="ot", lemma="avoir", context="crestïens devint Cil ot non Cloovis si", label_uniform="avoir", morph="ind|psp|3|s|||"),
    WordToken(corpus=Floovant.id, form="non", lemma="nom", context="devint Cil ot non Cloovis si com", label_uniform="nom", morph="|||s|m|r|"),
    WordToken(corpus=Floovant.id, form="Cloovis", lemma="clovis", context="Cil ot non Cloovis si com truis", label_uniform="clovis", morph="|||s|m|r|"),
    WordToken(corpus=Floovant.id, form="si", lemma="si", context="ot non Cloovis si com truis en", label_uniform="si", morph="||||||-"),
    WordToken(corpus=Floovant.id, form="com", lemma="come1", context="non Cloovis si com truis en escrit", label_uniform="come1", morph="||||||"),
    WordToken(corpus=Floovant.id, form="truis", lemma="trover", context="Cloovis si com truis en escrit", label_uniform="trover", morph="ind|pst|1|s|||"),
    WordToken(corpus=Floovant.id, form="en", lemma="en1", context="si com truis en escrit", label_uniform="en1", morph="||||||"),
    WordToken(corpus=Floovant.id, form="escrit", lemma="escrit", context="com truis en escrit", label_uniform="escrit", morph="|||s|m|r|")
]
FloovantAllowedPOS = [
    AllowedPOS(corpus=Floovant.id, label="ADVgen"),
    AllowedPOS(corpus=Floovant.id, label="VERcjg"),
    AllowedPOS(corpus=Floovant.id, label="NOMcom"),
    AllowedPOS(corpus=Floovant.id, label="ADJord"),
    AllowedPOS(corpus=Floovant.id, label="ADJqua"),
    AllowedPOS(corpus=Floovant.id, label="ADVneg"),
    AllowedPOS(corpus=Floovant.id, label="CONsub"),
    AllowedPOS(corpus=Floovant.id, label="DETcar"),
    AllowedPOS(corpus=Floovant.id, label="NOMpro"),
    AllowedPOS(corpus=Floovant.id, label="PRE"),
    AllowedPOS(corpus=Floovant.id, label="PRE.DETdef"),
    AllowedPOS(corpus=Floovant.id, label="PROdem"),
    AllowedPOS(corpus=Floovant.id, label="PROper"),
    AllowedPOS(corpus=Floovant.id, label="PROrel")
]
FloovantAllowedLemma = [
    AllowedLemma(corpus=Floovant.id, label="escouter", label_uniform="escouter"),
    AllowedLemma(corpus=Floovant.id, label="or4", label_uniform="or4"),
    AllowedLemma(corpus=Floovant.id, label="seignor", label_uniform="seignor"),
    AllowedLemma(corpus=Floovant.id, label="ami", label_uniform="ami"),
    AllowedLemma(corpus=Floovant.id, label="avoir", label_uniform="avoir"),
    AllowedLemma(corpus=Floovant.id, label="bon", label_uniform="bon"),
    AllowedLemma(corpus=Floovant.id, label="cel", label_uniform="cel"),
    AllowedLemma(corpus=Floovant.id, label="clovis", label_uniform="clovis"),
    AllowedLemma(corpus=Floovant.id, label="come1", label_uniform="come1"),
    AllowedLemma(corpus=Floovant.id, label="crestiien", label_uniform="crestiien"),
    AllowedLemma(corpus=Floovant.id, label="de", label_uniform="de"),
    AllowedLemma(corpus=Floovant.id, label="de+le", label_uniform="de+le"),
    AllowedLemma(corpus=Floovant.id, label="devenir", label_uniform="devenir"),
    AllowedLemma(corpus=Floovant.id, label="deviser", label_uniform="deviser"),
    AllowedLemma(corpus=Floovant.id, label="dieu", label_uniform="dieu"),
    AllowedLemma(corpus=Floovant.id, label="en1", label_uniform="en1"),
    AllowedLemma(corpus=Floovant.id, label="escrit", label_uniform="escrit"),
    AllowedLemma(corpus=Floovant.id, label="estoire1", label_uniform="estoire1"),
    AllowedLemma(corpus=Floovant.id, label="estre1", label_uniform="estre1"),
    AllowedLemma(corpus=Floovant.id, label="france", label_uniform="france"),
    AllowedLemma(corpus=Floovant.id, label="il", label_uniform="il"),
    AllowedLemma(corpus=Floovant.id, label="je", label_uniform="je"),
    AllowedLemma(corpus=Floovant.id, label="nom", label_uniform="nom"),
    AllowedLemma(corpus=Floovant.id, label="premier", label_uniform="premier"),
    AllowedLemma(corpus=Floovant.id, label="que4", label_uniform="que4"),
    AllowedLemma(corpus=Floovant.id, label="qui", label_uniform="qui"),
    AllowedLemma(corpus=Floovant.id, label="roi2", label_uniform="roi2"),
    AllowedLemma(corpus=Floovant.id, label="si", label_uniform="si"),
    AllowedLemma(corpus=Floovant.id, label="trois1", label_uniform="trois1"),
    AllowedLemma(corpus=Floovant.id, label="trover", label_uniform="trover"),
    AllowedLemma(corpus=Floovant.id, label="vers1", label_uniform="vers1"),
    AllowedLemma(corpus=Floovant.id, label="vos1", label_uniform="vos1")
]

DB_CORPORA = {
    "wauchier": {
        "corpus": Wauchier,
        "first_id": 1,
        "tokens": WauchierTokens,
        "lemma": WauchierAllowedLemma,
        "POS": WauchierAllowedPOS,
        "morph": []
    },
    "floovant": {
        "corpus": Floovant,
        "first_id": len(WauchierTokens)+1,
        "tokens": FloovantTokens,
        "lemma": FloovantAllowedLemma,
        "POS": FloovantAllowedPOS,
        "morph": []
    }
}


def add_corpus(
        corpus, db, with_token=True,
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