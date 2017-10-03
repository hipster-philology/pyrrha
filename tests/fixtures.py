CORPUS_NAME = "Wauchier"
CORPUS_DATA = """tokens	lemmas	pos
De	de	PRE
seint	saint	ADJqua
Martin	martin	NOMpro
mout	mout	ADVgen
doit	devoir	VERcjg
on	un	PRE
doucement	doucement	ADVgen
et	et	CONcoo
volentiers	volentiers	ADVgen
le	le	DETdef
bien	bien	ADVgen
oïr	öir	VERinf
et	et	CONcoo
entendre	entendre	VERinf
,	,	PONfbl
car	car	CONcoo
par	par	PRE
le	le	DETdef
bien	bien	ADVgen
savoir	savoir	VERinf
et	et	CONcoo
retenir	retenir	VERinf
puet	pöoir	VERcjg
l	il	PROper
en	en1	PRE"""

FULL_CORPUS_LEMMA_ALLOWED = "\n".join([
    'öir', 'car', 'devoir', 'entendre', ',', 'de', 'par', 'martin', 'un', 'pöoir', 'il', 'doucement', 'en1', 'le',
    'mout', 'bien', 'retenir', 'volentiers', 'saint', 'et', 'savoir'
])


PARTIAL_CORPUS_ALLOWED_LEMMA = "\n".join(["de", "saint", "martin"])