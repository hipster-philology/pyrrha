from unittest import TestCase

import mock
from click.testing import CliRunner

from app import db, create_app
from app.cli import make_cli
from app.models import Corpus, ControlLists, Role, User


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

    def test_edit_user_should_get_user_by_email(self):
        """Test that user gets identified by email"""

        TEST_USER_ID = 1
        TEST_USER_EMAIL = 'test@example.org'

        with self.app.app_context():
            db.create_all()
            Role.add_default_roles()
            db.session.commit()
        
        with self.app.app_context():
            role_user = Role.query.filter(Role.name == 'User').first()
            unconfirmed_user = User(
                id=TEST_USER_ID,
                first_name='test',
                last_name='test',
                email=TEST_USER_EMAIL,
                password='password',
                confirmed=False,
                role=role_user,
            )
            db.session.add(unconfirmed_user)
            db.session.commit()

        with self.app.app_context():
            role_user = Role.query.filter(Role.name == 'User').first()
            self.assertIsNotNone(role_user)
            user = User.query.get(TEST_USER_ID)
            self.assertEqual(user.role_id, role_user.id)
        
        response = self.invoke(["edit-user", f"{TEST_USER_EMAIL}", "--role", "Administrator"])

        with self.app.app_context():
            role_administrator = Role.query.filter(Role.name == 'Administrator').first()
            self.assertIsNotNone(role_administrator)
            user = User.query.get(TEST_USER_ID)
            self.assertEqual(user.role_id, role_administrator.id)

    def test_edit_user_should_set_role_to_administrator(self):
        """Test that user has role administrator"""

        TEST_USER_ID = 1

        with self.app.app_context():
            db.create_all()
            Role.add_default_roles()
            db.session.commit()
        
        with self.app.app_context():
            role_user = Role.query.filter(Role.name == 'User').first()
            unconfirmed_user = User(
                id=TEST_USER_ID,
                first_name='test',
                last_name='test',
                email='test@example.org',
                password='password',
                confirmed=False,
                role=role_user,
            )
            db.session.add(unconfirmed_user)
            db.session.commit()

        with self.app.app_context():
            role_user = Role.query.filter(Role.name == 'User').first()
            self.assertIsNotNone(role_user)
            user = User.query.get(TEST_USER_ID)
            self.assertEqual(user.role_id, role_user.id)
        
        response = self.invoke(["edit-user", f"{TEST_USER_ID}", "--role", "Administrator"])

        with self.app.app_context():
            role_administrator = Role.query.filter(Role.name == 'Administrator').first()
            self.assertIsNotNone(role_administrator)
            user = User.query.get(TEST_USER_ID)
            self.assertEqual(user.role_id, role_administrator.id)


    def test_edit_user_should_confirm_user(self):
        """Test that user is confirmed"""

        TEST_USER_ID = 1

        with self.app.app_context():
            db.create_all()
            Role.add_default_roles()
            db.session.commit()
        
        with self.app.app_context():
            role_user = Role.query.filter(Role.name == 'User').first()
            unconfirmed_user = User(
                id=TEST_USER_ID,
                first_name='test',
                last_name='test',
                email='test@example.org',
                password='password',
                confirmed=False,
                role=role_user,
            )
            db.session.add(unconfirmed_user)
            db.session.commit()

        with self.app.app_context():
            user = User.query.get(TEST_USER_ID)
            self.assertFalse(user.confirmed)

        response = self.invoke(["edit-user", f"{TEST_USER_ID}", "--confirm-mail"])

        with self.app.app_context():
            user = User.query.get(TEST_USER_ID)
            self.assertTrue(user.confirmed)

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
