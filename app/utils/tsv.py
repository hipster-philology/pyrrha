from csv import DictReader, QUOTE_NONE
from io import StringIO


TSV_CONFIG = dict(delimiter='\t', quoting=QUOTE_NONE, escapechar="\\")


def StringDictReader(string, **kwargs):
    file = StringIO(string)
    return DictReader(file, **TSV_CONFIG, **kwargs)


def stream_tsv(file: StringIO):
    for line in file:
        yield line
