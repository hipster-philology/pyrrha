from flask_login import current_user
from flask import request


from .utils import render_template_with_nav_info
from .. import main

from ...models import Corpus
from ...utils.pagination import int_or


@main.route('/')
def index():
    """ Index
    """
    if current_user.is_authenticated and not current_user.is_anonymous:
        corpora = Corpus.for_user(current_user, _all=False).paginate(
            page=int_or(request.args.get("page"), 1),
            per_page=20  # ToDo: Should it be hardcoded ?
        )
        return render_template_with_nav_info("main/index_loggedin.html", corpora=corpora)

    return render_template_with_nav_info('main/index.html')
