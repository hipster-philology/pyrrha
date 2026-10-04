from csv import DictReader, QUOTE_NONE
from io import StringIO


TSV_CONFIG = dict(delimiter='\t', quoting=QUOTE_NONE, escapechar="\\")


def neutralize_formula(value):
    """ Prefix values that spreadsheets would evaluate as formulas (CSV injection) """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def StringDictReader(string, **kwargs):
    file = StringIO(string)
    return DictReader(file, **TSV_CONFIG, **kwargs)


def stream_tsv(file: StringIO):
    for line in file:
        yield line
