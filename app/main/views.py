from flask import render_template, jsonify, request, flash

from . import main
from ..models import Corpus, WordToken, ChangeRecord
from ..utils import StringDictReader, int_or, string_to_none


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
def get_corpus(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    return render_template_with_nav_info('main/corpus_info.html', corpus=corpus)


@main.route('/corpus/get/<int:corpus_id>/history')
def corpus_history(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_history(page=int_or(request.args.get("page"), 1), limit=int_or(request.args.get("limit"), 20))
    return render_template_with_nav_info('main/corpus_history.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/edit')
def edit_tokens(corpus_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus.get_tokens(page=int_or(request.args.get("page"), 1), limit=int_or(request.args.get("limit"), 100))
    return render_template_with_nav_info('main/tokens_edit.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:record_id>')
def similar_tokens(corpus_id, record_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    tokens = WordToken.get_similar_to(change_record=record).paginate(per_page=1000)
    return render_template_with_nav_info(
        # The Dict is a small hack to emulate paginate
        'main/corpus_similar.html', corpus=corpus, tokens=tokens, record=record
    )


@main.route('/corpus/<int:corpus_id>/tokens/edit/<int:token_id>', methods=["POST"])
def edit_single_token(corpus_id, token_id):
    try:
        token = WordToken.update(
            token_id=token_id, corpus_id=corpus_id,
            lemma=request.form.get("lemma"),
            POS=string_to_none(request.form.get("POS")),
            morph=string_to_none(request.form.get("morph"))
        )
        return jsonify(token.to_dict())
    except WordToken.ValidityError as E:
        response = jsonify({"status": False, "message": E.msg, "details": E.statuses})
        response.status_code = 403
        return response


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:record_id>/update', methods=["POST"])
def edit_from_tracked_record(corpus_id, record_id):
    _ = Corpus.query.filter_by(**{"id": corpus_id}).first_or_404()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    changed = []
    for token_id in request.json.get("word_tokens"):
        changed.append(
            WordToken.update(
                token_id=token_id, corpus_id=corpus_id,
                lemma=record.lemma_new, POS=record.POS_new, morph=record.morph_new
            )
        )
    return jsonify([token.to_dict() for token in changed])


@main.route('/corpus/<int:corpus_id>/tokens')
def view_tokens(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_all_tokens()
    return render_template_with_nav_info(
        template="main/tokens_view.html",
        corpus=corpus, tokens=tokens,
        headers="\t".join(["form", "lemma", "POS", "morph"])
    )
