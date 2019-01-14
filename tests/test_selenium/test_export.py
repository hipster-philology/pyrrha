from tests.test_selenium.base import TestBase
from selenium.webdriver.chrome.options import Options
import xml.etree.ElementTree as etree

import os
import os.path
import time
import glob


TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


class TestExport(TestBase):
    def enable_download_in_headless_chrome(self, driver, download_dir):
        # add missing support for chrome "send_command"  to selenium webdriver
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        command_result = driver.execute("send_command", params)

    def create_driver(self, options=None):
        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "profile.default_content_settings.popups": 0,
            "safebrowsing.enabled": False
        })
        driver = super(TestExport, self).create_driver(options)
        self.enable_download_in_headless_chrome(driver, self.download_path)
        return driver

    def setUp(self):
        self.download_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "download_temp")
        )
        print(self.download_path)
        os.makedirs(self.download_path, exist_ok=True)
        super(TestExport, self).setUp()

    def tearDown(self):
        #super(TestExport, self).tearDown()
        for file in glob.glob(os.path.join(self.download_path, "*")):
            os.remove(file)
        os.rmdir(self.download_path)

    def test_tei_export(self):
        """ [Export] Test that the TEI export uses delimiter when needed"""
        # Try first with an edit that would word
        self.addCorpus(
            "wauchier", with_token=True, with_allowed_lemma=True, tokens_up_to=24,
            with_delimiter=True
        ) ## apparement, corpus.delimiter vaut rien

        self.driver.refresh()

        self.driver.get(self.url_for_with_port("main.tokens_export", corpus_id=1))
        self.driver.find_element_by_id("geste-tei").click()

        time.sleep(5)

        with open(os.path.join(self.download_path, "pyrrha-correction.xml")) as f:
            xml = etree.parse(f)
        abs = xml.findall(".//tei:ab", namespaces=TEI_NS)
        self.assertEqual(
            len(abs), 24/2,
            "There should be 12 segments, as one is added every two tokens"
        )
        self.assertEqual(
            [(el.text, el.get("lemma"), el.get("type")) for el in abs[0].findall("./tei:w", namespaces=TEI_NS)],
            [
                ("De", "de", "POS=PRE"),
                ("seint", "saint", "POS=ADJqua")
            ],
            "Words should be correctly written"
        )
        self.assertEqual(
            [(el.text, el.get("lemma"), el.get("type")) for el in abs[-1].findall("./tei:w", namespaces=TEI_NS)],
            [('puet', 'pöoir', 'POS=VERcjg'), ('l', 'il', 'POS=PROper')],
            "Words should be correctly grouped"
        )
