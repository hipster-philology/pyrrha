from app.models import WordToken
from tests.test_selenium.base import CorpusSearchThroughFieldsBase


class TestCorpusSearchThroughFields(CorpusSearchThroughFieldsBase):
    """ Test searching tokens through fields (Form, Lemma, POS, Morph) within a corpus """
    def test_search_with_complete_form(self):
        # Search a form
        rows = self.search(form="Martin", lemma="martin", pos="NOMpro", morph="")
        self.assertEqual(rows, [{'form': 'Martin', 'lemma': 'martin', 'morph': 'None', 'pos': 'NOMpro'}])

    def test_search_with_pagination(self):
        # Search a morph
        rows = self.search(lemma='*e*')
        pagination = self.driver.find_element_by_class_name("pagination").find_elements_by_tag_name("a")
        pagination[-1].click()
        tokens = WordToken.query.filter(WordToken.lemma.like('%e%')).all()
        print(len(rows), len(tokens))
        self.assertEqual(len(rows), len(tokens))

    def test_search_with_partial_form(self):
        """
            Successivelity Search values in different the fields (form, lemma, POS, morph)
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
        pagination = self.driver.find_element_by_class_name("pagination").find_elements_by_tag_name("a")
        pagination[-1].click()
        tokens = WordToken.query.filter(WordToken.morph == 'None').all()
        print(len(rows), len(tokens))
        self.assertEqual(len(rows), len(tokens))

    def test_search_with_combinations(self):
        raise NotImplementedError

    def test_search_with_like_operator(self):
        raise NotImplementedError

    def test_search_with_negation_operator(self):
        raise NotImplementedError