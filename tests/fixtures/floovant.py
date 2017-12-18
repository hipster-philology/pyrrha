CORPUS_2_NAME = "Floovant"
CORPUS_2_DATA = """form	lemma	POS	morph
SOIGNORS	seignor	NOMcom	NOMB.=p|GENRE=m|CAS=n
or	or4	ADVgen	DEGRE=-
escoutez	escouter	VERcjg	MODE=imp|PERS.=2|NOMB.=p
que	que4	CONsub	_
Dés	dieu	NOMpro	NOMB.=s|GENRE=m|CAS=n
vos	vos1	PROper	PERS.=2|NOMB.=p|GENRE=m|CAS=r
soit	estre1	VERcjg	MODE=sub|TEMPS=pst|PERS.=3|NOMB.=s
amis	ami	NOMcom	NOMB.=s|GENRE=m|CAS=n
III	trois1	DETcar	NOMB.=p|GENRE=m|CAS=r
vers	vers1	NOMcom	NOMB.=p|GENRE=m|CAS=r
de	de	PRE	_
bone	bon	ADJqua	NOMB.=s|GENRE=f|CAS=r|DEGRE=p
estoire	estoire1	NOMcom	NOMB.=s|GENRE=f|CAS=r
se	si	ADVgen	DEGRE=-
je	je	PROper	PERS.=1|NOMB.=s|GENRE=m|CAS=n
les	il	PROper	PERS.=3|NOMB.=p|GENRE=m|CAS=r
vos	vos1	PROper	PERS.=2|NOMB.=p|GENRE=m|CAS=r
devis	deviser	VERcjg	MODE=ind|TEMPS=pst|PERS.=1|NOMB.=s
Dou	de+le	PRE.DETdef	NOMB.=s|GENRE=m|CAS=r
premier	premier	ADJord	NOMB.=s|GENRE=m|CAS=r
roi	roi2	NOMcom	NOMB.=s|GENRE=m|CAS=r
de	de	PRE	_
France	france	NOMpro	NOMB.=s|GENRE=f|CAS=r
qui	qui	PROrel	NOMB.=s|GENRE=m|CAS=n
crestïens	crestiien	NOMcom	NOMB.=s|GENRE=m|CAS=n
devint	devenir	VERcjg	MODE=ind|TEMPS=psp|PERS.=3|NOMB.=s
Cil	cel	PROdem	NOMB.=s|GENRE=m|CAS=n
ot	avoir	VERcjg	MODE=ind|TEMPS=psp|PERS.=3|NOMB.=s
non	nom	ADVneg	NOMB.=s|GENRE=m|CAS=r
Cloovis	clovis	NOMpro	NOMB.=s|GENRE=m|CAS=r
si	si	ADVgen	DEGRE=-
com	come1	CONsub	_
truis	trover	VERcjg	MODE=ind|TEMPS=pst|PERS.=1|NOMB.=s
en	en1	PRE	_
escrit	escrit	NOMcom	NOMB.=s|GENRE=m|CAS=r
"""
CORPUS_2_FULL_LEMMA = "\n".join(['trover', 'de+le', 'or4', 'france', 'cel', 'trois1', 'devenir', 'avoir', 'bon',
                                 'si', 'estoire1', 'nom', 'estre1', 'dieu', 'vos1', 'crestiien', 'seignor', 'il',
                                 'que4', 'roi2', 'clovis', 'premier', 'de', 'en1', 'escrit', 'qui', 'come1',
                                 'escouter', 'ami', 'vers1', 'deviser', 'je']
)
CORPUS_2_PARTIAL_LEMMA = "\n".join(['escouter', 'seignor', 'or4'])
CORPUS_2_FULL_POS = ",".join(['PROdem', 'ADVgen', 'NOMpro', 'ADJord', 'PROrel', 'CONsub', 'NOMcom', 'VERcjg',
                               'PROper', 'PRE', 'ADJqua', 'PRE.DETdef', 'ADVneg', 'DETcar'])
CORPUS_2_PARTIAL_POS = ",".join(["NOMcom", "VERcjg", "ADJgen"])
CORPUS_2_FULL_MORPH = """label\treadable
_\tpas de morphologie
DEGRE=-\tnon applicable
MODE=imp|PERS.=2|NOMB.=p\timpératif 2e personne pluriel
MODE=ind|TEMPS=psp|PERS.=3|NOMB.=s\tindicatif passé simple 3e personne singulier
MODE=ind|TEMPS=pst|PERS.=1|NOMB.=s\tindicatif présent 1re personne singulier
MODE=sub|TEMPS=pst|PERS.=3|NOMB.=s\tsubjonctif présent 3e personne singulier
NOMB.=p|GENRE=m|CAS=n\tpluriel masculin nominatif
NOMB.=p|GENRE=m|CAS=r\tpluriel masculin régime
NOMB.=s|GENRE=f|CAS=r\tsingulier féminin régime
NOMB.=s|GENRE=f|CAS=r|DEGRE=p\tsingulier féminin régime positif
NOMB.=s|GENRE=m|CAS=n\tsingulier masculin nominatif
NOMB.=s|GENRE=m|CAS=r\tsingulier masculin régime
PERS.=1|NOMB.=s|GENRE=m|CAS=n\t1re personne singulier masculin nominatif
PERS.=2|NOMB.=p|GENRE=m|CAS=r\t2e personne pluriel masculin régime
PERS.=3|NOMB.=p|GENRE=m|CAS=r\t3e personne pluriel masculin régime"""
CORPUS_2_PARTIAL_MORPH = """label\treadable
_\tpas de morphologie
DEGRE=-\tnon applicable
MODE=imp|PERS.=2|NOMB.=p\timpératif 2e personne pluriel
NOMB.=p|GENRE=m|CAS=n\tpluriel masculin nominatif
NOMB.=p|GENRE=m|CAS=r\tpluriel masculin régime
NOMB.=s|GENRE=f|CAS=r|DEGRE=p\tsingulier féminin régime positif
NOMB.=s|GENRE=m|CAS=n\tsingulier masculin nominatif
PERS.=3|NOMB.=p|GENRE=m|CAS=r\t3e personne pluriel masculin régime"""


