from ...models import Corpus
from flask import render_template


def render_template_with_nav_info(template, **kwargs):
    kwargs.update(dict(
        corpora=Corpus.query.all()
    ))
    return render_template(template, **kwargs)