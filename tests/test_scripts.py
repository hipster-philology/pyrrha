""" Tests here that reuse subscripts such as function from atservices.scripts.collatinus should
just check that these function are called, not that they have the right effect. Checking the effects of these
function should be done in their respective test modules (see .test_collatinus)

"""

from unittest import TestCase
from click.testing import CliRunner
import mock
import os


from app import create_app, db
from app.cli import make_cli
from app.models.linguistic import (
    Corpus,
    WordToken,
    AllowedLemma,
    AllowedMorph,
    AllowedPOS
)
from csv import DictReader, reader


class TestGenericScript(TestCase):
    """ Tests for the generic parts of Scripts
     """

    def clear_db(self, app):
        with app.app_context():
            try:
                db.drop_all()
            except:
                pass

    def setUp(self):
        self.app = create_app("test")
        self.clear_db(self.app)

        # We create all cli to check that it does not overwrite anything
        with self.app.app_context():
            self.cli = make_cli()

        self.runner = CliRunner()

    def tearDown(self):
        self.clear_db(self.app)

    def invoke(self, commands):
        return self.runner.invoke(self.cli, ["--config", "test"] + commands)

    def test_db_create(self):
        """ Test that db is created """

        result = self.invoke(["db-create"])
        self.assertIn("Created the database", result.output)
        with self.app.app_context():
            db.session.add(Corpus(name="Corpus1"))
            db.session.commit()

            self.assertEqual(
                len(Corpus.query.all()), 1,
                "There should have been an insert"
            )

    def test_db_recreate(self):
        """ Test that db is recreated """

        with self.app.app_context():
            db.create_all()
            db.session.commit()
            db.session.add(Corpus(name="Corpus1"))
            db.session.commit()

            self.assertEqual(
                len(Corpus.query.all()), 1,
                "There should have been an insert"
            )

        result = self.invoke(["db-recreate"])

        self.assertIn("Dropped then recreated the database", result.output)

        with self.app.app_context():
            self.assertEqual(
                len(Corpus.query.all()), 0,
                "There should have been 0 insert"
            )

    def test_db_fixtures(self):
        """ Test that fixtures are put in the DB"""

        with self.app.app_context():
            db.create_all()
            db.session.commit()

        result = self.invoke(["db-fixtures"])
        self.assertIn("Loaded fixtures to the database", result.output)

        with self.app.app_context():
            self.assertEqual(
                len(Corpus.query.all()), 2,
                "Both corpus should have been inserted"
            )

    def test_run(self):
        """ Test run actually runs the application"""

        with self.app.app_context():
            db.create_all()
            db.session.commit()

        app_mock = mock.MagicMock(self.app)

        with mock.patch("app.cli.create_app", return_value=app_mock) as create_app_mock:
            result = self.invoke(["run"])

            create_app_mock.assert_called()
            app_mock.run.assert_called()


class TestCorpusScript(TestCase):
    def clear_db(self, app):
        with app.app_context():
            try:
                db.drop_all()
            except:
                pass

    def relPath(self, *paths):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            *paths
        )

    def setUp(self):
        self.app = create_app("test")

        # We create all cli to check that it does not overwrite anything
        with self.app.app_context():
            db.create_all()
            db.session.commit()
            self.cli = make_cli()

        self.runner = CliRunner()

    def tearDown(self):
        self.clear_db(self.app)

    def invoke(self, *commands):
        return self.runner.invoke(self.cli, ["--config", "test"] + list(commands))

    def pos_test(self):
        with self.app.app_context():
            POS = AllowedPOS.query.filter(AllowedPOS.corpus == 1).all()
            self.assertEqual(
                len(POS), 14,
                "There should be 14 allowed POS"
            )
            with open(self.relPath("test_scripts_data", "POS.txt")) as pos:
                self.assertEqual(
                    sorted(pos.read().strip().split(",")),
                    sorted([p.label for p in POS]),
                    "POS should be consistent with import file"
                )

    def token_test(self, result):
        self.assertIn(
            "Corpus created under the name Wauchier2 with 25 tokens",
            result.output
        )

    def morph_test(self):
        with self.app.app_context():
            morphs = AllowedMorph.query.filter(AllowedMorph.corpus == 1).all()
            self.assertEqual(
                len(morphs), 145,
                "There should be 145 allowed Morphs"
            )
            morphs = [
                m.label + " " + m.readable
                for m in morphs
            ]
            with open(self.relPath("test_scripts_data", "morph.csv")) as f:
                data = [
                    " ".join(line)
                    for line in list(reader(f, dialect="excel-tab"))[1:]
                    ]
            self.assertEqual(
                sorted(morphs), sorted(data),
                "Input allowed morphs should have been correctly inserted"
            )

    def test_corpus_import(self):
        """ Test that data ingestion works correctly"""
        result = self.invoke(
            "corpus-import",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv")
        )
        self.token_test(result)

    def test_corpus_import_POS(self):
        """ Test that data ingestion works correctly with Allowed POS"""
        result = self.invoke(
            "corpus-import",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--POS", self.relPath("test_scripts_data", "POS.txt")
        )
        self.token_test(result)
        self.pos_test()

    def test_corpus_import_morph(self):
        """ Test that data ingestion works correctly with Allowed Morph"""
        result = self.invoke(
            "corpus-import",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--morph", self.relPath("test_scripts_data", "morph.csv")
        )
        self.token_test(result)
        self.morph_test()

    def test_corpus_dump(self):
        """ Test that data export works correctly """
        """ Test that data ingestion works correctly"""
        result = self.invoke(
            "corpus-import",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv")
        )
        self.assertIn(
            "Corpus created under the name Wauchier2 with 25 tokens",
            result.output
        )
