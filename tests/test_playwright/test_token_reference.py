"""Playwright tests for the token_reference and gloss ingestion feature."""
import pytest
from lxml import etree

from app.models import Corpus, WordToken
from tests.test_playwright.base import Helpers

REF_TSV = (
    "ref\tform\tlemma\tPOS\tmorph\tgloss\n"
    "w1\tDe\tde\tPRE\tNone\tpreposition\n"
    "w2\tseint\tsaint\tADJqua\tNone\tholy\n"
    "w3\tMartin\tmartin\tNOMpro\tNone\tproper name\n"
    "w4\tmout\tmout\tADVgen\tNone\t\n"
    "w5\tdoit\tdevoir\tVERcjg\tNone\t\n"
)

CORPUS_NAME = "RefTestCorpus"


class TestTokenReference(Helpers):

    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def _create_corpus(self):
        """Create the test corpus via the UI and return its DB object."""
        self.page.locator("#new_corpus_link").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#mode-annotated").click()
        self.page.locator("#panel-annotated").wait_for(state="visible")

        self.page.locator("#corpusName").fill(CORPUS_NAME)
        self.page.locator("#tokens").fill(REF_TSV)

        # Gloss column is visible by default (checkboxes hide columns when checked)
        # Use "Write your own" control list (simpler)
        self.page.locator("#label_checkbox_create").click()

        self.page.locator("#submit").click()
        self.page.wait_for_load_state("networkidle")

        return Corpus.query.filter_by(name=CORPUS_NAME).first()

    def _go_to_corpus(self, corpus_id):
        self.page.goto(self.url_for("main.tokens_correct", corpus_id=corpus_id))
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".at-loading").wait_for(state="hidden", timeout=10000)

    def test_ingestion_stores_token_reference_and_gloss(self):
        """Ingesting a TSV with ref and gloss columns stores them in the DB."""
        corpus = self._create_corpus()
        assert corpus is not None, "Corpus was not created"

        tokens = (
            WordToken.query.filter_by(corpus=corpus.id)
            .order_by(WordToken.order_id)
            .all()
        )
        assert len(tokens) == 5

        refs = [t.token_reference for t in tokens]
        assert refs == ["w1", "w2", "w3", "w4", "w5"]

        assert tokens[0].gloss == "preposition"
        assert tokens[1].gloss == "holy"
        assert tokens[2].gloss == "proper name"
        assert tokens[3].gloss is None
        assert tokens[4].gloss is None

    def test_view_shows_token_reference_in_id_column(self):
        """The ID column displays the token_reference instead of order_id when set."""
        corpus = self._create_corpus()
        self._go_to_corpus(corpus.id)

        first_row = self.page.locator(".at-row").first
        order_id_text = first_row.locator(".at-order-id").text_content().strip()
        assert order_id_text == "w1", f"Expected 'w1', got {order_id_text!r}"

    def test_standoff_tei_export_uses_token_reference(self):
        """The standoff-tei export uses token_reference as xml:id."""
        corpus = self._create_corpus()

        self.page.goto(self.url_for("main.tokens_export", corpus_id=corpus.id))
        self.page.wait_for_load_state("networkidle")

        with self.page.expect_download() as dl_info:
            self.page.locator("#standoff-tei").click()
        download = dl_info.value
        path = download.path()

        tree = etree.parse(path)
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        # w elements in <text>
        w_elements = tree.findall(".//tei:text//tei:w", ns)
        assert len(w_elements) == 5
        assert w_elements[0].get("{http://www.w3.org/XML/1998/namespace}id") == "w1"
        assert w_elements[0].text == "De"

        # annotationBlock in <standOff>
        blocks = tree.findall(".//tei:standOff//tei:annotationBlock", ns)
        assert len(blocks) == 5
        assert blocks[0].get("corresp") == "#w1"

        # gloss feature for w1
        gloss_f = blocks[0].find(".//tei:f[@name='gloss']/tei:string", ns)
        assert gloss_f is not None
        assert gloss_f.text == "preposition"

    def test_bookmark_works_with_token_reference(self):
        """Bookmarking a token with a token_reference still navigates correctly."""
        corpus = self._create_corpus()
        self._go_to_corpus(corpus.id)

        # Bookmark token at order_id=1 via the dropdown
        row = self.page.locator("[data-token-order='1']")
        row.locator(".at-dd-toggle").click()
        menu = row.locator(".at-dd-menu:visible")
        menu.get_by_role("link", name="Bookmark").click()
        self.page.wait_for_load_state("networkidle")

        # Navigate to the bookmark
        self.page.goto(self.url_for("main.index"))
        self.page.wait_for_load_state("networkidle")

        bookmark_link = self.page.locator("#bookmark_link")
        # Bookmark link only appears when on a corpus page
        self.page.goto(self.url_for("main.tokens_correct", corpus_id=corpus.id))
        self.page.wait_for_load_state("networkidle")

        self.page.locator("#bookmark_link").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator(".at-loading").wait_for(state="hidden", timeout=10000)

        # The first row with order_id=1 should be present
        assert self.page.locator("[data-token-order='1']").count() >= 1
