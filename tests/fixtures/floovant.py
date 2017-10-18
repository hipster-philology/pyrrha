CORPUS_2_NAME = "Floovant"
CORPUS_2_DATA = """form	lemma	POS	morph
SOIGNORS	seignor	NOMcom	|||p|m|n|
or	or4	ADVgen	||||||-
escoutez	escouter	VERcjg	imp||2|p|||
que	que4	CONsub	||||||
Dés	dieu	NOMpro	|||s|m|n|
vos	vos1	PROper	||2|p|m|r|
soit	estre1	VERcjg	sub|pst|3|s|||
amis	ami	NOMcom	|||s|m|n|
III	trois1	DETcar	|||p|m|r|
vers	vers1	NOMcom	|||p|m|r|
de	de	PRE	||||||
bone	bon	ADJqua	|||s|f|r|p
estoire	estoire1	NOMcom	|||s|f|r|
se	si	ADVgen	||||||-
je	je	PROper	||1|s|m|n|
les	il	PROper	||3|p|m|r|
vos	vos1	PROper	||2|p|m|r|
devis	deviser	VERcjg	ind|pst|1|s|||
Dou	de+le	PRE.DETdef	|||s|m|r|
premier	premier	ADJord	|||s|m|r|
roi	roi2	NOMcom	|||s|m|r|
de	de	PRE	||||||
France	france	NOMpro	|||s|f|r|
qui	qui	PROrel	|||s|m|n|
crestïens	crestiien	NOMcom	|||s|m|n|
devint	devenir	VERcjg	ind|psp|3|s|||
Cil	cel	PROdem	|||s|m|n|
ot	avoir	VERcjg	ind|psp|3|s|||
non	nom	ADVneg	|||s|m|r|
Cloovis	clovis	NOMpro	|||s|m|r|
si	si	ADVgen	||||||-
com	come1	CONsub	||||||
truis	trover	VERcjg	ind|pst|1|s|||
en	en1	PRE	||||||
escrit	escrit	NOMcom	|||s|m|r|"""
CORPUS_2_FULL_LEMMA = "\n".join(['trover', 'de+le', 'or4', 'france', 'cel', 'trois1', 'devenir', 'avoir', 'bon',
                                 'si', 'estoire1', 'nom', 'estre1', 'dieu', 'vos1', 'crestiien', 'seignor', 'il',
                                 'que4', 'roi2', 'clovis', 'premier', 'de', 'en1', 'escrit', 'qui', 'come1',
                                 'escouter', 'ami', 'vers1', 'deviser', 'je']
)
CORPUS_2_PARTIAL_LEMMA = "\n".join(['escouter', 'seignor', 'or4'])
CORPUS_2_FULL_POS = "\n".join(['PROdem', 'ADVgen', 'NOMpro', 'ADJord', 'PROrel', 'CONsub', 'NOMcom', 'VERcjg',
                               'PROper', 'PRE', 'ADJqua', 'PRE.DETdef', 'ADVneg', 'DETcar'])
CORPUS_2_PARTIAL_POS = "\n".join(["NOMcom", "VERcjg", "ADJgen"])
