from app.models import WordToken
from tests.test_selenium.base import TokensSearchThroughFieldsBase


class TestTokensSearchThroughFields(TokensSearchThroughFieldsBase):
    """ Test searching tokens through fields (Form, Lemma, POS, Morph) within a corpus """
    def test_search_with_complete_form(self):
        """ make a search based on all fields at once"""
        rows = self.search(form="Martin", lemma="martin", pos="NOMpro", morph="")
        self.assertEqual(rows, [{'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}])

    def test_search_homepage(self):
        """ Homepage should only contain the current corpus tokens"""
        #self.addCorpus("wauchier")
        self.addCorpus("floovant")
        self.go_to_search_tokens_page(2, as_callback=False)
        result = []

        def get_field(row, f):
            return self.element_find_element_by_class_name(row, f).text.strip()
        
        res_table = self.element_find_element_by_tag_name(
            self.driver_find_element_by_id("result_table"),
            "tbody"
        )
        rows = self.element_find_elements_by_tag_name(res_table, "tr")

        for row in rows:
            result.append({
                "form": self.element_find_elements_by_tag_name(row, "td")[1].text.strip(),
                "lemma": get_field(row, "token_lemma"),
                "morph": get_field(row, "token_morph"),
                "pos": get_field(row, "token_pos")
            })

        self.assertEqual(
            result[:3],
            [
             {'form': 'SOIGNORS', 'lemma': 'seignor', 'morph': 'NOMB.=p|GENRE=m|CAS=n', 'pos': 'None'},
             {'form': 'or', 'lemma': 'or4', 'morph': 'DEGRE=-', 'pos': 'None'},
             {'form': 'escoutez', 'lemma': 'escouter', 'morph': 'MODE=imp|PERS.=2|NOMB.=p', 'pos': 'None'}
            ],
            "Only tokens for requested corpus should be shown !"
        )

    def test_search_with_pagination(self):
        """ Test the count of returned results among the different pages"""
        # Search a morph
        rows = self.search(lemma='*e*')
        tokens = WordToken.query.filter(WordToken.lemma.like('%e%')).all()
        self.assertEqual(len(rows), len(tokens))

    def test_search_with_partial_form(self):
        """
            Successively Search values in different fields (form, lemma, POS, morph)
            This is a partial search: when fields are empty they are not part of the search
        """

        # Search a form
        rows = self.search(form="Martin")
        self.assertEqual(rows, [{'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}])

        # Search a lemma
        rows = self.search(lemma="le")
        self.assertEqual(rows, [
            {'form': 'le', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'le', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'li', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'l', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'le', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'li', 'lemma': 'le', 'morph': 'None', 'pos': 'PROper'},
            {'form': 'les', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'les', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'la', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'les', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'l', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'li', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'le', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'li', 'lemma': 'le', 'morph': 'None', 'pos': 'PROper'},
            {'form': 'la', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'li', 'lemma': 'le', 'morph': 'None', 'pos': 'PROper'},
            {'form': 'la', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'},
            {'form': 'la', 'lemma': 'le', 'morph': 'None', 'pos': 'DETdef'}
        ])

        # Search a POS
        rows = self.search(pos="NOMpro")
        self.assertEqual(rows, [
            {'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'},
            {'form': 'Dex', 'lemma': 'dieu', 'morph': 'None', 'pos': 'NOMpro'},
            {'form': 'parmenable', 'lemma': 'parmenidés', 'morph': 'None', 'pos': 'NOMpro'},
            {'form': 'Martins', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'},
            {'form': 'Martins', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}
        ])

        # Search a morph
        rows = self.search(morph='*None*')
        tokens = WordToken.query.filter(WordToken.morph == 'None').all()
        self.assertEqual(len(rows), len(tokens))

    def test_search_with_combinations(self):
        """ Search through different fields at the same time"""
        rows = self.search(form="Martin", lemma="martin", pos="NOMpro", morph="")
        self.assertEqual(rows, [{'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}])
        rows = self.search(lemma="martin", pos="NOMpro", morph="")
        self.assertIn({'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}, rows)
        rows = self.search(form="Martin",  pos="NOMpro", morph="")
        self.assertIn({'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}, rows)
        rows = self.search(form="Martin", lemma="martin", morph="")
        self.assertIn({'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}, rows)

    def test_search_with_like_operator(self):
        # search with wildcard escaped
        rows = self.search(form="Testword\*")
        self.assertEqual(rows, [{'form': 'Testword*', 'lemma': 'testword*', 'morph': 'test*morph', 'pos': 'TEST*pos'}])

        # search with wildcard as a suffix
        rows = self.search(form="Testword*")
        self.assertEqual(rows, [
            {'form': 'Testword*', 'lemma': 'testword*', 'morph': 'test*morph', 'pos': 'TEST*pos'},
            {'form': 'TestwordFake', 'lemma': 'testwordFake', 'morph': 'testmorphFake', 'pos': 'TESTposFake'}
        ])

        # search with wildcard as a prefix
        rows = self.search(lemma="*le")
        tokens = WordToken.query.filter(WordToken.lemma.like('%le')).all()
        self.assertEqual(len(rows), len(tokens))

        # search with wildcard both as a prefix and a suffix
        rows = self.search(lemma="*ai*")
        tokens = WordToken.query.filter(WordToken.lemma.like('%ai%')).all()
        self.assertEqual(len(rows), len(tokens))

    def test_search_with_negation_operator(self):
        # search with negation operator escaped
        rows = self.search(form="\!TestwordFake")
        self.assertEqual(rows, [{
            'form': '!TestwordFake', 'lemma': '!testwordFake', 'morph': '!testmorphFake', 'pos': '!TESTposFake'
        }])

        # search with negation operator
        rows = self.search(form="!Testword")
        tokens = WordToken.query.filter(WordToken.lemma.notlike('!Testword')).all()
        self.assertEqual(len(rows), len(tokens))

        # check complementarity coherence
        rows_neg = self.search(lemma="!*e*")
        rows = self.search(lemma="*e*")
        rows_all = self.search()
        self.assertTrue(len(rows_all) == len(rows + rows_neg))

    def test_search_with_negation_and_like_operator(self):
        # searchs forms which do not contain the 'e' character
        rows = self.search(form="!*e*")
        self.assertTrue(len(rows) > 0)
        self.assertTrue('e' not in ''.join([r['form'] for r in rows]))

    def test_search_with_or_operator(self):
        # search with OR operator
        rows = self.search(form="seint|seinz|Seinz|seinte")
        rows_wildcard = self.search(form="sein*")
        rows_lemma = self.search(lemma="saint")
        self.assertTrue(rows_lemma == rows and rows == rows_wildcard)

        # test combination with an other field
        rows = self.search(lemma="m*", pos="NOMcom|NOMpro")
        self.assertTrue(len(rows) == 9)

        # test combination with an other field
        rows = self.search(form="Martins|mere", lemma="martin|mere")
        self.assertTrue(len(rows) == 3)
