from flask import request, jsonify, url_for

from .utils import render_template_with_nav_info, request_wants_json
from .. import main
from ...models import WordToken, Corpus, ChangeRecord
from ...utils.forms import string_to_none
from ...utils.pagination import int_or


@main.route('/corpus/<int:corpus_id>/tokens/edit')
def tokens_edit(corpus_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus\
        .get_tokens()\
        .paginate(page=int_or(request.args.get("page"), 1), per_page=int_or(request.args.get("limit"), 100))
    return render_template_with_nav_info('main/tokens_edit.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/unallowed/<allowed_type>/edit')
def tokens_edit_unallowed(corpus_id, allowed_type):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus\
        .get_unallowed(allowed_type)\
        .paginate(page=int_or(request.args.get("page"), 1), per_page=int_or(request.args.get("limit"), 100))
    return render_template_with_nav_info(
        'main/tokens_edit_unallowed.html',
        corpus=corpus,
        tokens=tokens,
        allowed_type=allowed_type
    )


@main.route('/corpus/<int:corpus_id>/tokens/changes/similar/<int:record_id>')
def tokens_similar_to_record(corpus_id, record_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    tokens = WordToken.get_similar_to_record(change_record=record).paginate(per_page=1000)
    return render_template_with_nav_info(
        # The Dict is a small hack to emulate paginate
        'main/tokens_similar_to_record.html', corpus=corpus, tokens=tokens, record=record
    )


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:token_id>')
def tokens_similar_to_token(corpus_id, token_id):
    mode = request.args.get("mode", "partial")
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    token = WordToken.query.filter_by(**{"id": token_id, "corpus": corpus_id}).first_or_404()
    tokens = WordToken.get_nearly_similar_to(token, mode=mode)
    if request_wants_json():
        if request.args.get("hits", "false").lower() == "true":
            return jsonify([
                tok.to_dict() for tok in tokens.all()
            ])
        return jsonify({"count" : tokens.count()})
    return render_template_with_nav_info(
        # The Dict is a small hack to emulate paginate
        'main/tokens_similar_to_token.html',
        corpus=corpus, tokens=tokens.paginate(per_page=1000), mode=mode, token=token
    )


@main.route('/corpus/<int:corpus_id>/tokens/edit/<int:token_id>', methods=["POST"])
def tokens_edit_single(corpus_id, token_id):
    try:
        token, change_record = WordToken.update(
            token_id=token_id, corpus_id=corpus_id,
            lemma=request.form.get("lemma"),
            POS=string_to_none(request.form.get("POS")),
            morph=string_to_none(request.form.get("morph"))
        )
        return jsonify({
            "token": token.to_dict(),
            "similar": {
                "count": change_record.similar_remaining,
                "link": url_for(".tokens_similar_to_record", corpus_id=corpus_id, record_id=change_record.id)
            }})
    except WordToken.ValidityError as E:
        response = jsonify({"status": False, "message": E.msg, "details": E.statuses})
        response.status_code = 403
        return response
    except WordToken.NothingChangedError as E:
        response = jsonify({"status": False, "message": E.msg, "details": E.statuses})
        response.status_code = 412
        return response


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:record_id>/update', methods=["POST"])
def tokens_edit_from_record(corpus_id, record_id):
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
    return jsonify([token.to_dict() for token, _ in changed])


@main.route('/corpus/<int:corpus_id>/tokens')
def tokens_export(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_tokens().all()
    return render_template_with_nav_info(
        template="main/tokens_view.html",
        corpus=corpus, tokens=tokens,
        headers="\t".join(["form", "lemma", "POS", "morph"])
    )


@main.route('/corpus/get/<int:corpus_id>/history')
def tokens_history(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_history(page=int_or(request.args.get("page"), 1), limit=int_or(request.args.get("limit"), 20))
    return render_template_with_nav_info('main/tokens_history.html', corpus=corpus, tokens=tokens)
