from .pagination import int_or
from .tsv import StringDictReader
from .forms import string_to_none
from typing import Dict, Optional
from urllib.parse import urlparse


class PyrrhaError(Exception):
    """Raised when errors specific to this application occur."""
    pass


class PersonalDictionaryError(PyrrhaError):
    """Raised when preferences could not be updated."""
    pass


class PreferencesUpdateError(PyrrhaError):
    """Raised when preferences could not be updated."""
    pass


class ValidationError(PyrrhaError):
    """Raised when constraints on data types are not respected."""
    pass


def validate_length(k: str, v: str, lengths: Dict[str, int]):
    """Enforce length constraints on data types to ensure
    portability of the database schema.

    SQLite does not enforce length constraints on data types.

    :param str k: column name
    :param str v: column value
    :param dict lengths: mapping of column names to length constraints

    :raises ValidationError: when length constraint is not respected
    """
    if k in lengths and len(v) > lengths[k]:
        raise ValidationError(
            f"column '{k}': '{v}' is too long (maximum {lengths[k]} characters)"
        )



def is_safe_next(target: Optional[str]) -> bool:
    """Only accept same-site relative paths as post-login redirect targets.

    :param target: Value of the ``next`` query parameter
    :return: True if the target is a local path (no scheme, no host)
    """
    if not target or not target.startswith("/") or target.startswith(("//", "/\\")):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc
