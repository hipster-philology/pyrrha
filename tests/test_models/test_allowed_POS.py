from .base import TestModels
from app.models.linguistic import AllowedPOS


class TestAllowedPOS(TestModels):
    def test_to_input_format(self):
        """ Test that export to input format works correctly """
        self.addCorpus("floovant", tokens_up_to=3,
                       with_allowed_pos=True, partial_allowed_pos=True)
        self.assertEqual(
            AllowedPOS.to_input_format(
                AllowedPOS.query.filter(AllowedPOS.corpus == 2)
            ),
            "ADVgen,VERcjg,NOMcom"
        )
