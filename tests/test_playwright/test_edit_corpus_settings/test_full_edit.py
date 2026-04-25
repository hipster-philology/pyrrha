"""Tests for the ControlLists full-edit (textarea rewrite) view."""
import random
import pytest

from tests.test_playwright.base import Helpers


class TestCorpusSettingsUpdate(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def go_to(self, mode="lemma"):
        morph = mode == "morph"
        self.addControlLists(
            "wauchier",
            with_allowed_lemma=True,
            partial_allowed_lemma=False,
            partial_allowed_pos=False,
            partial_allowed_morph=False,
            with_allowed_pos=True,
            with_allowed_morph=morph,
        )
        self.addControlLists(
            "floovant",
            with_allowed_lemma=True,
            partial_allowed_lemma=False,
            partial_allowed_pos=False,
            partial_allowed_morph=False,
            with_allowed_pos=True,
            with_allowed_morph=morph,
        )
        self.page.reload()
        self.page.locator("#toggle_controllists").click()
        self.page.locator("#dropdown_link_cl_2").click()
        self.page.locator("header > a").click()
        self.page.locator(f".settings-{mode}").click()
        self.page.wait_for_load_state("networkidle")
        return self.page.locator("#allowed_values").input_value()

    def test_edit_allowed_lemma(self):
        allowed_values = self.go_to("lemma")
        original_lemma = """escouter
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
        assert allowed_values == original_lemma

        for i in range(20):
            new_values = list(random.sample(allowed_values.split(), i))
            self.page.locator("#allowed_values").fill("\n".join(new_values))
            self.page.locator("#submit").click()
            self.page.wait_for_load_state("networkidle")
            assert self.page.locator("#allowed_values").input_value() == "\n".join(new_values)

    def test_edit_allowed_POS(self):
        allowed_values = self.go_to(mode="POS")
        original_pos = "ADVgen,VERcjg,NOMcom,ADJord,ADJqua,ADVneg,CONsub,DETcar,NOMpro,PRE,PRE.DETdef,PROdem,PROper,PROrel"
        assert allowed_values == original_pos

        for i in range(20):
            new_values = list(random.sample(allowed_values.split(","), original_pos.count(",")))
            self.page.locator("#allowed_values").fill(",".join(new_values))
            self.page.locator("#submit").click()
            self.page.wait_for_load_state("networkidle")
            assert self.page.locator("#allowed_values").input_value() == ",".join(new_values)

    def test_edit_allowed_morph(self):
        allowed_values = self.go_to(mode="morph")
        expected_start = "label\treadable\n_\tpas de morphologie\nDEGRE=-\tnon applicable"
        expected_end = "PERS.=3|NOMB.=p|GENRE=m|CAS=r\t3e personne pluriel masculin régime"
        assert allowed_values[: len(expected_start)] == expected_start
        assert allowed_values[-len(expected_end) :] == expected_end

        added = "\nFOO\tBAR"
        self.page.locator("#allowed_values").fill(allowed_values + added)
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        new_values = self.page.locator("#allowed_values").input_value()
        assert new_values[: len(expected_start)] == expected_start
        assert new_values[-len(expected_end + added) :] == expected_end + added
