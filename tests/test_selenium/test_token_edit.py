from tests.test_selenium.base import TokenEditBase, TokenEdit2CorporaBase
import selenium


class TestTokenEditWauchierCorpus(TokenEditBase):
    def test_edit_token_lemma_with_allowed_values(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("un", id_row="1")
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "saint", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "martin", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_allowed_values_autocomplete(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "d", id_row="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='devoir']"
        )
        self.assertEqual(token.lemma, "devoir", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "PRE", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_POS(self):
        """ Edit POS of a token """
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "ADJqua", id_row="1", value_type="POS"
        )
        self.assertEqual(token.lemma, "de", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "ADJqua", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_morph(self):
        """ Edit POS of a token """
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "_", id_row="1", value_type="morph"
        )
        self.assertEqual(token.lemma, "de", "Lemma should not have been changed")
        self.assertEqual(token.POS, "PRE", "POS should not have been changed")
        self.assertEqual(token.morph, "_", "Morph has been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed morph
        token, status_text, row = self.edith_nth_row_value(
            "Not Allowed", id_row="2", value_type="morph"
        )
        self.assertEqual(token.lemma, "saint", "Lemma should not have been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should not have been changed")
        self.assertEqual(token.morph, "Not Allowed", "Morph should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_morph_with_allowed(self):
        """ Edit POS of a token """
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_morph=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "_", id_row="1", value_type="morph"
        )
        self.assertEqual(token.lemma, "de", "Lemma should not have been changed")
        self.assertEqual(token.POS, "PRE", "POS should not have been changed")
        self.assertEqual(token.morph, "_", "Morph has been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed morph
        token, status_text, row = self.edith_nth_row_value(
            "Not Allowed", id_row="2", value_type="morph"
        )
        self.assertEqual(token.lemma, "saint", "Lemma should not have been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should not have been changed")
        self.assertEqual(token.morph, "None", "Morph should not have been changed")
        self.assertEqual(status_text, "(Invalid value in morph) Save")

        # With auto complete
        token, status_text, row = self.edith_nth_row_value(
            "masc sing", id_row="3", corpus_id="1", value_type="morph",
            autocomplete_selector=".autocomplete-suggestion[data-val='NOMB.=s|GENRE=m|CAS=n']"
        )
        self.assertEqual(token.lemma, "martin", "Lemma should have been changed")
        self.assertEqual(token.POS, "NOMpro", "POS should not have been changed")
        self.assertEqual(token.morph, "NOMB.=s|GENRE=m|CAS=n", "Morph should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")


class TestTokensEditFloovant(TokenEditBase):
    CORPUS = "floovant"
    CORPUS_ID = "2"

    def test_edit_POS(self):
        """ Edit POS of a token """
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, status_text, row = self.edith_nth_row_value(
            "ADJqua", id_row="1", value_type="POS"
        )
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed to devoir")
        self.assertEqual(token.POS, "ADJqua", "POS should not have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_allowed_values_lemma_pos(self):
        """ Test the edition of a token """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_pos=True)
        token, status_text, row = self.edith_nth_row_value("estoire1", id_row="1")
        self.assertEqual(token.lemma, "estoire1", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "or4", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "escouter", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_allowed_values_lemma(self):
        """ Test the edition of a token's lemma and POS with allowed_lemma """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, status_text, row = self.edith_nth_row_value("estoire1", id_row="1")
        self.assertEqual(token.lemma, "estoire1", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an unallowed lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("WRONG", id_row="2")
        self.assertEqual(token.lemma, "or4", "Lemma should have not been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save", "Error should be written about lemma")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "escouter", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_morph_with_allowed_values_lemma(self):
        """ Test the edition of a token's morph  with allowed_lemma """
        # Try first with an edit that would word
        self.addCorpus(with_token=True, with_allowed_lemma=True)
        token, status_text, row = self.edith_nth_row_value("SomeMorph", id_row="1", value_type="morph")
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed")
        self.assertEqual(token.morph, "SomeMorph", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_morph(self):
        """ Test the edition of a token's morph"""
        # Try first with an edit that would word
        self.addCorpus(with_token=True)
        token, status_text, row = self.edith_nth_row_value("SomeMorph", id_row="1", value_type="morph")
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed")
        self.assertEqual(token.morph, "SomeMorph", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_with_same_value(self):
        """ Test the edition of a token's morph"""
        # Try first with an edit that would word
        self.addCorpus(with_token=True)
        token, status_text, row = self.edith_nth_row_value("seignor", id_row="1", value_type="lemma")
        self.assertEqual(status_text, "(No value where changed) Save")
        self.assertNotIn("table-changed", row.get_attribute("class"))


class TestTokensEditTwoCorpora(TokenEdit2CorporaBase):
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def test_edit_token_lemma_with_allowed_values_lemma_pos(self):
        """ Test the edition of a token """
        # Try first with an edit that would work
        self.addCorpus(with_token=True, with_allowed_lemma=True, with_allowed_pos=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value("saint", id_row="1")
        self.assertEqual(token.lemma, "saint", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an allowed lemma from the second corpus
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("seignor", id_row="2")
        self.assertEqual(token.lemma, "saint", "Lemma should not have been changed")
        self.assertEqual(status_text, "(Invalid value in lemma) Save")

        # Try with a POS update but keeping the lemma
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("ADJqua", value_type="POS", id_row="3")
        self.assertEqual(token.lemma, "martin", "Lemma should have not been changed")
        self.assertEqual(token.POS, "ADJqua", "POS should have been changed to ADJqua")
        self.assertEqual(status_text, "(Saved) Save")

    def test_edit_token_lemma_with_typeahead_click(self):
        """ Test the edition of a token """
        # Try first with an edit that would work
        self.addCorpus(with_token=True, with_allowed_lemma=True, tokens_up_to=24)
        token, status_text, row = self.edith_nth_row_value(
            "s", id_row="1", corpus_id="1",
            autocomplete_selector=".autocomplete-suggestion[data-val='saint']"
        )
        self.assertEqual(token.lemma, "saint", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an allowed lemma from the second corpus
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value(
            "s", id_row=str(self.first_token_id(2)+1), corpus_id="2",
            autocomplete_selector=".autocomplete-suggestion[data-val='seignor']"
        )
        self.assertEqual(token.lemma, "seignor", "Lemma should have been changed")
        self.assertEqual(status_text, "(Saved) Save")

        # Try with an allowed lemma from the second corpus
        self.driver.refresh()
        with self.assertRaises(selenium.common.exceptions.NoSuchElementException):
            _ = self.edith_nth_row_value(
                "s", id_row=str(self.first_token_id(2)+1), corpus_id="2",
                autocomplete_selector=".autocomplete-suggestion[data-val='saint']"
            )
