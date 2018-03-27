#!/usr/bin/env python
import click
import unittest
from config import Config


from app import create_app, db
# from app.models import Role, User


app = None


@click.group()
@click.option('--config', default="dev")
def cli(config):
    click.echo("Loading the application")
    global app, db
    app = create_app(config)


@click.command("db-create")
def db_create():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    with app.app_context():
        db.create_all()
        db.session.commit()


@click.command("db-recreate")
def db_recreate():
    """ Recreates a local database. You probably should not use this on
    production.
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.commit()


@click.command("db-fixtures")
def db_fixtures():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    with app.app_context():
        from tests.db_fixtures import add_corpus
        add_corpus(
            "wauchier", db, with_token=True, tokens_up_to=None,
            with_allowed_lemma=True, partial_allowed_lemma=False,
            with_allowed_pos=True, partial_allowed_pos=False,
            with_allowed_morph=True)
        add_corpus(
            "floovant", db, with_token=True, tokens_up_to=None,
            with_allowed_lemma=True, partial_allowed_lemma=False,
            with_allowed_pos=True, partial_allowed_pos=False,
            with_allowed_morph=True)


@click.command("run")
def run():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    app.run()


cli.add_command(db_create)
cli.add_command(db_fixtures)
cli.add_command(db_recreate)
cli.add_command(run)


if __name__ == '__main__':
    cli()
