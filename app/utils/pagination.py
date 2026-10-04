MAX_PAGE_SIZE = 500


def int_or(value, default, max_value=None):
    """ Parse a request value as a non-negative integer.

    :param value: Raw value (usually from request.args)
    :param default: Returned when the value is not a number
    :param max_value: Optional upper bound the result is clamped to
    """
    if isinstance(value, (int, float)):
        result = value
    elif isinstance(value, str) and value.isnumeric():
        result = int(value)
    else:
        return default
    if max_value is not None:
        result = min(result, max_value)
    return result
