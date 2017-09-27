import locale
from . import main

locale.setlocale(locale.LC_ALL, '')


@main.app_template_filter("thousands")
def thousands(integer):
    return locale.format("%d", integer, 1)
