import locale
from . import main
from json import dumps

locale.setlocale(locale.LC_ALL, '')


@main.app_template_filter("thousands")
def thousands(integer):
    """ Writes an integer with a coma to mark thousand (100000 becomes 100,000)

    :param integer: A number to transform
    :type integer: int
    :return: Formated number with grouped thousands
    :rtype: str
    """
    return locale.format("%d", integer, 1)


@main.app_template_filter("json")
def json(obj):
    return dumps(obj)
