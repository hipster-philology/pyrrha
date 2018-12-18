from .base import TestModels
from app.models import WordToken


class TestWordToken(TestModels):
    def test_to_input_format(self):
        """ Test that export to input format works correctly """
        self.addCorpus("floovant", tokens_up_to=3)
        self.assertEqual(
            WordToken.to_input_format(
                WordToken.query.filter(WordToken.corpus == 2)
            ),
            "token_id\tform\tlemma\tPOS\tmorph\r\n"
            "1\tSOIGNORS\tseignor\t_\tNOMB.=p|GENRE=m|CAS=n\r\n"
            "2\tor\tor4\t_\tDEGRE=-\r\n"
            "3\tescoutez\tescouter\t_\tMODE=imp|PERS.=2|NOMB.=p\r\n"
        )
