from csv import DictReader

from app.utils import StringDictReader
from app.utils.tsv import TSV_CONFIG


def string_to_none(string):
    if string is None:
        return
    elif string.strip() == "None":
        return None
    else:
        return string


def strip_or_none(string):
    if string is not None:
        return string.strip()
    return string


def prepare_search_string(string: str) -> list:
    """ Transform a search string into a list of strings if "|" was used inside the string

    Agrees with escaped pipes.

    :param string: String to prepare
    :return: List of strings to search for
    """
    value = string.replace('\\|', '¤$¤')
    value = [v.replace('¤$¤', '|') for v in value.split('|')]
    return value


def column_search_filter(field, value: str) -> list:
    """ Based on a field name and a string value, computes the list of search WHERE that needs to be \
    applied to a query

    :param field: ORM Field Property
    :param value: Search String
    :return: List of WHERE clauses
    """
    branch_filters = []
    if len(value) > 0:
        value = value.replace(" ", "")
        # escape search operators
        value = value.replace('%', '\\%')
        value = value.replace('\\*', '¤$¤')
        value = value.replace('\\!', '¤$$¤')

        value = string_to_none(value)
        # distinguish LIKE from EQ
        if value is not None and "*" in value:
            value = value.replace("*", "%")
            # unescape '\*'
            value = value.replace('¤$¤', '*')

            if value.startswith("!") and len(value) > 1:
                value = value[1:]
                branch_filters.append(field.notlike(value, escape='\\'))
            else:
                # unescape '\!'
                value = value.replace('¤$$¤', '!')
                branch_filters.append(field.like(value, escape='\\'))
        else:
            # unescape '\*'
            value = value.replace('¤$¤', '*')

            if value is not None and value.startswith("!") and len(value) > 1:
                value = value[1:]
                branch_filters.append(field != value)
            else:
                # unescape '\!'
                value = value.replace('¤$$¤', '!')
                branch_filters.append(field == value)
    return branch_filters


def read_input_lemma(values):
    return [x.replace('\r', '') for x in values.split("\n") if len(x.replace('\r', '').strip()) > 0]


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