from .wauchier import *
from .floovant import *
PLAINTEXT_CORPORA = {
    "Wauchier": {
        "name": CORPUS_NAME,
        "data": CORPUS_DATA,
        "lemma": FULL_CORPUS_LEMMA_ALLOWED,
        "partial_lemma": PARTIAL_CORPUS_ALLOWED_LEMMA,
        "POS": "",
        "partial_POS": "",
        "morph": MORPHS
    },
    "Floovant": {
        "name": CORPUS_2_NAME,
        "data": CORPUS_2_DATA,
        "lemma": CORPUS_2_FULL_LEMMA,
        "partial_lemma": CORPUS_2_PARTIAL_LEMMA,
        "POS": CORPUS_2_FULL_POS,
        "partial_POS": CORPUS_2_PARTIAL_POS,
        "morph": CORPUS_2_PARTIAL_MORPH
    }
}