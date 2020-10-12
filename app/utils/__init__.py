from .pagination import int_or
from .tsv import StringDictReader
from .forms import string_to_none


class PyrrhaError(Exception):
    """Raised when errors specific to this application occur."""
    pass


class PreferencesUpdateError(PyrrhaError):
    """Raised when preferences could not be updated."""
    pass
