import pytest

from app.models import WordToken
from app import db
from tests.test_playwright.base import TokensSearchHelpers


class TestTokensSearchThroughFields(TokensSearchHelpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app
        self.addCorpus(corpus="wauchier")
        for order_id, form, lemma, POS, morph in [
            (1, "Testword*", "testword*", "TEST*pos", "test*morph"),
            (2, "TestwordFake", "testwordFake", "TESTposFake", "testmorphFake"),
            (3, "!TestwordFake", "!testwordFake", "!TESTposFake", "!testmorphFake"),
        ]:
            db.session.add(
                WordToken(
                    corpus=self.CORPUS_ID,
                    order_id=order_id,
                    form=form,
                    lemma=lemma,
                    POS=POS,
                    morph=morph,
                    left_context="This is a left context",
                    right_context="This is a left context",
                )
            )
        db.session.commit()

    def test_search_with_complete_form(self):
        rows = self.search(form="Martin", lemma="martin", pos="NOMpro", morph="")
        assert rows == [{"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"}]

    def test_search_homepage(self):
        self.addCorpus(corpus="floovant")
        self.go_to_search_tokens_page(2, as_callback=False)
        result = []
        res_table = self.page.locator("#result_table tbody")
        for row_loc in res_table.locator("tr").all():
            tds = row_loc.locator("td").all()
            if tds:
                result.append({
                    "form": tds[1].text_content().strip(),
                    "lemma": row_loc.locator(".token_lemma").text_content().strip(),
                    "morph": row_loc.locator(".token_morph").text_content().strip(),
                    "pos": row_loc.locator(".token_pos").text_content().strip(),
                })
        assert result[:3] == [
            {"form": "SOIGNORS", "lemma": "seignor", "morph": "NOMB.=p|GENRE=m|CAS=n", "pos": "None"},
            {"form": "or", "lemma": "or4", "morph": "DEGRE=-", "pos": "None"},
            {"form": "escoutez", "lemma": "escouter", "morph": "MODE=imp|PERS.=2|NOMB.=p", "pos": "None"},
        ]

    def test_search_with_pagination(self):
        rows = self.search(lemma="*e*")
        tokens = WordToken.query.filter(WordToken.lemma.like("%e%")).all()
        assert len(rows) == len(tokens)

    def test_search_with_partial_form(self):
        rows = self.search(form="Martin")
        assert rows == [{"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"}]

        rows = self.search(lemma="le")
        assert rows == [
            {"form": "le", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "le", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "li", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "l", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "le", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "li", "lemma": "le", "morph": "None", "pos": "PROper"},
            {"form": "les", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "les", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "la", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "les", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "l", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "li", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "le", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "li", "lemma": "le", "morph": "None", "pos": "PROper"},
            {"form": "la", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "li", "lemma": "le", "morph": "None", "pos": "PROper"},
            {"form": "la", "lemma": "le", "morph": "None", "pos": "DETdef"},
            {"form": "la", "lemma": "le", "morph": "None", "pos": "DETdef"},
        ]

        rows = self.search(pos="NOMpro")
        assert rows == [
            {"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"},
            {"form": "Dex", "lemma": "dieu", "morph": "None", "pos": "NOMpro"},
            {"form": "parmenable", "lemma": "parmenidés", "morph": "None", "pos": "NOMpro"},
            {"form": "Martins", "lemma": "martin", "morph": "None", "pos": "NOMpro"},
            {"form": "Martins", "lemma": "martin", "morph": "None", "pos": "NOMpro"},
        ]

        rows = self.search(morph="*None*")
        tokens = WordToken.query.filter(WordToken.morph == "None").all()
        assert len(rows) == len(tokens)

    def test_search_with_combinations(self):
        rows = self.search(form="Martin", lemma="martin", pos="NOMpro", morph="")
        assert rows == [{"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"}]
        rows = self.search(lemma="martin", pos="NOMpro", morph="")
        assert {"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"} in rows
        rows = self.search(form="Martin", pos="NOMpro", morph="")
        assert {"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"} in rows
        rows = self.search(form="Martin", lemma="martin", morph="")
        assert {"form": "Martin", "lemma": "martin", "morph": "None", "pos": "NOMpro"} in rows

    def test_search_with_like_operator(self):
        rows = self.search(form="Testword\\*")
        assert rows == [{"form": "Testword*", "lemma": "testword*", "morph": "test*morph", "pos": "TEST*pos"}]

        rows = self.search(form="Testword*")
        assert rows == [
            {"form": "Testword*", "lemma": "testword*", "morph": "test*morph", "pos": "TEST*pos"},
            {"form": "TestwordFake", "lemma": "testwordFake", "morph": "testmorphFake", "pos": "TESTposFake"},
        ]

        rows = self.search(lemma="*le")
        tokens = WordToken.query.filter(WordToken.lemma.like("%le")).all()
        assert len(rows) == len(tokens)

        rows = self.search(lemma="*ai*")
        tokens = WordToken.query.filter(WordToken.lemma.like("%ai%")).all()
        assert len(rows) == len(tokens)

    def test_search_with_negation_operator(self):
        rows = self.search(form="\\!TestwordFake")
        assert rows == [{"form": "!TestwordFake", "lemma": "!testwordFake", "morph": "!testmorphFake", "pos": "!TESTposFake"}]

        rows = self.search(form="!Testword")
        tokens = WordToken.query.filter(WordToken.lemma.notlike("!Testword")).all()
        assert len(rows) == len(tokens)

        rows_neg = self.search(lemma="!*e*")
        rows = self.search(lemma="*e*")
        rows_all = self.search()
        assert len(rows_all) == len(rows) + len(rows_neg)

    def test_search_with_negation_and_like_operator(self):
        rows = self.search(form="!*e*")
        assert len(rows) > 0
        assert "e" not in "".join([r["form"] for r in rows])

    def test_search_with_or_operator(self):
        rows = self.search(form="seint|seinz|Seinz|seinte")
        rows_wildcard = self.search(form="sein*", case_insensitivity=True)
        rows_lemma = self.search(lemma="saint")
        assert rows_lemma == rows
        assert rows_wildcard == rows

        rows = self.search(lemma="m*", pos="NOMcom|NOMpro")
        assert len(rows) == 9

        rows = self.search(form="Martins|mere", lemma="martin|mere")
        assert len(rows) == 3

    def test_search_with_case_sensitivy(self):
        rows_case_sensitivity_min = self.search(form="de")
        row_case_sensitivity_maj = self.search(form="De")
        rows_case_insensitivity = self.search(form="de", case_insensitivity=True)

        def form_only(results):
            return set(line["form"] for line in results)

        assert form_only(rows_case_sensitivity_min) == {"de"}
        assert form_only(row_case_sensitivity_maj) == {"De"}
        assert form_only(rows_case_insensitivity) == {"De", "de"}

        seinz_sens = self.search(form="sein*", case_insensitivity=False)
        seinz_insens = self.search(form="sein*", case_insensitivity=True)
        assert form_only(seinz_sens) == {"seinz", "seinte", "seint"}
        assert form_only(seinz_insens) == {"seinz", "seinte", "seint", "Seinz"}
