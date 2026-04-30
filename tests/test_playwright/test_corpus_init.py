"""Tests for corpus creation / registration."""
import csv
import pytest
from flask import url_for
from playwright.sync_api import expect

from app.models import Corpus, WordToken, AllowedLemma, AllowedMorph, ControlLists
from app import db
from tests.test_playwright.base import Helpers
from tests.fixtures import PLAINTEXT_CORPORA


class TestCorpusRegistration(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def go_to_new_corpus(self):
        self.page.locator("#new_corpus_link").click()
        self.page.wait_for_load_state("networkidle")

    def test_registration(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        with self.app.test_request_context():
            assert url_for('main.corpus_get', corpus_id=1) in self.page.url

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert corpus.delimiter_token is None

        tokens = WordToken.query.filter(WordToken.corpus == corpus.id)
        assert tokens.count() == 25

        saint = WordToken.query.filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "saint")).first()
        assert saint.form == "seint"
        assert saint.label_uniform == "saint"
        assert saint.POS == "ADJqua"
        assert saint.morph is None

        oir = WordToken.query.filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "öir")).first()
        assert oir.form == "oïr"
        assert oir.label_uniform == "oir"
        assert oir.POS == "VERinf"
        assert oir.morph is None

    def test_registration_with_full_allowed_lemma(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#allowed_lemma").fill(PLAINTEXT_CORPORA["Wauchier"]["lemma"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert WordToken.query.filter(WordToken.corpus == corpus.id).count() == 25

        allowed = AllowedLemma.query.filter(AllowedLemma.control_list == corpus.control_lists_id)
        assert allowed.count() == 21
        assert corpus.get_unallowed(allowed_type="lemma").count() == 0

    def test_registration_with_partial_allowed_lemma(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#allowed_lemma").fill(PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert WordToken.query.filter(WordToken.corpus == corpus.id).count() == 25

        saint = WordToken.query.filter(db.and_(WordToken.corpus == 1, WordToken.lemma == "saint")).first()
        assert saint.context == "De seint Martin mout doit"

        allowed = AllowedLemma.query.filter(AllowedLemma.control_list == corpus.control_lists_id)
        assert allowed.count() == 3
        assert corpus.get_unallowed(allowed_type="lemma").count() == 22

    def test_registration_with_allowed_morph(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#allowed_lemma").fill(PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.page.locator("#allowed_morph").fill(PLAINTEXT_CORPORA["Wauchier"]["morph"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert WordToken.query.filter(WordToken.corpus == corpus.id).count() == 25

        allowed_lemma = AllowedLemma.query.filter(AllowedLemma.control_list == corpus.control_lists_id)
        assert allowed_lemma.count() == 3

        allowed_morph = AllowedMorph.query.filter(AllowedMorph.control_list == corpus.control_lists_id)
        assert allowed_morph.count() == 145
        assert corpus.get_unallowed(allowed_type="lemma").count() == 22

    def test_registration_with_context(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#context_left").fill("5")
        self.page.locator("#context_right").fill("2")
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#allowed_lemma").fill(PLAINTEXT_CORPORA["Wauchier"]["partial_lemma"])
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert WordToken.query.filter(WordToken.corpus == corpus.id).count() == 25

        volentiers = WordToken.query.filter(
            db.and_(WordToken.corpus == 1, WordToken.lemma == "volentiers")
        ).first()
        assert volentiers.form == "volentiers"
        assert volentiers.context == "mout doit on doucement et volentiers le bien"

    def test_tokenization(self):
        self.go_to_new_corpus()
        self.page.locator("#tokens").fill("Ci gist mon seignor")
        self.page.locator("#tokenize").click()
        self.page.wait_for_load_state("networkidle")

        assert self.page.locator("#tokens").input_value() == "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n"
        assert self.page.locator("#punct-keep").is_checked()

        self.page.locator("#tokens").fill("Ci gist mon seignor...")
        self.page.locator("#tokenize").click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator("#tokens").input_value() == "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n.\t\t\t\n.\t\t\t\n.\t\t\t\n"

        self.page.locator("#tokens").fill("Ci gist mon seignor...")
        self.page.locator("#punct-keep").click()
        self.page.locator("#tokenize").click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator("#tokens").input_value() == "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n"

        self.page.locator("#tokens").fill("Ci gist mon sei- gnor...")
        self.page.locator("#hyphens-remove").click()
        self.page.locator("#tokenize").click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator("#tokens").input_value() == "form\tlemma\tPOS\tmorph\nCi\t\t\t\ngist\t\t\t\nmon\t\t\t\nseignor\t\t\t\n"

    def test_corpus_with_quotes(self):
        self.go_to_new_corpus()
        name = "GUILLEMETS DE MONTMURAIL"
        self.page.locator("#corpusName").fill(name)
        self.page.locator("#tokens").fill(
            "tokens\tlemmas\tPOS\tmorph\n"
            "\"\t\"\tPONC\tMORPH=EMPTY\n"
            "\'\t\'\tPONC\tMORPH=EMPTY\n"
            "“\t“\tPONC\tMORPH=EMPTY\n"
            "”\t”\tPONC\tMORPH=EMPTY\n"
            "«\t«\tPONC\tMORPH=EMPTY\n"
            "»\t»\tPONC\tMORPH=EMPTY\n"
            "‘\t‘\tPONC\tMORPH=EMPTY\n"
            "’\t’\tPONC\tMORPH=EMPTY\n"
            "„\t„\tPONC\tMORPH=EMPTY\n"
            "《\t《\tPONC\tMORPH=EMPTY\n"
            "》\t》\tPONC\tMORPH=EMPTY\n"
        )
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == name).first()
        assert corpus is not None
        tokens = WordToken.query.filter(WordToken.corpus == corpus.id)
        assert tokens.count() == 11
        assert WordToken.to_input_format(tokens).replace("\r", "") == (
            "token_id\tform\tlemma\tPOS\tmorph\n"
            "1\t\\\"\t\\\"\tPONC\tMORPH=EMPTY\n"
            "2\t\'\t\'\tPONC\tMORPH=EMPTY\n"
            "3\t“\t“\tPONC\tMORPH=EMPTY\n"
            "4\t”\t”\tPONC\tMORPH=EMPTY\n"
            "5\t«\t«\tPONC\tMORPH=EMPTY\n"
            "6\t»\t»\tPONC\tMORPH=EMPTY\n"
            "7\t‘\t‘\tPONC\tMORPH=EMPTY\n"
            "8\t’\t’\tPONC\tMORPH=EMPTY\n"
            "9\t„\t„\tPONC\tMORPH=EMPTY\n"
            "10\t《\t《\tPONC\tMORPH=EMPTY\n"
            "11\t》\t》\tPONC\tMORPH=EMPTY\n"
        )

    def test_registration_with_existing_control_list(self):
        self.add_control_lists()
        self.go_to_new_corpus()

        target_cl = ControlLists.query.filter(
            ControlLists.name == "Ancien Français - École des Chartes"
        ).first()

        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_reuse").click()
        self.page.select_option("#control_list_select", str(target_cl.id))
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert WordToken.query.filter(WordToken.corpus == corpus.id).count() == 25

        control_list = ControlLists.query.filter(ControlLists.id == corpus.control_lists_id).first()
        assert control_list.name.strip() == "Ancien Français - École des Chartes"

        self.page.locator("#toggle_controllists").click()
        assert self.page.locator(".dd-control_list").text_content().strip() == "Ancien Français - École des Chartes"

    def test_registration_with_false_control_list(self):
        self.add_control_lists()
        self.go_to_new_corpus()

        target_cl = ControlLists.query.filter(
            ControlLists.name == "Ancien Français - École des Chartes"
        ).first()

        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_reuse").click()
        self.page.select_option("#control_list_select", str(target_cl.id))
        # Changing the ID in javascript to check safety
        self.page.locator(f"#cl_opt_{target_cl.id}").evaluate("el => el.value = '99999'")
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        assert (
            "This control list does not exist" in
            [
                warning.text_content().strip()
                for warning in self.page.locator(".alert.alert-danger").all()
            ]
        )

    def test_registration_with_wrongly_formated_input(self):
        self.add_control_lists()
        self.go_to_new_corpus()

        target_cl = ControlLists.query.filter(
            ControlLists.name == "Ancien Français - École des Chartes"
        ).first()

        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(
            "lala\tlemma\tPOS\tmorph\n"
            "SOIGNORS\tseignor\tNOMcom\tNOMB.=p|GENRE=m|CAS=n\n"
            "or\tor4\tADVgen\tDEGRE=-\n"
            "escoutez\tescouter\tVERcjg\tMODE=imp|PERS.=2|NOMB.=p\n"
            "que\tque4\tCONsub\t_\n"
            "\tdieu\tNOMpro\tNOMB.=s|GENRE=m|CAS=n\n"
            "vos\tvos1\tPROper\tPERS.=2|NOMB.=p|GENRE=m|CAS=r\n"
            "soit\testre1\tVERcjg\tMODE=sub|TEMPS=pst|PERS.=3|NOMB.=s"
        )
        self.page.locator("#label_checkbox_reuse").click()
        self.page.select_option("#control_list_select", str(target_cl.id))
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        assert sorted(
            e.text_content().strip()
            for e in self.page.locator(".alert.alert-danger:visible").all()
            if e.text_content().strip()
        ) == sorted(["At least one line of your corpus is missing a token/form. Check line 1"])

    def test_registration_with_no_tsv_input(self):
        self.add_control_lists()
        self.go_to_new_corpus()

        target_cl = ControlLists.query.filter(
            ControlLists.name == "Ancien Français - École des Chartes"
        ).first()

        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#label_checkbox_reuse").click()
        self.page.select_option("#control_list_select", str(target_cl.id))
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        assert sorted(
            e.text_content().strip()
            for e in self.page.locator(".alert.alert-danger:visible").all()
            if e.text_content().strip()
        ) == sorted(["You did not input any text."])

    def test_registration_with_sep_token(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#sep_token").fill("____")
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        corpus = Corpus.query.filter(Corpus.name == PLAINTEXT_CORPORA["Wauchier"]["name"]).first()
        assert corpus is not None
        assert corpus.delimiter_token == "____"

    def test_registration_upload_file(self, tmp_path):
        self.go_to_new_corpus()
        temp_file = self.create_temp_example_file(tmp_path)
        self.page.locator("#upload").set_input_files(str(temp_file))
        expect(self.page.locator("#tokens[data-upload-complete='true']")).to_be_attached()

        tokens_value = self.page.locator("#tokens").input_value()
        with open(temp_file) as fp:
            file_rows = [row for row in csv.reader(fp, delimiter="\t")]
        textarea_rows = [row for row in csv.reader(tokens_value.split("\n"), delimiter="\t") if row]
        assert sorted(textarea_rows) == sorted(file_rows)

    def test_registration_with_field_length_violation(self):
        self.add_control_lists()
        target_cl = ControlLists.query.filter(
            ControlLists.name == "Ancien Français - École des Chartes"
        ).first()

        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill("example")
        self.page.locator("#label_checkbox_reuse").click()
        self.page.select_option("#control_list_select", str(target_cl.id))

        invalid = "btOUZvzXARqNbnmvVIrcqjAbsRGIvZQsrhspGusZypNlUJSubtOztbiMiwipTpQJVTvSDZyIGCaONJ"
        self.page.locator("#tokens").fill(
            f"form\tlemma\tPOS\tmorph\n{invalid}\tseignor\tNOMcom\tNOMB.=p|GENRE=m|CAS=n"
        )
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        assert (
            self.page.locator(".alert.alert-danger:visible").text_content().strip()
            == f"ln. 2, column 'form': '{invalid}' is too long (maximum 64 characters)"
        )

    def test_registration_without_field_length_violation(self):
        self.add_control_lists()
        target_cl = ControlLists.query.filter(
            ControlLists.name == "Ancien Français - École des Chartes"
        ).first()

        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill("example")
        self.page.locator("#label_checkbox_reuse").click()
        self.page.select_option("#control_list_select", str(target_cl.id))
        self.page.locator("#tokens").fill(
            "form\tlemma\tPOS\tmorph\nSOIGNORS\tseignor\tNOMcom\tNOMB.=p|GENRE=m|CAS=n"
        )
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator(".alert.alert-danger:visible").count() == 0

    def test_corpus_name_unique_user(self):
        self.add_control_lists()
        self.add_user("foo", "foo")
        self.login("foo.foo@ppa.fr", self.app.config["ADMIN_PASSWORD"])
        self.addCorpus("wauchier", cl=False)
        self.add_user("bar", "bar")
        self.login("bar.bar@ppa.fr", self.app.config["ADMIN_PASSWORD"])
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill("Wauchier")
        self.page.locator("#label_checkbox_reuse").click()
        self.page.locator("#control_list_select").click()
        self.page.locator("#tokens").fill(
            "form\tlemma\tPOS\tmorph\nSOIGNORS\tseignor\tNOMcom\tNOMB.=p|GENRE=m|CAS=n"
        )
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")
        assert self.page.locator(".alert.alert-danger").count() == 0

    def test_lemmatization_service(self):
        self.go_to_new_corpus()
        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])

        details = self.page.locator(".lemmatizer-details").all()
        assert not details[0].is_visible(), "Nothing should be displayed by default"

        self.page.locator("#language-model").select_option(label="Dummy lemmatizer")
        assert details[0].is_visible(), "Something should be displayed"
        assert "Dummy lemmatizer is a lemmatization service provided by ProviderInstitution." in details[0].text_content()

        self.page.locator("#language-model").select_option(label="Select a service")
        assert not details[0].is_visible(), "Nothing should be displayed now"

    def test_lemmatization_service_runs(self):
        from multiprocessing import Process
        from flask import Flask, request, Response

        fixture_app = Flask("fixture")

        @fixture_app.route("/lemma", methods=["POST"])
        def lemmatizing():
            return Response(
                "\n".join(
                    ["token\tlemma"] +
                    ["\t".join([tok, f"{idx}"]) for idx, tok in enumerate(request.form.get("data").split())]
                ),
                200,
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "Access-Control-Allow-Origin": "*",
                },
            )

        second_app = Process(
            target=fixture_app.run,
            daemon=True,
            kwargs={"host": "localhost", "port": 4567}
        )
        second_app.start()

        try:
            self.go_to_new_corpus()
            self.page.locator("#corpusName").fill("Test")
            self.page.locator("#tokens").fill("Je suis")

            self.page.locator("#language-model").select_option(index=1)
            self.page.locator("#submit-model").click()
            self.page.locator("#tokens-success").wait_for(state="visible", timeout=10000)

            assert self.page.locator("#tokens").input_value().split("\n") == ["token\tlemma", "Je\t0", "suis\t1"]
            assert (
                self.page.locator("#tokens-success").text_content().strip()
                == "Operation finished with success ! 2 tokens analyzed in total."
            )
        finally:
            second_app.terminate()
            second_app.join(2)
            second_app.close()

    def test_registration_filters(self):
        self.add_user("foo", "foo")
        self.login("foo.foo@ppa.fr", self.app.config["ADMIN_PASSWORD"])
        self.go_to_new_corpus()

        self.page.locator("#corpusName").fill(PLAINTEXT_CORPORA["Wauchier"]["name"])
        self.page.locator("#tokens").fill(PLAINTEXT_CORPORA["Wauchier"]["data"])
        self.page.locator("#label_checkbox_create").click()
        self.page.locator("[name='punct']").wait_for(state="visible", timeout=10000)
        self.page.locator("[name='punct']").click()
        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        self.go_to_control_list_curation("Wauchier")
        self.page.get_by_role("link", name="Ignore values").click()
        self.page.wait_for_load_state("networkidle")

        assert self.page.locator("[name='punct']").is_checked()
        assert not self.page.locator("[name='numeral']").is_checked()
