from tests.test_selenium.base import TestBase
from tests.db_fixtures.wauchier import WauchierTokens


class TestTokenEdit(TestBase):
    """ Check token form edition, token update, token delete
    """

    def dropdown_link(self, tok_id, link):
        self.driver.get(self.url_for_with_port("main.tokens_correct", corpus_id="1"))
        self.driver_find_element_by_id("dd_t"+str(tok_id)).click()
        self.driver.implicitly_wait(2)
        dd = self.driver_find_element_by_css_selector("*[aria-labelledby='dd_t{}']".format(tok_id))
        self.element_find_element_by_partial_link_text(dd, link).click()
        self.driver.implicitly_wait(2)

    def change_form_value(self, value):
        inp = self.driver_find_element_by_css_selector("input[name='form']")
        inp.clear()
        inp.send_keys(value)

    def select_context_around(self, tok_id, max_id=len(WauchierTokens)):
        return [
            self.element_find_elements_by_tag_name(
                self.driver_find_element_by_id("token_"+str(cur)+"_row"),
                "td"
            )[5].text
            for cur in range(
                max(tok_id - 3, 0),
                min(max_id, tok_id + 3 + 2)
            )
        ]

    def get_history(self):
        self.driver_find_element_by_css_selector("a[title='Browse editions of the base text']").click()
        return [
            (
                self.element_find_element_by_css_selector(el, ".type").text.strip(),
                self.element_find_element_by_css_selector(el, ".new").text.strip(),
                self.element_find_element_by_css_selector(el, ".old").text.strip()
            )
            for el in self.driver_find_elements_by_css_selector("tbody > tr")
        ]

    def test_edition(self):
        """ [TokenEdit] Check that we are able to edit the form of a token """
        self.addCorpus("wauchier")
        # First edition
        self.dropdown_link(5, "Edit")
        self.change_form_value("oulala")
        self.driver_find_element_by_css_selector("button[type='submit']").click()
        self.driver.implicitly_wait(5)

        self.assertEqual(
            self.select_context_around(5),
            ['De seint Martin mout oulala',
             'De seint Martin mout oulala on',
             'De seint Martin mout oulala on doucement',
             'seint Martin mout oulala on doucement et',
             'Martin mout oulala on doucement et volentiers',
             'mout oulala on doucement et volentiers le',
             'oulala on doucement et volentiers le bien',
             'on doucement et volentiers le bien oïr'],
            "Context of neighbours and form have been updated"
        )
        self.assertEqual(
            self.get_history(),
            [('Edition', 'oulala', 'doit')],
            "History should be saved"
        )
        # Second edition
        self.dropdown_link(8, "Edit")
        self.change_form_value("Oulipo")
        self.driver_find_element_by_css_selector("button[type='submit']").click()
        self.driver.implicitly_wait(5)

        self.assertEqual(
            self.select_context_around(8),
            ['seint Martin mout oulala on doucement Oulipo',
             'Martin mout oulala on doucement Oulipo volentiers',
             'mout oulala on doucement Oulipo volentiers le',
             'oulala on doucement Oulipo volentiers le bien',
             'on doucement Oulipo volentiers le bien oïr',
             'doucement Oulipo volentiers le bien oïr et',
             'Oulipo volentiers le bien oïr et entendre',
             'volentiers le bien oïr et entendre ,'],
            "Context of neighbours and form have been updated"
        )
        self.assertEqual(
            self.get_history(),
            [('Edition', 'oulala', 'doit'), ('Edition', 'Oulipo', 'et')],
            "History should be saved"
        )

    def test_addition(self):
        """ [TokenEdit] Check that we are able to add tokens"""
        self.addCorpus("wauchier")
        # First edition
        self.dropdown_link(5, "Add")
        self.change_form_value("oulala")
        self.driver_find_element_by_css_selector("button[type='submit']").click()
        self.driver.implicitly_wait(5)

        self.assertEqual(
            self.select_context_around(6),
            ['De seint Martin mout doit oulala',
             'De seint Martin mout doit oulala on',
             'seint Martin mout doit oulala on doucement',
             'mout doit oulala on doucement et volentiers',
             'doit oulala on doucement et volentiers le',
             'oulala on doucement et volentiers le bien',
             'on doucement et volentiers le bien oïr',
             'doucement et volentiers le bien oïr et']
            ,
            "Context of neighbours and form have been updated"
        )
        self.assertEqual(
            self.get_history(),
            [("Addition", "oulala", "")],
            "History should be saved"
        )
        # Second edition
        self.dropdown_link(8, "Add")
        self.change_form_value("Oulipo")
        self.driver_find_element_by_css_selector("button[type='submit']").click()
        self.driver.implicitly_wait(5)

        self.assertEqual(
            self.select_context_around(8),
            ['seint Martin mout doit oulala on doucement',
             'mout doit oulala on doucement Oulipo et',
             'doit oulala on doucement Oulipo et volentiers',
             'on doucement Oulipo et volentiers le bien',
             'doucement Oulipo et volentiers le bien oïr',
             'Oulipo et volentiers le bien oïr et',
             'et volentiers le bien oïr et entendre',
             'volentiers le bien oïr et entendre ,'],
            "Context of neighbours and form have been updated"
        )
        self.assertEqual(
            self.get_history(),
            [('Addition', 'oulala', ''), ('Addition', 'Oulipo', '')],
            "History should be saved"
        )

    def test_delete(self):
        """ [TokenEdit] Check that we are able to edit the form of a token """
        self.addCorpus("wauchier")

        # Get the original value
        self.driver.get(self.url_for_with_port("main.tokens_correct", corpus_id="1"))
        original_set = self.select_context_around(5)

        # First we add a token
        self.dropdown_link(5, "Add")
        self.change_form_value("oulala")
        self.driver_find_element_by_css_selector("button[type='submit']").click()
        self.driver.implicitly_wait(5)

        self.assertEqual(
            self.select_context_around(6),
            ['De seint Martin mout doit oulala',
             'De seint Martin mout doit oulala on',
             'seint Martin mout doit oulala on doucement',
             'mout doit oulala on doucement et volentiers',
             'doit oulala on doucement et volentiers le',
             'oulala on doucement et volentiers le bien',
             'on doucement et volentiers le bien oïr',
             'doucement et volentiers le bien oïr et']
            ,
            "Context of neighbours and form have been updated after addition"
        )
        self.assertEqual(
            self.get_history(),
            [("Addition", "oulala", "")],
            "History should be saved"
        )

        # Then we remove it
        self.dropdown_link(6, "Delete")
        self.change_form_value("oulala")
        self.driver_find_element_by_css_selector("button[type='submit']").click()
        self.driver.implicitly_wait(5)

        self.assertEqual(
            self.select_context_around(5),
            original_set,
            "Context of neighbours and form have been updated after deletion"
        )
        self.assertEqual(
            self.get_history(),
            [("Addition", "oulala", ""), ("Deletion", "", "oulala")],
            "History should be saved"
        )
