#!/usr/bin/env python
from flask_script import Manager
from config import Config
from tests.db_fixtures import add_corpus

from app import create_app, db
# from app.models import Role, User


app = create_app("dev")
manager = Manager(app)


@manager.command
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def create_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.create_all()
    db.session.commit()


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@manager.command
def fixtures_to_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    add_corpus(
        "wauchier", db, with_token=True, tokens_up_to=None,
        with_allowed_lemma=True, partial_allowed_lemma=False,
        with_allowed_pos=True, partial_allowed_pos=False)
    add_corpus(
        "floovant", db, with_token=True, tokens_up_to=None,
        with_allowed_lemma=True, partial_allowed_lemma=False,
        with_allowed_pos=True, partial_allowed_pos=False)


@manager.command
def test():
    """ Run tests locally
    """
    import tests.__main__ as tests
    tests.unittest.main()


@manager.command
def run():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    app.run()

if __name__ == '__main__':
    manager.run()
