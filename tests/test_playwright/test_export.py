"""Tests for corpus export (TEI formats)."""
import xml.etree.ElementTree as etree
import pytest

from tests.test_playwright.base import Helpers

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


class TestExport(Helpers):
    @pytest.fixture(autouse=True)
    def setup(self, page, url_for_port, app):
        self.page = page
        self.url_for = url_for_port
        self.app = app

    def test_tei_msd_export(self):
        self.addCorpus("priapees", with_token=True, with_allowed_lemma=True, tokens_up_to=24, with_delimiter=True)
        self.page.reload()
        self.page.goto(self.url_for("main.tokens_export", corpus_id=3))

        with self.page.expect_download() as dl_info:
            self.page.locator("#tei-msd").click()
        download = dl_info.value
        path = download.path()

        with open(path) as f:
            xml = etree.parse(f)

        abs_elems = xml.findall(".//tei:ab", namespaces=TEI_NS)
        assert len(abs_elems) == 18 // 2, "There should be 9 segments"

        assert [
            (
                el.text,
                el.get("lemma"),
                el.get("pos"),
                el.get("n"),
                el.get("{http://www.w3.org/XML/1998/namespace}id"),
                el.get("msd"),
            )
            for el in abs_elems[0].findall("./tei:w", namespaces=TEI_NS)
        ] == [
            ("Carminis", "carmen1", "NOMcom", "1", "t1", "Case=Gen|Numb=Sing"),
            ("incompti", "incomptus", "ADJqua", "2", "t2", "Case=Gen|Numb=Sing|Deg=Pos"),
        ]

        assert [
            (el.text, el.get("lemma"), el.get("pos"), el.get("msd"))
            for el in abs_elems[1].findall("./tei:w", namespaces=TEI_NS)
        ] == [
            ("lusus", "lusus", "NOMcom", "Case=Gen|Numb=Sing"),
            ("lecture", "lego?", "VER", "Case=Voc|Numb=Sing|Mood=Par|Voice=Act"),
        ]

    def test_tei_geste_export(self):
        self.addCorpus("wauchier", with_token=True, with_allowed_lemma=True, tokens_up_to=24, with_delimiter=True)
        self.page.reload()
        self.page.goto(self.url_for("main.tokens_export", corpus_id=1))

        with self.page.expect_download() as dl_info:
            self.page.locator("#geste-tei").click()
        download = dl_info.value
        path = download.path()

        with open(path) as f:
            xml = etree.parse(f)

        abs_elems = xml.findall(".//tei:ab", namespaces=TEI_NS)
        assert len(abs_elems) == 24 // 2, "There should be 12 segments"

        assert [
            (
                el.text,
                el.get("lemma"),
                el.get("type"),
                el.get("n"),
                el.get("{http://www.w3.org/XML/1998/namespace}id"),
            )
            for el in abs_elems[0].findall("./tei:w", namespaces=TEI_NS)
        ] == [
            ("De", "de", "POS=PRE", "1", "t1"),
            ("seint", "saint", "POS=ADJqua", "2", "t2"),
        ]

        assert [
            (el.text, el.get("lemma"), el.get("type"))
            for el in abs_elems[-1].findall("./tei:w", namespaces=TEI_NS)
        ] == [
            ("puet", "pöoir", "POS=VERcjg"),
            ("l", "il", "POS=PROper"),
        ]
