def string_to_none(string):
    if string.strip() == "None":
        return None
    else:
        return string


def strip_or_none(string):
    if string is not None:
        return string.strip()
    return string