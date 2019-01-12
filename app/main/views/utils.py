from flask import render_template, request
from flask_login import current_user

from ...models import Corpus, ControlLists


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