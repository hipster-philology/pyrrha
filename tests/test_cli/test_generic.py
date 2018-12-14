from unittest import TestCase

import mock
from click.testing import CliRunner

from app import db, create_app
from app.cli import make_cli
from app.models import Corpus, ControlLists


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
            cl = ControlLists(name="Corpus1")
            db.session.add(cl)
            db.session.flush()
            db.session.add(Corpus(name="Corpus1", control_lists_id=cl.id))
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
            cl = ControlLists(name="Corpus1")
            db.session.add(cl)
            db.session.flush()
            db.session.add(Corpus(name="Corpus1", control_lists_id=cl.id))
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