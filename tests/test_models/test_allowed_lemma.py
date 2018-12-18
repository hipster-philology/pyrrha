from .base import TestModels
from app.models import AllowedLemma


class TestAllowedLemma(TestModels):
    def test_to_input_format(self):
        """ Test that export to input format works correctly """
        self.addCorpus("floovant", tokens_up_to=3, with_allowed_lemma=True)
        self.assertEqual(
            AllowedLemma.to_input_format(
                AllowedLemma.query.filter(AllowedLemma.control_list == 2)
            ).replace("\r", ""),
            """escouter
or4
seignor
ami
avoir
bon
cel
clovis
come1
crestiien
de
de+le
devenir
deviser
dieu
en1
escrit
estoire1
estre1
france
il
je
nom
premier
que4
qui
roi2
si
trois1
trover
vers1
vos1"""
        )
