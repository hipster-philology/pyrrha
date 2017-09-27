from csv import DictReader
from io import StringIO


def StringDictReader(string, **kwargs):
    file = StringIO(string)
    return DictReader(file, dialect="excel-tab", **kwargs)
