from ...models import Corpus
from flask import render_template, request


def render_template_with_nav_info(template, **kwargs):
    """ Render the template and adds information about available corpora

    :param template: Template path
    :param kwargs: Additional arguments for the template
    :return:
    """
    kwargs.update(dict(
        corpora=Corpus.query.all()
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
