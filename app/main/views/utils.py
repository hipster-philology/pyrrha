from flask_login import current_user

from ...models import Corpus, ControlLists
from ...utils.tsv import StringDictReader
from flask import render_template, request
from csv import DictReader


def create_input_format_convertion(tokens, allowed_lemma, allowed_morph, allowed_POS):
    """ Convert input data into Corpus.create formats

    :param tokens: Tokens for the corpus
    :type tokens: str or _io.TextIOWrapper
    :param allowed_lemma: Lemmas that will be allowed in the corpus
    :type allowed_lemma:  str or _io.TextIOWrapper
    :param allowed_morph: Morphs that will be allowed in the corpus
    :type allowed_morph: str or _io.TextIOWrapper
    :param allowed_POS: POS that will be allowed in the corpus
    :type allowed_POS: str
    :return: Tokens, Allowed Lemma, Allowed Morph, Allowed POS
    :rtype: (csv.DictReader, list(str), list(dict), list(str))
    """
    if allowed_lemma is not None:
        allowed_lemma = [x.replace('\r', '') for x in allowed_lemma.split("\n") if len(x.replace('\r', '').strip()) > 0]

    if allowed_POS is not None:
        allowed_POS = [x.replace('\r', '') for x in allowed_POS.split(",") if len(x.replace('\r', '').strip()) > 0]

    if allowed_morph is not None:
        if isinstance(allowed_morph, str):
            allowed_morph = list(StringDictReader(allowed_morph))
        else:
            allowed_morph = list(DictReader(allowed_morph, dialect="excel-tab"))

    if isinstance(tokens, str):
        tokens = StringDictReader(tokens)
    else:
        tokens = DictReader(tokens, dialect="excel-tab")

    return tokens, allowed_lemma, allowed_morph, allowed_POS


def render_template_with_nav_info(template, **kwargs):
    """ Render the template and adds information about available corpora

    :param template: Template path
    :param kwargs: Additional arguments for the template
    :return:
    """
    kwargs.update(dict(
        corpora=[corpus for corpus in Corpus.for_user(current_user)]
    ))
    kwargs.update(dict(
        control_lists=[
            control_list for control_list in ControlLists.for_user(current_user)
        ]
    ))
    return render_template(template, **kwargs)


def request_wants_json():
    """ Evaluates whether JSON response was requested
    """
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def format_api_like_reply(result, mode="lemma"):
    """ Format autocomplete result for frontend

    :param result: A tuple of result out of the SQL Query
    :return: A jsonify-compliant value that will show on the front end
    """
    result = list(result)
    if mode == "morph" and len(result) == 1:
        return {"value": result[0], "label": result[0]}
    elif len(result) == 1:
        return result[0]
    elif len(result) == 2:
        return {"value": result[0], "label": result[1]}
