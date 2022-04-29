from flask import url_for, current_app, Flask
from flask_testing import LiveServerTestCase
import flask_login
import os
import csv
import signal
import logging
import tempfile
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app import db, create_app
from app.models import CorpusUser, Corpus, ControlListsUser, ControlLists, Favorite, Column
from tests.db_fixtures import add_corpus, add_control_lists
from app.models import WordToken, Role, User

LIVESERVER_TIMEOUT = 1


COOKIE = None
__all__ = [
    "TestBase",
    "TokenCorrect2CorporaBase",
    "TokenCorrectBase",
    "TokensSearchThroughFieldsBase"
]


class _element_has_count(object):
    """ An expectation for checking that an element has a particular css class.

    locator - used to find the element
    returns the WebElement once it has the particular css class
    """
    def __init__(self, element, cnt: int):
        self.element = element
        self.cnt = cnt

    def __call__(self, driver):
        if self.cnt == len(driver.find_elements(By.CSS_SELECTOR, self.element)):
            return self.element
        else:
            return False


class _AuthenticatedUser(flask_login.UserMixin):
    def __init__(self, app: Flask):
        self._app = app
        self._user = None

    def __getattr__(self, item):
        if not self._user:
            self._user = User.query.get(1)
        return getattr(self._user, item)


def _force_authenticated(app):
    @app.before_request
    def set_identity():
        user = _AuthenticatedUser(app)
        flask_login.login_user(user)


