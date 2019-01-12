""" Tests here that reuse subscripts such as function from atservices.scripts.collatinus should
just check that these function are called, not that they have the right effect. Checking the effects of these
function should be done in their respective test modules (see .test_collatinus)

"""

import os
import shutil
from csv import reader
from unittest import TestCase

from click.testing import CliRunner
from nose.tools import nottest

from app import create_app, db
from app.cli import make_cli
from app.models import (
    AllowedLemma,
    AllowedMorph,
    AllowedPOS,
    WordToken
)
from tests.db_fixtures import add_corpus


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

    @nottest
    def pos_test(self):
        with self.app.app_context():
            POS = AllowedPOS.query.filter(AllowedPOS.control_list == 1).all()
            self.assertEqual(
                len(POS), 14,
                "There should be 14 allowed POS"
            )
            with open(self.relPath("test_scripts_data", "allowed_pos.txt")) as pos:
                self.assertEqual(
                    sorted(pos.read().strip().split(",")),
                    sorted([p.label for p in POS]),
                    "POS should be consistent with import file"
                )

    @nottest
    def token_test(self, result, success_msg="Corpus created under the name Wauchier2 with 25 tokens"):
        self.assertIn(
            success_msg,
            result.output
        )

    @nottest
    def morph_test(self):
        with self.app.app_context():
            morphs = AllowedMorph.query.filter(AllowedMorph.control_list == 1).all()
            self.assertEqual(
                len(morphs), 145,
                "There should be 145 allowed Morphs"
            )
            morphs = [
                m.label + " " + m.readable
                for m in morphs
            ]
            with open(self.relPath("test_scripts_data", "allowed_morph.csv")) as f:
                data = [
                    " ".join(line)
                    for line in list(reader(f, dialect="excel-tab"))[1:]
                    ]
            self.assertEqual(
                sorted(morphs), sorted(data),
                "Input allowed morphs should have been correctly inserted"
            )

    @nottest
    def lemma_test(self):
        with self.app.app_context():
            output_data = AllowedLemma.query.filter(AllowedLemma.control_list == 1).all()
            self.assertEqual(
                len(output_data), 21, "There should be 21 Lemmas"
            )
            with open(self.relPath("test_scripts_data", "allowed_lemma.txt")) as f:
                input_data = f.read().split()

            self.assertEqual(
                sorted([t.label for t in output_data]),
                sorted(input_data),
                "Input data should be the same as output data"
            )

    def test_corpus_import(self):
        """ Test that data ingestion works correctly"""
        result = self.invoke(
            "corpus-from-file",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv")
        )
        self.token_test(result)

    def test_corpus_import_POS(self):
        """ Test that data ingestion works correctly with Allowed POS"""
        result = self.invoke(
            "corpus-from-file",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--POS", self.relPath("test_scripts_data", "allowed_pos.txt")
        )
        self.token_test(result)
        self.pos_test()

    def test_corpus_import_morph(self):
        """ Test that data ingestion works correctly with Allowed Morph"""
        result = self.invoke(
            "corpus-from-file",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--morph", self.relPath("test_scripts_data", "allowed_morph.csv")
        )
        self.token_test(result)
        self.morph_test()

    def test_corpus_import_lemmas(self):
        """ Test that data ingestion works correctly with Allowed Lemmas"""
        result = self.invoke(
            "corpus-from-file",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--lemma", self.relPath("test_scripts_data", "allowed_lemma.txt")
        )
        self.token_test(result)
        self.lemma_test()

    def test_corpus_import_morph_and_POS(self):
        """ Test that data ingestion works correctly with Allowed Morph AND Morph"""
        result = self.invoke(
            "corpus-from-file",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--morph", self.relPath("test_scripts_data", "allowed_morph.csv"),
            "--POS", self.relPath("test_scripts_data", "allowed_pos.txt")
        )
        self.token_test(result)
        self.morph_test()
        self.pos_test()

    def test_corpus_import_morph_and_POS_and_lemma(self):
        """ Test that data ingestion works correctly with Allowed Morph AND Morph"""
        result = self.invoke(
            "corpus-from-file",
            "Wauchier2",
            "--corpus", self.relPath("test_scripts_data", "tokens.csv"),
            "--morph", self.relPath("test_scripts_data", "allowed_morph.csv"),
            "--POS", self.relPath("test_scripts_data", "allowed_pos.txt"),
            "--lemma", self.relPath("test_scripts_data", "allowed_lemma.txt")
        )
        self.token_test(result)
        self.morph_test()
        self.lemma_test()
        self.pos_test()

    def assertHasContents(self, file1, content):
        with open(file1) as f1:
            self.assertEqual(f1.read().replace("\r", ""), content)

    def test_corpus_list(self):
        with self.app.app_context():
            add_corpus(
                "floovant", db, tokens_up_to=3,
                with_allowed_lemma=True, partial_allowed_lemma=True,
                with_allowed_morph=True, partial_allowed_morph=True,
                with_allowed_pos=True, partial_allowed_pos=True
            )
            add_corpus(
                "wauchier", db, tokens_up_to=3,
                with_allowed_lemma=True, partial_allowed_lemma=True,
                with_allowed_morph=True, partial_allowed_morph=True,
                with_allowed_pos=True, partial_allowed_pos=True
            )
        result = self.invoke("corpus-list")
        self.assertIn("1\t| Wauchier", result.output)
        self.assertIn("2\t| Floovant", result.output)

    def test_corpus_dump(self):
        """ Test that data export works correctly """
        # Ingest data this way, not the best practice, but the shortest. Will allow file comparison down the lane
        with self.app.app_context():
            add_corpus(
                "floovant", db, tokens_up_to=3,
                with_allowed_lemma=True, partial_allowed_lemma=True,
                with_allowed_morph=True, partial_allowed_morph=True,
                with_allowed_pos=True, partial_allowed_pos=True
            )

        with self.runner.isolated_filesystem() as f:
            curr_dir = str(f)
            test_dir = "some_dir"
            result = self.invoke("corpus-dump", "2", "--path", test_dir)

            self.assertHasContents(
                os.path.join(curr_dir, test_dir, "tokens.csv").replace("\r", ""),
                "token_id	form	lemma	POS	morph\n"
                "1	SOIGNORS	seignor	_	NOMB.=p|GENRE=m|CAS=n\n"
                "2	or	or4	_	DEGRE=-\n"
                "3	escoutez	escouter	_	MODE=imp|PERS.=2|NOMB.=p\n"
            )
            self.assertIn("--- Tokens dumped", result.output)

            self.assertHasContents(
                os.path.join(curr_dir, test_dir, "allowed_lemma.txt"),
                "escouter\nor4\nseignor"
            )
            self.assertIn("--- Allowed Lemma Values dumped", result.output)

            self.assertHasContents(
                os.path.join(curr_dir, test_dir, "allowed_pos.txt"),
                "ADVgen,VERcjg,NOMcom"
            )
            self.assertIn("--- Allowed POS Values dumped", result.output)

            self.assertHasContents(
                os.path.join(curr_dir, test_dir, "allowed_morph.csv").replace("\r", ""),
                "label	readable\n"
                "_	pas de morphologie\n"
                "DEGRE=-	non applicable\n"
                "MODE=imp|PERS.=2|NOMB.=p	impératif 2e personne pluriel\n"
            )
            self.assertIn("--- Allowed Morphological Values dumped", result.output)

    def test_corpus_dump_not_found(self):
        """ Test that data export works correctly by not raising an issue if Corpus does not exist """
        # Ingest data this way, not the best practice, but the shortest. Will allow file comparison down the lane
        with self.app.app_context():
            add_corpus(
                "floovant", db, tokens_up_to=3,
                with_allowed_lemma=True, partial_allowed_lemma=True,
                with_allowed_morph=True, partial_allowed_morph=True,
                with_allowed_pos=True, partial_allowed_pos=True
            )

        with self.runner.isolated_filesystem() as f:
            curr_dir = str(f)
            test_dir = "some_dir"
            result = self.invoke("corpus-dump", "1", "--path", test_dir)
            self.assertIn(
                "Corpus not found", result.output
            )
            self.assertEqual(
                len(os.listdir(os.path.join(curr_dir, test_dir))), 0,
                "There should be no files"
            )

    @nottest
    def make_test(self, tests, context):
        with self.app.app_context():
            with self.runner.isolated_filesystem() as f:
                cur_dir = str(f)

                shutil.copy(
                    self.relPath("test_scripts_data", "tokens.csv"),
                    os.path.join(cur_dir, "tokens.csv")
                )
                extensions = {
                    "lemma": "txt",
                    "pos": "txt",
                    "morph": "csv"
                }
                for test in tests:
                    fname = "allowed_" + test + "." + extensions[test]
                    shutil.copy(
                        self.relPath("test_scripts_data", fname),
                        os.path.join(cur_dir, fname)
                    )
                self.assertEqual(
                    len(list(os.listdir(cur_dir))), len(tests) + 1,
                    "There should be as many input file as tests"
                )

                args = ["corpus-from-dir", "Floovant2", "--path", cur_dir]
                if context:
                    args += ["--right", "2", "--left", "1"]

                result = self.invoke(*args)

                self.token_test(
                    result,
                    success_msg="Corpus 'Floovant2' (ID : 1) created"
                )
                for test in tests:
                    getattr(self, test + "_test")()
                    print("Running " + test + "_test")

                if context:
                    self.assertEqual(
                        WordToken.query.get(context[0]).context, context[1],
                        "Context should be right"
                    )

                self.clear_db(self.app)
                db.create_all()

    def test_corpus_from_dir(self):
        """ Test that import from a directory works with autogenerated tests"""

        # Automatically testing a list of different situation

        tests = [
            ["morph", "lemma", "pos"],
            ["morph", "lemma"],
            ["lemma", "pos"],
            ["morph", "pos"],
            ["morph"],
            ["lemma"],
            ["pos"],
            []
        ]
        for context in [None, (9, "et volentiers le bien")]:
            for combination in tests:
                self.make_test(combination, context)
