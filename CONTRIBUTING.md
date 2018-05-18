How to contribute
=================

## Writing an issue

By writing an issue, you're already contributing a lot. Though, if you want to really help us, try to be clear when you 
write this issue : state your machine, the version of the app you are using (git sha and branch, pip version if available),
give us the specific error and means to replicate it (attach any corpus sample that might be of interest. You do not need to 
give us the full data!), and ensure to give a proper pip freeze result, just in case.

Try to write your issue (if this is a bug you describing) by adding separation such as

```markdown
## Context of the issue
Description of steps to take to replicate the issue

## Expected output
Output that would normally happen

## Effective output
Output that you have

## Error code (if applicable)

## Environment
Pip freeze, ubuntu version, anything useful
```

Think about running your app in debug mode if you can ! That will help us with a nice debug info !

## Running tests

To run tests, you will need [chrome-webdriver](https://chromedriver.storage.googleapis.com/index.html?path=2.32/)

### Install webdriver on Linux

**Note:** this script is also available as `chromedriver.sh` in the root directory of this repository

```shell
wget -N https://chromedriver.storage.googleapis.com/2.36/chromedriver_linux64.zip -P ~/
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
sudo mv -f ~/chromedriver /usr/local/share/
sudo chmod +x /usr/local/share/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
```

### Run the tests

To run the tests, you simply need run `nose2` at the root of the pandora-postcorrect-app folder. 

## Writing a test

For writing and running test, we recommend you install chromium-webdriver (`apt-get install chromium-chromedriver`). 
Make sure to have the full requirements.txt installed (this includes packages needed to run the tests)

### Integration tests

If you want to write a test that would follow human behaviour, you will need to write a test using selenium. This kind of
tests are in the module `tests.test_selenium`.

#### New class of test

Class for integration tests should inherit from `tests.test_selenium.base.TestBase`. This class comes with a `self.driver` property to use Selenium
It also comes with a `self.writeMultiline(element, text)` method that will allow to write multiline and tab-including strings to element in the browser.

- A class must have a name starting with `Test` and should be camelCase after that.
- A class must have a doc string explaing what it does
- A class must have at least one method starting with `test_`

**e.g.**:

```python
class TestCorpusRegistration(TestBase):
    """ Test creation of Corpus """
    def test_registration(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """
        pass
```

#### New method of test

A new test method should be added to the correct class regarding scope of each class.

- A test method must have a name starting with `test_` and should be snake case (Test Edition of Token -> `test_edition_of_token`).
- A class must have a doc string explaining what it does
- A class must have at least one self.assertEqual, self.assertCount, etc.
- If you need to create fixtures (fake data), add it to `tests.fixtures`
- A test should prefer to test new or updated database values using direct models queries instead of DOM parsing

**e.g.**:

```python
    def test_registration(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """

        # Click register menu link
        self.driver.find_element_by_id("new_corpus_link").click()
        # Just make sure we wait long enough if needed
        self.driver.implicitly_wait(15)

        # Fill in registration form
        # Click on #corpusName, write the value in Variable CORPUS_NAME
        self.driver.find_element_by_id("corpusName").send_keys(CORPUS_NAME)

        # Because we have tabs and new lines, here we find #tokens but we fill it with
        #   the TestBase method writeMultiline that takes an element and a string
        self.writeMultiline(self.driver.find_element_by_id("tokens"), CORPUS_DATA)

        # We click on submit
        self.driver.find_element_by_id("submit").click()

        # We make sure things are posted by waiting
        self.driver.implicitly_wait(15)

        # We check the current URI
        self.assertIn(
            url_for('main.corpus_new'), self.driver.current_url,
            "Result page is the corpus new page"
        )

        # And now we check the result of such a POST
        self.assertEqual(
            db.session.query(Corpus).filter(Corpus.name == CORPUS_NAME).count(), 1,
            "There should be one well named corpus"
        )
        corpus = db.session.query(Corpus).filter(Corpus.name == CORPUS_NAME).first()
        tokens = db.session.query(WordToken).filter(WordToken.corpus == corpus.id)
        self.assertEqual(tokens.count(), 25, "There should be 25 tokens")

        saint = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "saint"))
        self.assertEqual(saint.count(), 1, "There should be the saint lemma")
        saint = saint.first()
        self.assertEqual(saint.form, "seint", "It should be correctly saved")
        self.assertEqual(saint.label_uniform, "saint", "It should be correctly saved and unidecoded")
        self.assertEqual(saint.POS, "ADJqua", "It should be correctly saved with POS")
        self.assertEqual(saint.morph, None, "It should be correctly saved with morph")

        oir = db.session.query(WordToken).filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "öir"))
        self.assertEqual(oir.count(), 1, "There should be the oir lemma")
        oir = oir.first()
        self.assertEqual(oir.form, "oïr", "It should be correctly saved")
        self.assertEqual(oir.label_uniform, "oir", "It should be correctly saved and unidecoded")
        self.assertEqual(oir.POS, "VERinf", "It should be correctly saved with POS")
        self.assertEqual(oir.morph, None, "It should be correctly saved with morph")
```

### Tests about models

Test about models should be written as submodules or packages of `test.test_models`

#### New class of test

Class for integration tests should inherit from `tests.test_models.base.TestBase`. This class comes with a `self.db` property to use the database and
a `self.client` to connect to the flask test client. See [Flask Documentation](http://flask.pocoo.org/docs/0.12/testing/#the-first-test) for more information

- A class must have a name starting with `Test` and should be camelCase after that.
- A class must have a doc string explaing what it does
- A class must have at least one method starting with `test_`

**e.g.**:

```python
class TestCorpusRegistration(TestBase):
    """ Test creation of Corpus """
    def test_registration(self):
        """
        Test that a user can create a corpus and that this corpus has its data well recorded
        """
        pass
```

#### New method of test

A new test method should be added to the correct class regarding scope of each class.

- A test method must have a name starting with `test_` and should be snake case (Test Edition of Token -> `test_edition_of_token`).
- A class must have a doc string explaing what it does
- A class must have at least one self.assertEqual, self.assertCount, etc.
- If you need to create fixtures (fake data), add it to `tests.fixtures`
- A test should prefer to test new or updated database values using direct models queries instead of DOM parsing

### Tests of routes or web API

Test about API should be written as submodules or packages of `test.test_requesting`

#### New class of test

Class for integration tests should inherit from `tests.test_requesting.base.TestBase`. This class comes with a `self.db` property to use the database and
a `self.client` to connect to the flask test client. See [Flask Documentation](http://flask.pocoo.org/docs/0.12/testing/#the-first-test) for more information

- A class must have a name starting with `Test` and should be camelCase after that.
- A class must have a doc string explaing what it does
- A class must have at least one method starting with `test_`

**e.g.**:

```python
class TestNavigation(TestBase):
    """ Test creation of Corpus """
    def test_read_home_page(self):
```

#### New method of test

A new test method should be added to the correct class regarding scope of each class.

- A test method must have a name starting with `test_` and should be snake case (Test Edition of Token -> `test_edition_of_token`).
- A class must have a doc string explaing what it does
- A class must have at least one self.assertEqual, self.assertCount, etc.
- If you need to create fixtures (fake data), add it to `tests.fixtures`
- A test should prefer to test new or updated database values using direct models queries instead of DOM parsing
- Prefer the usage of `flask.url_for` instead of hardcoded URIs in any `self.client` request

**e.g.**:

```python
class TestNavigation(TestBase):
    """ Test creation of Corpus """
    def test_read_home_page(self):
        """ Test that the home page is accessible """
        response = self.client.get(url_for("main.index"))
        self.assertEqual(response.status_code, 200, "Display of index should work")
```

## Fixtures and getting fixtures

Fixtures are mock-up data that can be drawn from real life corpora. To generate a corpora's 
fixture you can simply got to `/corpus/<id>/fixtures` and you will be able to get 
python code printed to your page.

To browse the application with data sample, you can run `python manage.py db-fixtures` after
having created or recreated the database.

You can contribute fixtures by adding a corpus in db_fixtures and fixtures following the 
example of the Floovant or Wauchier corpus. 
