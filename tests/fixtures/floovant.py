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
CORPUS_2_FULL_POS = "\n".join(['PROdem', 'ADVgen', 'NOMpro', 'ADJord', 'PROrel', 'CONsub', 'NOMcom', 'VERcjg',
                               'PROper', 'PRE', 'ADJqua', 'PRE.DETdef', 'ADVneg', 'DETcar'])
CORPUS_2_PARTIAL_POS = "\n".join(["NOMcom", "VERcjg", "ADJgen"])
CORPUS_2_FULL_MORPH = "\n".join(['_','DEGRE=-','MODE=imp|PERS.=2|NOMB.=p','MODE=ind|TEMPS=psp|PERS.=3|NOMB.=s','MODE=ind|TEMPS=pst|PERS.=1|NOMB.=s','MODE=sub|TEMPS=pst|PERS.=3|NOMB.=s','NOMB.=p|GENRE=m|CAS=n','NOMB.=p|GENRE=m|CAS=r','NOMB.=s|GENRE=f|CAS=r','NOMB.=s|GENRE=f|CAS=r|DEGRE=p','NOMB.=s|GENRE=m|CAS=n','NOMB.=s|GENRE=m|CAS=r','PERS.=1|NOMB.=s|GENRE=m|CAS=n','PERS.=2|NOMB.=p|GENRE=m|CAS=r','PERS.=3|NOMB.=p|GENRE=m|CAS=r'])
CORPUS_2_PARTIAL_MORPH = "\n".join(['MODE=ind|TEMPS=pst|PERS.=1|NOMB.=s','NOMB.=p|GENRE=m|CAS=n','NOMB.=s|GENRE=f|CAS=r|DEGRE=p','PERS.=3|NOMB.=p|GENRE=m|CAS=r'])

