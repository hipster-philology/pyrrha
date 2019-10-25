def int_or(value, default):
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, str) and value.isnumeric():
        return int(value)
    else:
        return default
