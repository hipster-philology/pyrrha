from flask import render_template, request, abort, flash
from flask_login import current_user
from functools import wraps


from ...models import Corpus, ControlLists


def requires_corpus_access(corpus_id_key):
    """ Check that a user has access to a corpus

    :param corpus_id_key: URL Parameter name in flask route declaration that contains the Corpus ID
    :return: Wrapped function
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not Corpus.static_has_access(request.view_args[corpus_id_key], current_user):
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def requires_corpus_admin_access(corpus_id_key):
    """ Check that a user has access to a corpus

    :param corpus_id_key: URL Parameter name in flask route declaration that contains the Corpus ID
    :return: Wrapped function
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not Corpus.query.get_or_404(request.view_args[corpus_id_key]).is_owned_by(
                    current_user
            ) and not current_user.is_admin():
                flash("You have not admin access to this corpus.")
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def render_template_with_nav_info(template, **kwargs):
    """ Render the template and adds information about available corpora

    :param template: Template path
    :param kwargs: Additional arguments for the template
    :return:
    """
    kwargs.update(dict(
        favorites=[corpus for corpus in Corpus.fav_for_user(current_user)]
    ))
    kwargs.update(dict(
        control_lists=[
            control_list for control_list in ControlLists.for_user(current_user)
        ]
    ))
    kwargs["resizedLeftMenu"] = request.cookies.get('resized-menu')
    return render_template(template, **kwargs)


def request_wants_json():
    """ Evaluates whether JSON response was requested
    """
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']
