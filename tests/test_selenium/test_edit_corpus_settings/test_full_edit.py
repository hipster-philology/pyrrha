import random

from tests.test_selenium.base import TestBase


class TestCorpusSettingsUpdate(TestBase):
    def go_to(self, mode="lemma"):
        morph = False
        if mode == "morph":
            morph = True
        self.addControlLists("wauchier", with_allowed_lemma=True, partial_allowed_lemma=False,
                             partial_allowed_pos=False, partial_allowed_morph=False,
                             with_allowed_pos=True, with_allowed_morph=morph)
        self.addControlLists("floovant", with_allowed_lemma=True, partial_allowed_lemma=False,
                             partial_allowed_pos=False, partial_allowed_morph=False,
                             with_allowed_pos=True, with_allowed_morph=morph)
        self.driver.refresh()
        self.driver_find_element_by_id("toggle_controllists").click()
        self.driver_find_element_by_id("dropdown_link_cl_2").click()
        self.driver_find_element_by_css_selector("header > a").click()
        self.driver_find_element_by_css_selector(".settings-"+mode).click()
        return self.driver_find_element_by_id("allowed_values").get_attribute('value')

    def test_edit_allowed_lemma(self):
        """ Ensure editing allowed lemma works """
        # Show the dropdown
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
        self.assertEqual(allowed_values, original_lemma, "Original allowed lemma should be correctly listed")
        for i in range(20):
            new_allowed_values = list(random.sample(allowed_values.split(), i))
            self.writeMultiline(self.driver_find_element_by_id("allowed_values"), "\n".join(new_allowed_values))
            self.driver_find_element_by_id("submit").click()
            self.assertEqual(
                self.driver_find_element_by_id("allowed_values").get_attribute('value'),
                "\n".join(new_allowed_values),
                "New values were saved : "+",".join(new_allowed_values)
            )

    def test_edit_allowed_POS(self):
        """ Ensure editing allowed POS works """
        # Show the dropdown
        allowed_values = self.go_to(mode="POS")
        original_lemma = "ADVgen,VERcjg,NOMcom,ADJord,ADJqua,ADVneg,CONsub,DETcar,NOMpro,PRE,PRE.DETdef,PROdem," \
                         "PROper,PROrel"
        self.assertEqual(allowed_values, original_lemma, "Original allowed lemma should be correctly listed")
        for i in range(20):
            new_allowed_values = list(random.sample(allowed_values.split(","), original_lemma.count(",")))
            self.writeMultiline(self.driver_find_element_by_id("allowed_values"), ",".join(new_allowed_values))
            self.driver_find_element_by_id("submit").click()
            self.assertEqual(
                self.driver_find_element_by_id("allowed_values").get_attribute('value'),
                ",".join(new_allowed_values),
                "New values were saved : "+",".join(new_allowed_values)
            )

    def test_edit_allowed_morph(self):
        """ Ensure editing allowed morph works """
        #  todo
        allowed_values = self.go_to(mode="morph")
        expected = "label\treadable\n_\tpas de morphologie\nDEGRE=-\tnon applicable"
        expected_end = "PERS.=3|NOMB.=p|GENRE=m|CAS=r\t3e personne pluriel masculin régime"
        self.assertEqual(allowed_values[:len(expected)], expected)
        self.assertEqual(allowed_values[-len(expected_end):], expected_end)

        added = "\nFOO\tBAR"

        self.writeMultiline(
            self.driver_find_element_by_id("allowed_values"),
            allowed_values+added
        )
        self.driver_find_element_by_id("submit").click()

        allowed_values = self.driver_find_element_by_id("allowed_values").get_attribute('value')
        self.assertEqual(allowed_values[:len(expected)], expected)
        self.assertEqual(allowed_values[-len(expected_end+added):], expected_end+added)