from unittest import TestCase
from glob import glob


class CheckConfigurations(TestCase):
    def test_unique_values(self):
        """ Check that configuration do not contain duplicate lines"""
        for config in glob("app/configurations/langs/**/*.txt"):
            with open(config) as f:
                content = f.read()

            if config.endswith("POS.txt"):
                lines = content.split(",")
            else:
                lines = content.split("\n")
            print("Testing " + config)
            self.assertEqual(
                len(set(lines)), len(lines),
                "There should be no duplicate in lemma"
            )
