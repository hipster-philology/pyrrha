from tests.test_selenium.base import TokenEdit2CorporaBase


class TokenEditBase(TokenEdit2CorporaBase):
    """ Base class with helpers to test token edition page """
    CORPUS = "wauchier"
    CORPUS_ID = "1"