class TestBase(LiveServerTestCase):
    db = db
    AUTO_LOG_IN = True

    def add_control_lists(self):
        """ Loads a control list from a folder as a public one

        :param folder_name: Name of the folder in app/configurations/langs
        """
        ControlLists.add_default_lists()
        db.session.commit()

    @staticmethod
    def element_find_element_by_id(element, *args, **kwargs):
        return element.find_element(By.ID, *args, **kwargs)

    @staticmethod
    def element_find_element_by_css_selector(element, *args, **kwargs):
        return element.find_element(By.CSS_SELECTOR, *args, **kwargs)

    @staticmethod
    def element_find_element_by_class_name(element, *args, **kwargs):
        return element.find_element(By.CLASS_NAME, *args, **kwargs)

    @staticmethod
    def element_find_element_by_link_text(element, *args, **kwargs):
        return element.find_element(By.LINK_TEXT, *args, **kwargs)

    @staticmethod
    def element_find_element_by_tag_name(element, *args, **kwargs):
        return element.find_element(By.TAG_NAME, *args, **kwargs)

    @staticmethod
    def element_find_element_by_name(element, *args, **kwargs):
        return element.find_element(By.NAME, *args, **kwargs)

    @staticmethod
    def element_find_elements_by_name(element, *args, **kwargs):
        return element.find_elements(By.NAME, *args, **kwargs)

    @staticmethod
    def element_find_element_by_partial_link_text(element, *args, **kwargs):
        return element.find_element(By.PARTIAL_LINK_TEXT, *args, **kwargs)

    @staticmethod
    def element_find_elements_by_css_selector(element, *args, **kwargs):
        return element.find_elements(By.CSS_SELECTOR, *args, **kwargs)

    @staticmethod
    def element_find_elements_by_class_name(element, *args, **kwargs):
        return element.find_elements(By.CLASS_NAME, *args, **kwargs)

    @staticmethod
    def element_find_elements_by_link_text(element, *args, **kwargs):
        return element.find_elements(By.LINK_TEXT, *args, **kwargs)

    @staticmethod
    def element_find_elements_by_tag_name(element, *args, **kwargs):
        return element.find_elements(By.TAG_NAME, *args, **kwargs)

    def driver_find_element_by_id(self, *args, **kwargs):
        return self.driver.find_element(By.ID, *args, **kwargs)

    def driver_find_element_by_css_selector(self, *args, **kwargs):
        return self.driver.find_element(By.CSS_SELECTOR, *args, **kwargs)

    def driver_find_element_by_class_name(self, *args, **kwargs):
        return self.driver.find_element(By.CLASS_NAME, *args, **kwargs)

    def driver_find_element_by_link_text(self, *args, **kwargs):
        return self.driver.find_element(By.LINK_TEXT, *args, **kwargs)

    def driver_find_element_by_tag_name(self, *args, **kwargs):
        return self.driver.find_element(By.TAG_NAME, *args, **kwargs)

    def driver_find_element_by_partial_link_text(self, *args, **kwargs):
        return self.driver.find_element(By.PARTIAL_LINK_TEXT, *args, **kwargs)

    def driver_find_elements_by_css_selector(self, *args, **kwargs):
        return self.driver.find_elements(By.CSS_SELECTOR, *args, **kwargs)

    def driver_find_elements_by_class_name(self, *args, **kwargs):
        return self.driver.find_elements(By.CLASS_NAME, *args, **kwargs)

    def driver_find_elements_by_link_text(self, *args, **kwargs):
        return self.driver.find_elements(By.LINK_TEXT, *args, **kwargs)

    def driver_find_elements_by_tag_name(self, *args, **kwargs):
        return self.driver.find_elements(By.TAG_NAME, *args, **kwargs)

    def create_app(self, config_overwrite=None):
        config_name = 'test'
        app = create_app(config_name)
        app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
        if config_overwrite:
            app.config.update(config_overwrite)

        app.DEBUG = True
        app.client = app.test_client()
        app.config.update(
            # Change the port that the liveserver listens on
            LIVESERVER_PORT=8943
        )
        if self.AUTO_LOG_IN:
            _force_authenticated(app)
        return app

    def add_favorite(self, user_id, corpora_ids):
        for corpus_id in corpora_ids:
            db.session.add(Favorite(user_id=user_id, corpus_id=corpus_id))
        db.session.commit()
        self.driver.refresh()

    def create_driver(self, options=None):
        if not options:
            options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        # options.add_experimental_option('w3c', False)

        options.set_capability("loggingPrefs", {'browser': 'ALL'})
        options.set_capability("goog:loggingPrefs", {'browser': 'ALL'})
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        return self.driver

    def pprint_log(self):
        for log in self.driver.get_log("browser"):
            print(log)

    def setUp(self):
        """Setup the test driver and create test users"""
        db.session.commit()
        db.drop_all()
        db.create_all()
        db.session.commit()

        # add default roles & admin user
        Role.add_default_roles()
        User.add_default_users()

        self.create_driver()
        self.driver.get(self.get_server_url())

    LOREM_IPSUM = """form	lemma	POS	morph
Lorem			
ipsum			
dolor			
sit			
amet			
,			
consectetur			
adipiscing			
elit			
.			"""

    def wait_until_shown(self, selector):
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, selector))
        )

    def write_lorem_impsum_tokens(self):
        self.writeMultiline(
            self.driver_find_element_by_id("tokens"),
            self.LOREM_IPSUM
        )

    def writeMultiline(self, element, text):
        """ Helper to write in multiline text

        :param element: Element in which to write the text
        :type element: selenium.webdriver.remote.webelement.WebElement
        :param text: Multiline text to write
        :return: element
        """
        self.driver.execute_script('arguments[0].value = arguments[1];', element, text)
        return element

    def _terminate_live_server(self):
        if self._process:
            try:
                os.kill(self._process.pid, signal.SIGINT)
                self._process.join(LIVESERVER_TIMEOUT)
            except Exception as ex:
                logging.error('Failed to join the live server process: %r', ex)
            finally:
                if self._process.is_alive():
                    # If it's still alive, kill it
                    self._process.terminate()

    def tearDown(self):
        self.driver.quit()

    def add_n_corpora(self, n_corpus: int, **kwargs):
        if not self.AUTO_LOG_IN:
            raise Exception("This function only works with autologin")

        user = User.query.filter(User.email == self.app.config['ADMIN_EMAIL']).first()
        for n in range(n_corpus):
            corpus = Corpus(
                name="a"*n,
                control_lists_id=1,
                columns=[
                    Column(heading="Lemma"),
                    Column(heading="POS"),
                    Column(heading="Morph"),
                    Column(heading="Similar"),
                ]
            )
            new_cu = CorpusUser(corpus=corpus, user=user, is_owner=True)
            db.session.add(corpus)
            db.session.add(new_cu)
            db.session.flush()
        db.session.commit()

    def create_temp_example_file(self):
        """Create temporary example file.

        :returns: temporary example file
        :rtype: NamedTemporaryFile
        """
        fp = tempfile.NamedTemporaryFile("w", delete=False)
        csv.writer(fp, delimiter="\t").writerows(
            (
                ("form", "lemma", "POS", "morph"),
                ("SOIGNORS", "seignor", "NOMcom", "NOMB.=p|GENRE=m|CAS=n")
            )
        )
        fp.close()
        return fp

    def addCorpus(self, corpus, *args, **kwargs):
        corpus = add_corpus(corpus.lower(), db, *args, **kwargs)
        if self.AUTO_LOG_IN and not kwargs.get("no_corpus_user", False):
            self.addCorpusUser(corpus.name, self.app.config['ADMIN_EMAIL'], is_owner=kwargs.get("is_owner", True))
        self.driver.get(self.get_server_url())
        return corpus

    def addCorpusUser(self, corpus_name, email, is_owner=False, _commit=True):
        corpus = Corpus.query.filter(Corpus.name == corpus_name).first()
        user = User.query.filter(User.email == email).first()
        new_cu = CorpusUser(corpus=corpus, user=user, is_owner=is_owner)
        self.db.session.add(new_cu)
        if _commit:
            self.db.session.commit()
        return new_cu

    def addControlLists(self, cl_name, *args, **kwargs):
        cl = add_control_lists(cl_name, db, *args, **kwargs)
        self.driver.get(self.get_server_url())
        if self.AUTO_LOG_IN and not kwargs.get("no_corpus_user", False):
            self.addControlListsUser(cl.name, self.app.config['ADMIN_EMAIL'], is_owner=kwargs.get("is_owner", True))
        for user_mail, owner in kwargs.get("for_users", []):
            self.addControlListsUser(cl.name, user_mail, is_owner=owner)
        return cl

    def addControlListsUser(self, cl_name, email, is_owner=False):
        cl = ControlLists.query.filter(ControlLists.name == cl_name).first()
        user = User.query.filter(User.email == email).first()
        new_clu = ControlListsUser(control_lists_id=cl.id, user_id=user.id, is_owner=is_owner)
        self.db.session.add(new_clu)
        self.db.session.commit()
        return new_clu

    def add_user(self, first_name, last_name, is_admin=False):
        email = "%s.%s@ppa.fr" % (first_name, last_name)
        new_user = User(confirmed=True,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        password=self.app.config['ADMIN_PASSWORD'],
                        role_id=2 if is_admin else 1)
        self.db.session.add(new_user)
        self.db.session.commit()
        return email

    def login(self, email, password):
        self.driver.get(self.url_for_with_port("account.login"))
        self.driver_find_element_by_id("email").send_keys(email)
        self.driver_find_element_by_id("password").send_keys(password)
        self.driver_find_element_by_id("submit").click()
        self.driver.implicitly_wait(5)

    def logout(self):
        try:
            self.driver.get(self.url_for_with_port("account.logout"))
            self.driver.implicitly_wait(5)
        except NoSuchElementException as e:
            pass

    def login_with_user(self, email):
        self.logout()
        self.driver.implicitly_wait(5)
        self.login(email, self.app.config['ADMIN_PASSWORD'])

    def get_admin_id(self):
        user = User.query.filter(User.email == self.app.config['ADMIN_EMAIL']).first()
        return user.id

    def admin_login(self):
        self.login_with_user(self.app.config['ADMIN_EMAIL'])

    def url_for_with_port(self, *args, **kwargs):
        with self.app.test_request_context():
            # With the test request context of the app
            kwargs['_external'] = True
            url = url_for(*args, **kwargs)  # Get the URL
            url = url.replace('://localhost/', '://localhost:%d/' % (self.app.config["LIVESERVER_PORT"]))
            return url


