from typing import List, Optional
from csv import DictReader
from sqlalchemy import func

from app.utils import StringDictReader
from app.utils.tsv import TSV_CONFIG
from sqlalchemy.sql import ColumnExpressionArgument, ColumnElement


def string_to_none(string: Optional[str]) -> Optional[str]:
    """ Converts a string to None, including a string marked as None
    """
    if string is None:
        return
    elif string.strip() == "None":
        return None
    else:
        return string


def strip_or_none(string: Optional[str]) -> Optional[str]:
    """Strip a string if it is not none"""
    if string is not None:
        return string.strip()
    return string


def prepare_search_string(string: str) -> List[str]:
    """ Transform a search string into a list of strings if "|" was used inside the string

    Agrees with escaped pipes.

    :param string: String to prepare
    :return: List of strings to search for
    """
    value = string.replace('\\|', '¤$¤')
    value = [v.replace('¤$¤', '|') for v in value.split('|')]
    return value


def column_search_filter(
        field: ColumnElement,
        value: str,
        case_sensitive: bool = True) -> List[ColumnExpressionArgument]:
    """ Based on a field name and a string value, computes the list of search WHERE that needs to be \
    applied to a query

    :param field: ORM Field Property
    :param value: Search String
    :param case_sensitive: Enable case sensitivity
    :return: List of WHERE clauses
    """
    # modifier ici case.
    branch_filters = []
    if not value:
        return []

    # Clean-up the string
    value = value.replace(" ", "")
    # Escape search operators from LIKE
    value = value.replace('%', '\\%')
    # Replace * and ! which are escaped, so that they are not treated as wildcard or NOTs.
    value = value.replace('\\*', '¤$¤')
    value = value.replace('\\!', '¤$$¤')
    value = string_to_none(value)

    # If all operation produced an empty string, return an empty list
    if not value or value == "!":
        return []

    # If we are case-sensitive, we keep using like and or not like
    if case_sensitive:
        notlike = lambda x: field.notlike(x, escape="\\")
        like = lambda x: field.like(x, escape="\\")
        eq_field = field
        eq_value = lambda x: x
    else:
        notlike = lambda x: field.notilike(x, escape="\\")
        like = lambda x: field.ilike(x, escape="\\")
        eq_field = func.lower(field)
        eq_value = lambda x: x.lower()

    # distinguish LIKE from EQ when wild cards are used
    if value is not None and "*" in value:
        # Replace unescaped * as LIKE operator wildcards
        value = value.replace("*", "%")
        # Re-introduce previously escaped * (as ¤$¤) as the search character *
        value = value.replace('¤$¤', '*')

        # Then we check if we are in a not or not request
        if value.startswith("!") and len(value) > 1:
            value = value[1:]
            operator = notlike
        else:
            operator = like
    else:
        # Re-introduce previously escaped * (as ¤$¤) as the search character *
        value = value.replace('¤$¤', '*')

        # Then we check if we are in a not or not request
        if value.startswith("!") and len(value) > 1:
            value = value[1:]
            operator = eq_field.__ne__
        else:
            operator = eq_field.__eq__

        value = eq_value(value)

    # Re-introduce previously escaped ! (as ¤$$¤) as the search character !
    value = value.replace('¤$$¤', '!')
    branch_filters.append(operator(value))
    return branch_filters


def read_input_lemma(values: str) -> List[str]:
    return [
        x.replace('\r', '')
        for x in values.split("\n")
        if len(x.replace('\r', '').strip()) > 0
    ]


def read_input_morph(values):
    if isinstance(values, str):
        return list(StringDictReader(values))
    else:
        return list(DictReader(values, dialect="excel-tab"))


def read_input_POS(values):
    return [x.replace('\r', '') for x in values.split(",") if len(x.replace('\r', '').strip()) > 0]


def read_input_tokens(tokens):
    if isinstance(tokens, str):
        return StringDictReader(tokens)
    else:
        return DictReader(tokens, **TSV_CONFIG)


def create_input_format_convertion(tokens, allowed_lemma, allowed_morph, allowed_POS):
    """ Convert input data into Corpus.create formats

    :param tokens: Tokens for the corpus
    :type tokens: str or _io.TextIOWrapper
    :param allowed_lemma: Lemmas that will be allowed in the corpus
    :type allowed_lemma:  str or _io.TextIOWrapper
    :param allowed_morph: Morphs that will be allowed in the corpus
    :type allowed_morph: str or _io.TextIOWrapper
    :param allowed_POS: POS that will be allowed in the corpus
    :type allowed_POS: str
    :return: Tokens, Allowed Lemma, Allowed Morph, Allowed POS
    :rtype: (csv.DictReader, list(str), list(dict), list(str))
    """
    if allowed_lemma is not None:
        allowed_lemma = read_input_lemma(allowed_lemma)

    if allowed_POS is not None:
        allowed_POS = read_input_POS(allowed_POS)

    if allowed_morph is not None:
        allowed_morph = read_input_morph(allowed_morph)

    if tokens:
        tokens = read_input_tokens(tokens)

    return tokens, allowed_lemma, allowed_morph, allowed_POS
