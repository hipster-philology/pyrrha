import click

from . import create_app, db
from .models import Corpus
from csv import DictReader


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
        """ Creates a local database
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
        """ Loads demo/tests data to the database
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
        """ Run the application in Debug Mode [Not Recommended on production]
        """
        app.run()

    @click.command("corpus-import", help="Creates a corpus named *name")
    @click.argument("name") #, help="Corpus name")
    @click.option("--corpus", "tokens", type=click.File(), required=True,
                  help="Path of the file containing the pre-annotated corpus tokens")
    @click.option("--lemma", "lemma_file", type=click.File(), help="Path of the file containing the Allowed Lemma")
    @click.option("--POS", "POS_file", type=click.File(), help="Path of the file containing the Allowed POS")
    @click.option("--morph", "morph_file", type=click.File(), help="Path of the file containing the Allowed Morphological tags")
    @click.option("-l", "--left_context", help="Number of words to keep on the left of each token")
    @click.option("-r", "--right_context", help="Number of words to keep on the right of each token")
    def corpus_ingest(
            name, tokens,
            lemma_file=None, POS_file=None, morph_file=None,
            left_context=None, right_context=None):
        lemma = None
        if lemma_file is not None:
            lemma = [
                x.replace('\r', '').strip()
                for x in lemma_file.readlines()
                if len(x.replace('\r', '').strip()) > 0
            ]

        POS = None
        if POS_file is not None:
            POS = [
                x.replace('\r', '')
                for x in POS_file.read().split(",")
                if len(x.replace('\r', '').strip()) > 0
            ]

        morph = None
        if morph_file is not None:
            morph = list(DictReader(morph_file, dialect="excel-tab"))

        token_reader = DictReader(tokens, dialect="excel-tab")

        with app.app_context():
            corpus = Corpus.create(
                name,
                word_tokens_dict=token_reader,
                allowed_lemma=lemma,
                allowed_POS=POS,
                allowed_morph=morph,
                context_left=left_context,
                context_right=right_context
            )
            click.echo(
                "Corpus created under the name {} with {} tokens".format(
                    name, corpus.tokens_count
                )
            )

    @click.command("corpus-dump")
    def corpus_dump():
        pass

    cli.add_command(db_create)
    cli.add_command(db_fixtures)
    cli.add_command(db_recreate)
    cli.add_command(run)
    cli.add_command(corpus_ingest)
    cli.add_command(corpus_dump)

    return cli
