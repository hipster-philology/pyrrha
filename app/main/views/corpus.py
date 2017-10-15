from flask import request, jsonify, flash

from .utils import render_template_with_nav_info
from .. import main
from ...utils.tsv import StringDictReader
from ...utils.pagination import int_or
from ...models import Corpus, WordToken


@main.route('/corpus/new', methods=["POST", "GET"])
def corpus_new():
    """ Register a new corpus
    """
    if request.method == "POST":

        allowed_lemma = request.form.get("allowed_lemma")
        if allowed_lemma is not None:
            allowed_lemma = [x.replace('\r', '') for x in allowed_lemma.split("\n") if len(x.replace('\r', '').strip()) > 0]

        allowed_POS = request.form.get("allowed_POS")
        if allowed_POS is not None:
            allowed_POS = [x.replace('\r', '') for x in allowed_POS.split(",") if len(x.replace('\r', '').strip()) > 0]

        allowed_morph = request.form.get("allowed_morph")
        if allowed_morph is not None:
            allowed_morph = list(StringDictReader(allowed_morph))

        corpus = Corpus.create(
            request.form.get("name"),
            word_tokens_dict=StringDictReader(request.form.get("tsv")),
            allowed_lemma=allowed_lemma,
            allowed_POS=allowed_POS,
            allowed_morph=allowed_morph
        )
        flash("New corpus registered", category="success")
    return render_template_with_nav_info('main/corpus_new.html')


@main.route('/corpus/get/<int:corpus_id>')
def corpus_get(corpus_id):
    """ Read information about the corpus

    :param corpus_id: ID of the corpus
    :return:
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    return render_template_with_nav_info('main/corpus_info.html', corpus=corpus)


@main.route('/corpus/<int:corpus_id>/allowed/<allowed_type>')
def corpus_allowed_values(corpus_id, allowed_type):
    """ Find allowed values

    :param corpus_id: Id of the corpus
    :param allowed_type: Type of allowed value (lemma, morph, POS)
    """
    corpus = Corpus.query.get_or_404(corpus_id)

    return render_template_with_nav_info(
        "main/corpus_allowed_values.html",
        allowed_type=allowed_type,
        corpus=corpus,
        allowed_values=list(corpus.get_allowed_values(allowed_type=allowed_type).all())
    )


@main.route('/corpus/<int:corpus_id>/api/<allowed_type>')
def corpus_allowed_values_api(corpus_id, allowed_type):
    """ Find allowed values

    :param corpus_id: Id of the corpus
    :param allowed_type: Type of allowed value (lemma, morph, POS)
    """
    corpus = Corpus.query.get_or_404(corpus_id)

    return jsonify(
        [
            token
            for (token, ) in WordToken.get_like(
                corpus_id=corpus_id,
                form=request.args.get("form"),
                group_by=True,
                type_like=allowed_type,
                allowed_list=corpus.get_allowed_values(allowed_type=allowed_type).count() > 0
            ).all()
            if token is not None
        ]
    )


@main.route('/corpus/<int:corpus_id>/fixtures')
def generate_fixtures(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_tokens().all()
    allowed_lemma = corpus.get_allowed_values(allowed_type="lemma")
    allowed_POS = corpus.get_allowed_values(allowed_type="POS")
    return render_template_with_nav_info(
        template="main/corpus_generate_fixtures.html", tokens=tokens,
        allowed_lemma=allowed_lemma, allowed_pos=allowed_POS
    )