class TokenCorrectBase(TestBase):
    """ Base class with helpers to test token edition page """
    CORPUS = "wauchier"
    CORPUS_ID = "1"

    def assert_token_has_values(self, token, lemma=None, POS=None, morph=None):
        """ Checks that value, if not None, have been updated
        """
        if lemma:
            self.assertEqual(token.lemma, lemma, f"[Lemma] {token.lemma} should have been updated to {lemma}")
        if POS:
            self.assertEqual(token.POS, POS, f"[POS] {token.POS} should have been updated to {POS}")
        if morph:
            self.assertEqual(token.morph, morph, f"[Morph] {token.morph} should have been updated to {morph}")

    def get_badge_text_for_token(self, row, badge_class: str):
        return self.driver_find_element_by_css_selector(f"[rel='{row.get_attribute('id')}'] {badge_class}").text.strip()

    def get_similar_badge(self, row):
        return self.driver_find_element_by_css_selector(f"[rel='{row.get_attribute('id')}'] .similar-link")

    def assert_saved(self, row):
        self.assertEqual(self.get_badge_text_for_token(row, ".badge-status.badge-success"), "Saved")

    def assert_invalid_value(self, row, category):
        self.assertEqual(self.get_badge_text_for_token(row, ".badge-status.badge-danger"), f"Invalid value in {category}")

    def assert_unchanged(self, row):
        self.assertEqual(
            self.get_badge_text_for_token(row, ".badge-status.badge-danger"), "No value where changed"
        )

    def go_to_edit_token_page(self, corpus_id, as_callback=True):
        """ Go to the corpus's edit token page """

        #def callback():
        #    # Show the dropdown
        #    self.driver_find_element_by_id("toggle_corpus_corpora").click()
        #    # Click on the edit link
        #    self.driver_find_element_by_id("dropdown_link_" + corpus_id).click()
        def callback():
            self.driver.get(self.url_for_with_port("main.tokens_correct", corpus_id=corpus_id))

        if as_callback:
            return callback
        return callback()

    def _edit_nth_row_value_autocomplete(
            self, value,
            value_type="lemma",
            id_row="1", corpus_id=None,
            autocomplete_selector=None,
            additional_action_before=None,
            go_to_edit_token_page=None
    ):
        """ Helper to go to the right page and edit the first row

        :param value: Value to write
        :type value: str
        :param value_type: Type of value to edit (lemma, form, context)
        :type value_type: str
        :param id_row: ID of the row to edit
        :type corpus_id: str
        :param corpus_id: ID of the corpus to edit
        :type corpus_id: str
        :param autocomplete_selector: Selector that match an autocomplete suggestion that will be clicked
        :type autocomplete_selector: str
        :param additional_action_before: Action to perform between page reaching and token editing
        :type additional_action_before: Callable
        :param go_to_edit_token_page: Action to perform to go to the edit token page

        :returns: Token that has been edited, Content of the save link td
        :rtype: WordToken, str
        """
        # Take the first row
        row = self.driver_find_element_by_id("token_" + id_row + "_row")
        # Take the td to edit
        if value_type == "POS":
            td = self.element_find_element_by_class_name(row, "token_pos")
        elif value_type == "morph":
            td = self.element_find_element_by_class_name(row, "token_morph")
        else:
            td = self.element_find_element_by_class_name(row, "token_lemma")

        td.clear()

        action = ActionChains(self.driver)
        action.move_to_element(td).click(td).send_keys(value).pause(1).perform()

        action = ActionChains(self.driver)
        autocomplete_element = self.driver_find_element_by_css_selector(autocomplete_selector)
        save_btn = self.element_find_element_by_css_selector(row, "a.save")
        action.move_to_element(autocomplete_element).click(autocomplete_element)\
            .move_to_element(save_btn).click(save_btn).perform()

        # It's safer to wait for the AJAX call to be completed
        row = self.driver_find_element_by_id("token_" + id_row + "_row")

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[rel='token_{}_row'] .badge-status".format(id_row))
            )
        )

        return (
            self.db.session.query(WordToken).get(int(id_row)),
            self.element_find_element_by_css_selector(row, "#token_"+id_row+"_row > td a.save").text.strip(),
            row
        )

    def edith_nth_row_value(
            self, value,
            value_type="lemma",
            id_row="1", corpus_id=None,
            autocomplete_selector=None,
            additional_action_before=None,
            go_to_edit_token_page=None):
        """ Helper to go to the right page and edit the first row

        :param value: Value to write
        :type value: str
        :param value_type: Type of value to edit (lemma, form, context)
        :type value_type: str
        :param id_row: ID of the row to edit
        :type corpus_id: str
        :param corpus_id: ID of the corpus to edit
        :type corpus_id: str
        :param autocomplete_selector: Selector that match an autocomplete suggestion that will be clicked
        :type autocomplete_selector: str
        :param additional_action_before: Action to perform between page reaching and token editing
        :type additional_action_before: Callable
        :param go_to_edit_token_page: Action to perform to go to the edit token page

        :returns: Token that has been edited, Content of the save link td
        :rtype: WordToken, str
        """
        if corpus_id is None:
            corpus_id = self.CORPUS_ID

        if go_to_edit_token_page is None:
            go_to_edit_token_page = self.go_to_edit_token_page(corpus_id)
        go_to_edit_token_page()

        if additional_action_before is not None:
            additional_action_before()

        if autocomplete_selector:
            return self._edit_nth_row_value_autocomplete(
                value=value, id_row=id_row,
                value_type=value_type, autocomplete_selector=autocomplete_selector
            )

        # Take the first row
        row = self.driver_find_element_by_id("token_" + id_row + "_row")
        # Take the td to edit
        if value_type == "POS":
            td = self.element_find_element_by_class_name(row, "token_pos")
        elif value_type == "morph":
            td = self.element_find_element_by_class_name(row, "token_morph")
        else:
            td = self.element_find_element_by_class_name(row, "token_lemma")

        # Click, clear the td and send a new value
        td.click()
        td.clear()
        td.send_keys(value)

        # Save
        self.element_find_element_by_css_selector(row, "a.save").click()
        # It's safer to wait for the AJAX call to be completed
        row = self.driver_find_element_by_id("token_" + id_row + "_row")

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[rel='token_{}_row'] .badge-status".format(id_row))
            )
        )

        return (
            self.db.session.query(WordToken).get(int(id_row)),
            self.element_find_element_by_css_selector(row, "#token_"+id_row+"_row > td a.save").text.strip(),
            row
        )

    def wait_until_text(self, selector, text):
        WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element(
                selector,
                text
            )
        )

    def wait_until_count(self, element, cnt):
        WebDriverWait(self.driver, 5).until(
            _element_has_count(element, cnt)
        )

    def first_token_id(self, corpus_id):
        return self.db.session.query(WordToken.id). \
            filter_by(corpus=corpus_id).order_by(WordToken.order_id).limit(1).first()[0]

    def addCorpus(self, *args, **kwargs):
        return super(TokenCorrectBase, self).addCorpus(self.CORPUS, *args, **kwargs)

    def test_edit_token(self):
        """ [Generic] Test the edition of a token """
        self.addCorpus(with_token=True, tokens_up_to=24)
        self.driver.refresh()
        token, status_text, row = self.edith_nth_row_value("un", corpus_id=self.CORPUS_ID)
        self.assertEqual(token.lemma, "un", "Lemma should have been changed")
        self.assertEqual(status_text, "Save")
        self.assert_saved(row)

        self.assertIn("table-changed", row.get_attribute("class"))
        self.driver.refresh()
        row = self.driver_find_element_by_id("token_1_row")
        self.assertIn("table-changed", row.get_attribute("class"))


