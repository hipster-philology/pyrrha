import click
import os

from . import create_app, db
from .models import (
    Corpus,
    AllowedPOS,
    AllowedLemma,
    AllowedMorph,
    WordToken
)
from .main.views.utils import create_input_format_convertion


app = None


DEFAULT_FILENAMES = {
    "tokens": "tokens.csv",
    "POS": "allowed_pos.txt",
    "lemma": "allowed_lemma.txt",
    "morph": "allowed_morph.csv"
}

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

        if lemma_file is not None:
            lemma_file = lemma_file.read()

        if POS_file is not None:
            POS_file = POS_file.read()

        token_reader, lemma, morph, POS = create_input_format_convertion(
            tokens, lemma_file, morph_file, POS_file
        )

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

    @click.command("corpus-list", help="Shows a list of corpus and their ID")
    def corpus_list():
        scheme = "{}\t| {}"   # Could use a 0 filling to allow for a nicer output
        with app.app_context():
            click.echo(scheme.format("ID", "Name"))
            for corpus in Corpus.query.all():
                click.echo(scheme.format(corpus.id, corpus.name))

    @click.command("corpus-dump", help="Dump corpus identified by {corpus} id. Use corpus-list to have a list of IDs")
    @click.argument("corpus", type=click.INT)
    @click.option("--path", type=click.Path(), required=True, help="Path where the corpus should be saved")
    def corpus_dump(corpus, path):
        with app.app_context():
            if not os.path.exists(path):
                os.makedirs(path)
            corpus = Corpus.query.get(corpus)

            # Check that the corpus exists
            if not corpus:
                click.echo("Corpus not found")
                return

            with open(os.path.join(path, DEFAULT_FILENAMES["tokens"]), "w") as file:
                file.write(WordToken.to_input_format(
                    WordToken.query.filter(WordToken.corpus == corpus.id)
                ))
                click.echo("--- Tokens dumped")
            with open(os.path.join(path, DEFAULT_FILENAMES["lemma"]), "w") as file:
                file.write(AllowedLemma.to_input_format(
                    AllowedLemma.query.filter(AllowedLemma.corpus == corpus.id)
                ))
                click.echo("--- Allowed Lemma Values dumped")
            with open(os.path.join(path, DEFAULT_FILENAMES["morph"]), "w") as file:
                file.write(AllowedMorph.to_input_format(
                    AllowedMorph.query.filter(AllowedMorph.corpus == corpus.id)
                ))
                click.echo("--- Allowed Morphological Values dumped")
            with open(os.path.join(path, DEFAULT_FILENAMES["POS"]), "w") as file:
                file.write(AllowedPOS.to_input_format(
                    AllowedPOS.query.filter(AllowedPOS.corpus == corpus.id)
                ))
                click.echo("--- Allowed POS Values dumped")

    cli.add_command(db_create)
    cli.add_command(db_fixtures)
    cli.add_command(db_recreate)
    cli.add_command(run)
    cli.add_command(corpus_ingest)
    cli.add_command(corpus_dump)
    cli.add_command(corpus_list)

    return cli
