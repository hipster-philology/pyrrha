import click

from . import create_app, db


app = None


def make_cli():
    """ Creates a Command Line Interface for everydays tasks

    :return: Click groum
    """
    @click.group()
    @click.option('--config', default="dev")
    def cli(config):
        """ Generates the client"""
        click.echo("Loading the application")
        global app
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
            click.echo("Created the database")

    @click.command("db-recreate")
    def db_recreate():
        """ Recreates a local database. You probably should not use this on
        production.
        """
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.commit()
            click.echo("Dropped then recreated the database")

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
            click.echo("Loaded fixtures to the database")

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

    return cli
