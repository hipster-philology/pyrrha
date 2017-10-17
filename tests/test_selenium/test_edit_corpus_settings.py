from tests.test_selenium.base import TestBase
import random


class TestCorpusSettingsUpdate(TestBase):
    def go_to(self, mode="lemma"):
        self.addCorpus("wauchier", with_allowed_lemma=True, with_allowed_pos=True)
        self.addCorpus("floovant", with_allowed_lemma=True, with_allowed_pos=True)
        self.driver.refresh()
        self.driver.find_element_by_id("toggle_corpus_2").click()
        self.driver.find_element_by_id("overview_2").click()
        self.driver.find_element_by_css_selector(".settings-"+mode).click()
        return self.driver.find_element_by_id("allowed_values").get_attribute('value')

    def test_edit_allowed_lemma(self):
        """ Ensure editing allowed lemma works """
        # Show the dropdown
        allowed_values = self.go_to()
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
            self.writeMultiline(self.driver.find_element_by_id("allowed_values"), "\n".join(new_allowed_values))
            self.driver.find_element_by_id("submit").click()
            self.assertEqual(
                self.driver.find_element_by_id("allowed_values").get_attribute('value'),
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
            self.writeMultiline(self.driver.find_element_by_id("allowed_values"), ",".join(new_allowed_values))
            self.driver.find_element_by_id("submit").click()
            self.assertEqual(
                self.driver.find_element_by_id("allowed_values").get_attribute('value'),
                ",".join(new_allowed_values),
                "New values were saved : "+",".join(new_allowed_values)
            )

    def test_edit_allowed_morph(self):
        """ Ensure editing allowed morph works """
        #  todo
        pass