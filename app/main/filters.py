from flask import request, url_for
from json import dumps
import math

import locale
from . import main
from ..models import WordToken

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


@main.app_template_filter("get_token_uri")
def get_token_uri(token: WordToken):
    per_page = request.args.get("per_page", 100, int)
    page = int(math.ceil(token.order_id / 100))
    return url_for(
        "main.tokens_correct",
        corpus_id=token.corpus,
        page=page,
        per_page=per_page
    ) + f"#tok{token.order_id}"
