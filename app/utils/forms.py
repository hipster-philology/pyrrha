def string_to_none(string):
    if string.strip() == "None":
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