class TokenCorrect2CorporaBase(TokenCorrectBase):
    def addCorpus(self, *args, **kwargs):
        super(TokenCorrectBase, self).addCorpus("wauchier", *args, **kwargs)
        super(TokenCorrectBase, self).addCorpus("floovant", *args, **kwargs)


class TokensSearchThroughFieldsBase(TestBase):
    CORPUS_ID = 1

    def go_to_search_tokens_page(self, corpus_id, as_callback=True):
        """ Go to the corpus's search token page """

        def callback():
            # Show the dropdown
            self.driver.get(self.url_for_with_port("main.tokens_search_through_fields", corpus_id=corpus_id))
            self.driver.implicitly_wait(1)

        if as_callback:
            return callback
        return callback()

    def fill_filter_row(self, form, lemma, pos, morph):
        # Take the first row
        row = self.driver_find_element_by_id("filter_row")

        for field_name, field_value in (("lemma", lemma), ("form", form), ("POS", pos), ("morph", morph)):
            # Take the td to edit
            td = self.element_find_element_by_name(row, field_name)
            # Click, clear the td and send a new value
            if field_value is None:
                field_value = 'None'
            td.click(), td.clear(), td.send_keys(field_value)

    def setUp(self):
        super(TokensSearchThroughFieldsBase, self).setUp()
        self.addCorpus(corpus="wauchier")
        new_token = WordToken(
            corpus=TokensSearchThroughFieldsBase.CORPUS_ID,
            order_id=1,
            form="Testword*",
            lemma="testword*",
            POS="TEST*pos",
            morph="test*morph",
            left_context="This is a left context",
            right_context="This is a left context"
        )
        db.session.add(new_token)
        new_token = WordToken(
            corpus=TokensSearchThroughFieldsBase.CORPUS_ID,
            order_id=2,
            form="TestwordFake",
            lemma="testwordFake",
            POS="TESTposFake",
            morph="testmorphFake",
            left_context="This is a left context",
            right_context="This is a left context"
        )
        db.session.add(new_token)

        new_token = WordToken(
            corpus=TokensSearchThroughFieldsBase.CORPUS_ID,
            order_id=3,
            form="!TestwordFake",
            lemma="!testwordFake",
            POS="!TESTposFake",
            morph="!testmorphFake",
            left_context="This is a left context",
            right_context="This is a left context"
        )
        db.session.add(new_token)
        db.session.commit()

    def search(self, form="", lemma="", pos="", morph=""):

        self.go_to_search_tokens_page(TokensSearchThroughFieldsBase.CORPUS_ID, as_callback=False)

        self.fill_filter_row(form, lemma, pos, morph)

        self.driver_find_element_by_id("submit_search").click()

        result = []

        def get_field(row, f):
            return self.element_find_element_by_class_name(row, f).text.strip()

        # load each page to get the (partials) result tables
        # pagination = self.driver_find_element_by_class_name("pagination").find_elements_by_tag_name("a")
        pagination = self.element_find_elements_by_tag_name(
            self.driver_find_element_by_class_name("pagination"),
            "a"
        )
        self.driver.save_screenshot("first.results.png")
        for page_index in range(0, len(pagination)):
            # self.driver_find_element_by_class_name("pagination").find_elements_by_tag_name("a")[page_index].click()
            self.element_find_elements_by_tag_name(
                self.driver_find_element_by_class_name("pagination"),
                "a"
            )[page_index].click()

            # find the result in the result table
            res_table = self.element_find_element_by_tag_name(
                self.driver_find_element_by_id("result_table"),
                "tbody"
            )
            try:
                rows = self.element_find_elements_by_tag_name(res_table, "tr")

                for row in rows:
                    result.append({
                        "form": self.element_find_elements_by_tag_name(row, "td")[1].text.strip(),
                        "lemma": get_field(row, "token_lemma"),
                        "morph": get_field(row, "token_morph"),
                        "pos": get_field(row, "token_pos"),
                    })
            except NoSuchElementException as e:
                print(e)

        return result
