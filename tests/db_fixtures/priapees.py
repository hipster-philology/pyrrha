from app.models import Corpus, WordToken, Column
from app.models import ControlLists

control_list = ControlLists(id=3, name="Latin")
corpus = Corpus(
    name="Priapees",
    id=3,
    control_lists_id=control_list.id,
)
PriapeeColumns = [
    Column(heading="Lemma", corpus_id=3),
    Column(heading="POS", corpus_id=3),
    Column(heading="Morph", corpus_id=3),
    Column(heading="Similar", corpus_id=3),
]
tokens = [
    WordToken(corpus=corpus.id, form="Carminis", lemma="carmen1", POS="NOMcom", left_context="Carminis incompti lusus lecture", right_context="procaces ,", label_uniform="carmen1", morph="Case=Gen|Numb=Sing"),
    WordToken(corpus=corpus.id, form="incompti", lemma="incomptus", POS="ADJqua", left_context="Carminis incompti lusus lecture", right_context="procaces , conueniens", label_uniform="incomptus", morph="Case=Gen|Numb=Sing|Deg=Pos"),
    WordToken(corpus=corpus.id, form="lusus", lemma="lusus", POS="NOMcom", left_context="Carminis incompti lusus lecture", right_context="procaces , conueniens Latio", label_uniform="lusus", morph="Case=Gen|Numb=Sing"),
    WordToken(corpus=corpus.id, form="lecture", lemma="lego?", POS="VER", left_context="Carminis incompti lusus lecture", right_context="procaces , conueniens Latio pone", label_uniform="lego?", morph="Case=Voc|Numb=Sing|Mood=Par|Voice=Act"),
    WordToken(corpus=corpus.id, form="procaces", lemma="procax", POS="ADJqua", left_context="Carminis incompti lusus lecture", right_context="procaces , conueniens Latio pone supercilium", label_uniform="procax", morph="Case=Acc|Numb=Plur|Deg=Pos"),
    WordToken(corpus=corpus.id, form=",", lemma=",", POS="PUNC", left_context="Carminis incompti lusus lecture", right_context="procaces , conueniens Latio pone supercilium .", label_uniform=",", morph="MORPH=empty"),
    WordToken(corpus=corpus.id, form="conueniens", lemma="conueniens", POS="ADJqua", left_context="incompti lusus lecture procaces", right_context=", conueniens Latio pone supercilium . non", label_uniform="conueniens", morph="Case=Nom|Numb=Sing|Deg=Pos"),
    WordToken(corpus=corpus.id, form="Latio", lemma="latio", POS="NOMcom", left_context="lusus lecture procaces ,", right_context="conueniens Latio pone supercilium . non soror", label_uniform="latio", morph="Case=Nom|Numb=Sing"),
    WordToken(corpus=corpus.id, form="pone", lemma="pono", POS="VER", left_context="lecture procaces , conueniens", right_context="Latio pone supercilium . non soror hoc", label_uniform="pono", morph="Numb=Sing|Mood=Imp|Tense=Pres|Voice=Act|Person=2"),
    WordToken(corpus=corpus.id, form="supercilium", lemma="supercilium", POS="NOMcom", left_context="procaces , conueniens Latio", right_context="pone supercilium . non soror hoc habitat", label_uniform="supercilium", morph="Case=Acc|Numb=Sing"),
    WordToken(corpus=corpus.id, form=".", lemma=".", POS="PUNC", left_context=", conueniens Latio pone", right_context="supercilium . non soror hoc habitat Phoebi", label_uniform=".", morph="MORPH=empty"),
    WordToken(corpus=corpus.id, form="non", lemma="non", POS="ADVneg", left_context="conueniens Latio pone supercilium", right_context=". non soror hoc habitat Phoebi ,", label_uniform="non", morph="MORPH=empty"),
    WordToken(corpus=corpus.id, form="soror", lemma="soror", POS="NOMcom", left_context="Latio pone supercilium .", right_context="non soror hoc habitat Phoebi , non", label_uniform="soror", morph="Case=Nom|Numb=Sing"),
    WordToken(corpus=corpus.id, form="hoc", lemma="hic1", POS="PROdem", left_context="pone supercilium . non", right_context="soror hoc habitat Phoebi , non uesta", label_uniform="hic1", morph="Case=Nom|Numb=Sing"),
    WordToken(corpus=corpus.id, form="habitat", lemma="habito", POS="VER", left_context="supercilium . non soror", right_context="hoc habitat Phoebi , non uesta sacello", label_uniform="habito", morph="Numb=Sing|Mood=Ind|Tense=Pres|Voice=Act|Person=3"),
    WordToken(corpus=corpus.id, form="Phoebi", lemma="phoebus", POS="NOMcom", left_context=". non soror hoc", right_context="habitat Phoebi , non uesta sacello ,", label_uniform="phoebus", morph="Case=Gen|Numb=Sing"),
    WordToken(corpus=corpus.id, form=",", lemma=",", POS="PUNC", left_context="non soror hoc habitat", right_context="Phoebi , non uesta sacello , nec", label_uniform=",", morph="MORPH=empty"),
    WordToken(corpus=corpus.id, form="non", lemma="non", POS="ADVneg", left_context="soror hoc habitat Phoebi", right_context=", non uesta sacello , nec quae", label_uniform="non", morph="MORPH=empty"),
]
