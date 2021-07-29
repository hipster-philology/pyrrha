import click
import os

from app.models import Role, User, ControlLists
from . import create_app, db
from .models import (
    Corpus,
    Column,
    AllowedPOS,
    AllowedLemma,
    AllowedMorph,
    WordToken
)
from app.utils.forms import create_input_format_convertion

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

    @click.command("edit-user")
    @click.argument("user_id_or_email")
    @click.option("--confirm-mail", "is_confirmed", is_flag=True,
                  help="Confirm mail address.")
    @click.option("--role", "role", type=click.Choice(['User', 'Administrator'], case_sensitive=False), required=False,
                  help="Set role.")
    def edit_user(user_id_or_email, is_confirmed=False, role=None):
        """Edits a user by id or email
        """
        with app.app_context():
            try:
                int(user_id_or_email)
                user_id = user_id_or_email
            except ValueError:
                lookup = User.query.filter(User.email == user_id_or_email).first()
                user_id = lookup.id if lookup else None

            if not user_id:
                click.echo(f"User with email '{user_id_or_email}' not found.")

            user = User.query.filter(User.id == user_id).first()
            if not user:
                click.echo(f"User with id '{user_id}' not found.")
                return
            
            if is_confirmed and not user.confirmed:
                User.query.filter(User.id == user_id).update({User.confirmed: True})
                db.session.commit()
            
            if role is not None:
                new_role = Role.query.filter(Role.name == role.title()).first()
                if user.role_id != new_role.id:      
                    User.query.filter(User.id == user_id).update({User.role_id: new_role.id})
                    db.session.commit()

    @click.command("db-create")
    def db_create():
        """ Creates a local database
        """
        with app.app_context():
            db.create_all()

            Role.add_default_roles()
            User.add_default_users()
            ControlLists.add_default_lists()

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

            Role.add_default_roles()
            User.add_default_users()
            ControlLists.add_default_lists()

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

    @click.command("corpus-from-file", help="Creates a corpus based on file."
                                         "First parameter is the name")
    @click.argument("name")
    @click.option("--corpus", "tokens", type=click.File(), required=True,
                  help="Path of the file containing the pre-annotated corpus tokens")
    @click.option("--lemma", "lemma_file", type=click.File(), help="Path of the file containing the Allowed Lemma")
    @click.option("--POS", "POS_file", type=click.File(), help="Path of the file containing the Allowed POS")
    @click.option("--morph", "morph_file", type=click.File(),
                  help="Path of the file containing the Allowed Morphological tags")
    @click.option("--left", help="Number of words to keep on the left of each token")
    @click.option("--right", help="Number of words to keep on the right of each token")
    def corpus_ingest(
            name, tokens,
            lemma_file=None, POS_file=None, morph_file=None,
            left=None, right=None):

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
                context_left=left,
                context_right=right,
                columns=[
                    Column(heading="Lemma"),
                    Column(heading="POS"),
                    Column(heading="Morph"),
                    Column(heading="Similar"),
                ]
            )
            db.session.commit()
            click.echo(
                "Corpus created under the name {} with {} tokens".format(
                    name, corpus.tokens_count
                )
            )

    @click.command("corpus-from-dir",
                   help="Create a corpus based on a folder. File with following names ({}) "
                        "should be in the folder. First parameter is the name".format(
                            ", ".join(DEFAULT_FILENAMES.values())))
    @click.argument("name")
    @click.option("--path", type=click.Path(), required=True,
                  help="Path of the file containing the pre-annotated corpus tokens")
    @click.option("--left", help="Number of words to keep on the left of each token")
    @click.option("--right", help="Number of words to keep on the right of each token")
    def corpus_import(name, path, left=None, right=None):
        # Set the list of paths
        token_path = os.path.join(path, DEFAULT_FILENAMES["tokens"])
        morph_path = os.path.join(path, DEFAULT_FILENAMES["morph"])
        lemma_path = os.path.join(path, DEFAULT_FILENAMES["lemma"])
        pos_path = os.path.join(path, DEFAULT_FILENAMES["POS"])

        # Set the default values
        tokens, lemma, POS, morph = None, None, None, None

        # If the token file does not exist, let's leave this city
        if not os.path.isfile(token_path):
            click.echo("Corpus not found")
            return

        tokens = open(token_path)
        if os.path.isfile(morph_path):
            morph = open(morph_path)
            click.echo("-- Found Morphological Allowed Values")

        if os.path.isfile(lemma_path):
            with open(lemma_path) as file:
                lemma = file.read()
            click.echo("-- Found Lemma Allowed Values")

        if os.path.isfile(pos_path):
            with open(pos_path) as file:
                POS = file.read()
            click.echo("-- Found POS Allowed Values")

        input_tokens, allowed_lemma, allowed_morph, allowed_POS = create_input_format_convertion(
            tokens, lemma, morph, POS
        )
        try:
            with app.app_context():
                data = Corpus.create(
                    name=name, word_tokens_dict=input_tokens,
                    allowed_lemma=allowed_lemma, allowed_morph=allowed_morph,
                    allowed_POS=allowed_POS, context_left=left,
                    context_right=right,
                    columns=[
                        Column(heading="Lemma"),
                        Column(heading="POS"),
                        Column(heading="Morph"),
                        Column(heading="Similar"),
                    ]
                )
                db.session.commit()
                click.echo(data.control_lists_id)
                click.echo("Corpus '{}' (ID : {}) created ".format(
                    name,
                    data.id
                ))
        except Exception as E:
            click.echo(str(E))

        tokens.close()
        if morph:
            morph.close()

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
                    AllowedLemma.query.filter(AllowedLemma.control_list == corpus.control_lists_id)
                ))
                click.echo("--- Allowed Lemma Values dumped")
            with open(os.path.join(path, DEFAULT_FILENAMES["morph"]), "w") as file:
                file.write(AllowedMorph.to_input_format(
                    AllowedMorph.query.filter(AllowedMorph.control_list == corpus.control_lists_id)
                ))
                click.echo("--- Allowed Morphological Values dumped")
            with open(os.path.join(path, DEFAULT_FILENAMES["POS"]), "w") as file:
                file.write(AllowedPOS.to_input_format(
                    AllowedPOS.query.filter(AllowedPOS.control_list == corpus.control_lists_id)
                ))
                click.echo("--- Allowed POS Values dumped")

    @cli.command("db-upgrade", help="Do small migrations")
    @click.argument("migration_name",
              type=click.Choice(['controllist-markdown', 'add-columns'], case_sensitive=False))
    def db_add_table(migration_name):
        columns = {
            "controllist-markdown": [
                ("control_lists", (db.Column("notes", db.Text),))
            ]
        }

        def add_column(engine, table_name, column):
            column_name = column.compile(dialect=engine.dialect)
            column_type = column.type.compile(engine.dialect)
            engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type))
            return column_name, column_type

        migration_name = migration_name.lower()
        with app.app_context():
            if migration_name == "add-columns":
                import app.models as tables
                Model = getattr(tables, "Column", None)
                if Model:
                    with app.app_context():
                        Model.__table__.create(db.session.bind, checkfirst=True)
                for corpus in Corpus.query.all():
                    corpus.columns = [
                        Column(corpus_id=corpus.id, heading="Lemma"),
                        Column(corpus_id=corpus.id, heading="POS"),
                        Column(corpus_id=corpus.id, heading="Morph"),
                        Column(corpus_id=corpus.id, heading="Similar"),
                    ]
                return
            if migration_name in columns:
                changes = []
                for table, columns in columns[migration_name]:
                    for column in columns:
                        name, _ = add_column(db.engine, table, column)
                        changes.append(str(name))

                click.echo(
                    "Success: {} columns added [{}]".format(
                        len(changes),
                        ", ".join(changes))
                )

    cli.add_command(db_create)
    
    @click.command("db-add", help="Small tool to add new table instead of migrating")
    @click.argument("model")
    def db_add_table(model):
        import app.models as tables
        Model = getattr(tables, model, None)
        if Model:
            with app.app_context():
                Model.__table__.create(db.session.bind, checkfirst=True)
        else:
            click.echo("Model not found.")
            click.echo(
                "Model available: " + ", ".join(sorted([
                    x for x in dir(tables)
                    if x[0] != "_" and x[0].isupper()
                ]))
            )

    cli.add_command(db_create)
    cli.add_command(db_fixtures)
    cli.add_command(db_recreate)
    cli.add_command(db_add_table)
    cli.add_command(edit_user)
    cli.add_command(run)
    cli.add_command(corpus_ingest)
    cli.add_command(corpus_import)
    cli.add_command(corpus_dump)
    cli.add_command(corpus_list)

    return cli
