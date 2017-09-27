from flask import render_template, jsonify, request, flash

from . import main
from ..models import Corpus, WordToken
from ..utils.tsv import StringDictReader
from ..utils.pagination import int_or


def render_template_with_nav_info(template, **kwargs):
    kwargs.update(dict(
        corpora=Corpus.query.all()
    ))
    return render_template(template, **kwargs)


@main.route('/')
def index():
    return render_template_with_nav_info('main/index.html')


@main.route('/corpus/new', methods=["POST", "GET"])
def new_corpus():
    if request.method == "POST":
        corpus = Corpus.create(request.form.get("name"), StringDictReader(request.form.get("tsv")))
        flash("New corpus registered", category="success")
    return render_template_with_nav_info('main/corpus_new.html')


@main.route('/corpus/get/<int:corpus_id>')
def get_corpus(corpus_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    return render_template_with_nav_info('main/corpus_info.html', corpus=corpus)


@main.route('/corpus/<int:corpus_id>/tokens/edit')
def edit_tokens(corpus_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus.get_tokens(page=int_or(request.args.get("page"), 1), limit=int_or(request.args.get("limit"), 100))
    return render_template_with_nav_info('main/tokens_edit.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/edit/<int:token_id>', methods=["POST"])
def edit_single_token(corpus_id, token_id):
    token = WordToken.update(
        token_id=token_id, corpus_id=corpus_id,
        lemma=request.form.get("lemma"), POS=request.form.get("POS"), morph=request.form.get("morph")
    )
    return jsonify(token.to_dict())


@main.route('/corpus/<int:corpus_id>/tokens')
def view_tokens(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_all_tokens()
    return render_template_with_nav_info(
        template="main/tokens_view.html",
        corpus=corpus, tokens=tokens,
        headers="\t".join(["form", "lemma", "POS", "morph"])
    )
