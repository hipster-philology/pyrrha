from .base import TestModels
from app.models import WordToken
from app.utils import ValidationError
import random
import string


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

    def test_add_batch_invalid(self):
        """Test adding a batch of tokens.

        Trying: one token violates length constraint
        Expecting: ValidationError
        """
        form = "".join(
            string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)] for i in range(100)
        )
        with self.assertRaises(ValidationError):
            WordToken.add_batch(0, [{"form": form}])

    def test_add_batch_valid(self):
        """Test adding a batch of tokens.

        Trying: one token respecting length constraint
        Expecting: number of tokens is returned
        """
        form = "".join(
            string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)]
            for i in range(64)
        )
        self.assertEqual(WordToken.add_batch(0, [{"form": form}]), 1)

    def test_update_batch_context(self):
        """Test updating left and right context.

        Trying: set right and left context to 4.
        """
        form_list = [
            {
                "form": "".join(
                    string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)]
                    for i in range(16)
                )
            } for j in range(200)
        ]
        WordToken.add_batch(0, form_list)
        self.assertEqual(WordToken.update_batch_context(0, 4, 4), 200)
        token = WordToken.query.filter_by(corpus=0, order_id=15).first()
        left_context = token.left_context.split(" ")
        right_context = token.right_context.split(" ")
        self.assertEqual(len(left_context), 4)
        self.assertEqual(len(right_context), 4)
        # WordToken order_id starts at 1, form_list indices starts at 0
        self.assertEqual(left_context[0], form_list[10]["form"])
        self.assertEqual(left_context[3], form_list[13]["form"])
        self.assertEqual(right_context[0], form_list[15]["form"])
        self.assertEqual(right_context[3], form_list[18]["form"])
