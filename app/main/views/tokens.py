from flask import request, jsonify, url_for, abort, render_template, current_app, redirect, flash, Response, \
    stream_with_context
from flask_login import current_user, login_required
from slugify import slugify
import math
from csv import DictWriter
from io import StringIO
from typing import Dict
from sqlalchemy.orm import selectinload

from app import db
from .utils import render_template_with_nav_info, request_wants_json, requires_corpus_access
from .. import main
from ...models import WordToken, Corpus, ChangeRecord, TokenHistory, Bookmark
from ...utils.forms import string_to_none
from ...utils.pagination import int_or
from ...utils.tsv import TSV_CONFIG, stream_tsv
from ...utils.response import stream_template


def _corpus_urls(corpus, data_url=None):
    """ Return the URL map shared between the HTML config and the data API. """
    return {
        "data": data_url or url_for("main.tokens_correct_data", corpus_id=corpus.id),
        "save": url_for("main.tokens_correct_single", corpus_id=corpus.id, token_id=0)[:-1],
        "edit": url_for("main.tokens_edit_form", corpus_id=corpus.id, token_id=0)[:-1],
        "remove": url_for("main.tokens_del_row", corpus_id=corpus.id, token_id=0)[:-1],
        "insert": url_for("main.tokens_add_row", corpus_id=corpus.id, token_id=0)[:-1],
        "bookmark": url_for("main.corpus_bookmark", corpus_id=corpus.id),
        "review": url_for("main.tokens_mark_review", corpus_id=corpus.id, token_id=0)[:-1],  # strips trailing 0
        "similar_record": url_for("main.tokens_similar_to_record", corpus_id=corpus.id, record_id=0)[:-1],
        "custom_dict": url_for("main.corpus_custom_dictionary", corpus_id=corpus.id),
        "autocomplete": {
            "lemma": {
                "allowed": corpus.allowed_search_route("lemma"),
                "custom": corpus.custom_dictionary_search_route("lemma")
            },
            "POS": {
                "allowed": corpus.allowed_search_route("POS"),
                "custom": corpus.custom_dictionary_search_route("POS")
            },
            "morph": {
                "allowed": corpus.allowed_search_route("morph"),
                "custom": corpus.custom_dictionary_search_route("morph")
            },
            "gloss": {
                "allowed": url_for("main.gloss_search_value_api", corpus_id=corpus.id),
                "custom": None
            }
        }
    }


@main.route('/corpus/<int:corpus_id>/tokens/correct')
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct(corpus_id):
    """ Page to edit word tokens

    :param corpus_id: Id of the corpus
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()

    # Minimal config — no token data; Vue fetches via tokens_correct_data
    visible_cols = list(corpus.displayed_columns_by_name.keys())

    pyrrha_config = {
        "corpus_id": corpus.id,
        "visible_columns": visible_cols,
        "urls": _corpus_urls(corpus),
    }

    return render_template_with_nav_info(
        'main/tokens_correct.html',
        corpus=corpus,
        pyrrha_config=pyrrha_config
    )


@main.route('/corpus/<int:corpus_id>/tokens/correct/data')
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_data(corpus_id):
    """ JSON endpoint: paginated token data for the annotation table. """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    current_user.bookmark: Bookmark = corpus.get_bookmark(current_user)

    tokens = corpus.get_tokens().paginate(
        page=int_or(request.args.get("page"), 1),
        per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
    )

    if "similar" in corpus.displayed_columns_by_name:
        WordToken.get_similar_for_batch(corpus, tokens.items)

    changed = corpus.changed(tokens.items)

    tokens_data = []
    for tok in tokens.items:
        d = tok.to_dict()
        d["changed"] = tok.id in changed
        d["similar"] = getattr(tok, "similar", 0)
        d["similar_link"] = url_for(
            "main.tokens_similar_to_token", corpus_id=corpus.id, token_id=tok.id
        ) if d["similar"] else None
        d["left_context"] = tok.left_context or ""
        d["right_context"] = tok.right_context or ""
        tokens_data.append(d)

    return jsonify({
        "tokens": tokens_data,
        "page": tokens.page,
        "pages": tokens.pages,
        "total": tokens.total,
        "per_page": tokens.per_page,
        "bookmark_token_id": current_user.bookmark.token_id if current_user.bookmark else None,
    })


@main.route('/corpus/<int:corpus_id>/tokens/unallowed/<allowed_type>/correct')
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_unallowed(corpus_id, allowed_type):
    """ Page to edit tokens that have unallowed values

    :param corpus_id: Id of the corpus
    :param allowed_type: Type of allowed value to check against (lemma, POS, morph)
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    visible_cols = list(corpus.displayed_columns_by_name.keys())
    pyrrha_config = {
        "corpus_id": corpus.id,
        "visible_columns": visible_cols,
        "urls": _corpus_urls(
            corpus,
            data_url=url_for("main.tokens_correct_unallowed_data", corpus_id=corpus.id, allowed_type=allowed_type)
        ),
    }
    return render_template_with_nav_info(
        'main/tokens_correct_unallowed.html',
        corpus=corpus, allowed_type=allowed_type,
        pyrrha_config=pyrrha_config
    )


@main.route('/corpus/<int:corpus_id>/tokens/unallowed/<allowed_type>/correct/data')
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_unallowed_data(corpus_id, allowed_type):
    """ JSON endpoint: paginated unallowed tokens for the annotation table. """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus.get_unallowed(allowed_type).paginate(
        page=int_or(request.args.get("page"), 1),
        per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
    )
    changed = corpus.changed(tokens.items)
    tokens_data = []
    for tok in tokens.items:
        d = tok.to_dict()
        d["changed"] = tok.id in changed
        d["similar"] = 0
        d["similar_link"] = None
        d["left_context"] = tok.left_context or ""
        d["right_context"] = tok.right_context or ""
        tokens_data.append(d)
    return jsonify({
        "tokens": tokens_data,
        "page": tokens.page,
        "pages": tokens.pages,
        "total": tokens.total,
        "per_page": tokens.per_page,
        "bookmark_token_id": None,
    })



@main.route('/corpus/<int:corpus_id>/tokens/changes/similar/<int:record_id>')
@login_required
@requires_corpus_access("corpus_id")
def tokens_similar_to_record(corpus_id, record_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    visible_cols = list(corpus.displayed_columns_by_name.keys())
    pyrrha_config = {
        "corpus_id": corpus.id,
        "visible_columns": visible_cols,
        "data_url": url_for("main.tokens_similar_to_record_data", corpus_id=corpus.id, record_id=record_id),
        "apply_url": url_for("main.tokens_correct_from_record", corpus_id=corpus.id, record_id=record_id),
        "record": {
            "lemma":     record.lemma,     "lemma_new":  record.lemma_new,
            "POS":       record.POS,       "POS_new":    record.POS_new,
            "morph":     record.morph,     "morph_new":  record.morph_new,
            "user":      "{}.{}".format(record.user.first_name[0], record.user.last_name),
            "created_on": str(record.created_on),
            "similar_remaining": record.similar_remaining,
        },
    }
    return render_template_with_nav_info(
        'main/tokens_similar_to_record.html',
        corpus=corpus, record=record,
        pyrrha_config=pyrrha_config
    )


@main.route('/corpus/<int:corpus_id>/tokens/changes/similar/<int:record_id>/data')
@login_required
@requires_corpus_access("corpus_id")
def tokens_similar_to_record_data(corpus_id, record_id):
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    tokens = WordToken.get_similar_to_record(change_record=record).paginate(
        page=int_or(request.args.get("page"), 1),
        per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
    )
    changed = corpus.changed(tokens.items)
    tokens_data = []
    for tok in tokens.items:
        d = tok.to_dict()
        d["changed"] = tok.id in changed
        d["similar"] = 0
        d["similar_link"] = None
        d["left_context"] = tok.left_context or ""
        d["right_context"] = tok.right_context or ""
        tokens_data.append(d)
    return jsonify({
        "tokens": tokens_data,
        "page": tokens.page,
        "pages": tokens.pages,
        "total": tokens.total,
        "per_page": tokens.per_page,
        "bookmark_token_id": None,
    })


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:token_id>')
@login_required
@requires_corpus_access("corpus_id")
def tokens_similar_to_token(corpus_id, token_id):
    mode = request.args.get("mode", "partial")
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    token = WordToken.query.filter_by(**{"id": token_id, "corpus": corpus_id}).first_or_404()
    if request_wants_json():
        tokens = WordToken.get_nearly_similar_to(token, mode=mode)
        if request.args.get("hits", "false").lower() == "true":
            return jsonify([tok.to_dict() for tok in tokens.all()])
        return jsonify({"count": tokens.count()})
    visible_cols = list(corpus.displayed_columns_by_name.keys())
    pyrrha_config = {
        "corpus_id": corpus.id,
        "visible_columns": visible_cols,
        "urls": _corpus_urls(
            corpus,
            data_url=url_for("main.tokens_similar_to_token_data", corpus_id=corpus.id, token_id=token_id, mode=mode)
        ),
    }
    return render_template_with_nav_info(
        'main/tokens_similar_to_token.html',
        corpus=corpus, mode=mode, token=token,
        pyrrha_config=pyrrha_config
    )


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:token_id>/data')
@login_required
@requires_corpus_access("corpus_id")
def tokens_similar_to_token_data(corpus_id, token_id):
    mode = request.args.get("mode", "partial")
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    token = WordToken.query.filter_by(**{"id": token_id, "corpus": corpus_id}).first_or_404()
    tokens = WordToken.get_nearly_similar_to(token, mode=mode).paginate(
        page=int_or(request.args.get("page"), 1),
        per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
    )
    changed = corpus.changed(tokens.items)
    tokens_data = []
    for tok in tokens.items:
        d = tok.to_dict()
        d["changed"] = tok.id in changed
        d["similar"] = 0
        d["similar_link"] = None
        d["left_context"] = tok.left_context or ""
        d["right_context"] = tok.right_context or ""
        tokens_data.append(d)
    return jsonify({
        "tokens": tokens_data,
        "page": tokens.page,
        "pages": tokens.pages,
        "total": tokens.total,
        "per_page": tokens.per_page,
        "bookmark_token_id": None,
    })


@main.route('/corpus/<int:corpus_id>/tokens/correct/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_single(corpus_id, token_id):
    """ Edit a single token values

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    """
    corpus = Corpus.get_or_404(corpus_id)
    try:
        token, change_record = WordToken.update(
            user_id=current_user.id,
            token_id=token_id, corpus_id=corpus_id,
            form=string_to_none(request.form.get("form")),
            lemma=string_to_none(request.form.get("lemma")),
            POS=string_to_none(request.form.get("POS")),
            morph=string_to_none(request.form.get("morph")),
            gloss=string_to_none(request.form.get("gloss"))
        )
        if "similar" in corpus.displayed_columns_by_name:
            similar = {
                "count": change_record.similar_remaining,
                "link": url_for(".tokens_similar_to_record", corpus_id=corpus_id, record_id=change_record.id)
            }
        else:
            similar = None

        return jsonify({
            "token": token.to_dict(),
            "similar": similar
        })
    except WordToken.ValidityError as E:
        response = jsonify({"status": False, "message": E.msg, "details": E.statuses, "new-values": E.invalid_columns})
        response.status_code = 403
        return response
    except WordToken.NothingChangedError as E:
        response = jsonify({"status": False, "message": E.msg, "details": E.statuses})
        response.status_code = 400
        return response


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:record_id>/update', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_from_record(corpus_id, record_id):
    """ Edit posted word_tokens's ids according to a given recorded changes

    :param corpus_id: Id of the record
    :param record_id: Id of the ChangeRecord
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first_or_404()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    changed = record.apply_changes_to(user_id=current_user.id, token_ids=request.json.get("word_tokens"))
    return jsonify([word_token.to_dict() for word_token in changed])


@main.route('/corpus/<int:corpus_id>/tokens/review/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_mark_review(corpus_id, token_id):
    """ Mark or unmark a token for review with an optional comment.

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    """
    token = WordToken.query.filter_by(id=token_id, corpus=corpus_id).first_or_404()
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    needs_review = data.get('needs_review', 'false')
    if isinstance(needs_review, str):
        needs_review = needs_review.lower() == 'true'
    else:
        needs_review = bool(needs_review)
    token.needs_review = needs_review
    token.review_comment = string_to_none(data.get('review_comment')) if needs_review else None
    db.session.add(token)
    db.session.commit()
    return jsonify({"token": token.to_dict()})


@main.route('/corpus/<int:corpus_id>/tokens/needs-review')
@login_required
@requires_corpus_access("corpus_id")
def tokens_needs_review(corpus_id):
    """ Page to edit tokens flagged for review

    :param corpus_id: Id of the corpus
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first_or_404()
    visible_cols = list(corpus.displayed_columns_by_name.keys())
    pyrrha_config = {
        "corpus_id": corpus.id,
        "visible_columns": visible_cols,
        "urls": _corpus_urls(
            corpus,
            data_url=url_for("main.tokens_needs_review_data", corpus_id=corpus.id)
        ),
    }
    return render_template_with_nav_info(
        'main/tokens_needs_review.html',
        corpus=corpus,
        pyrrha_config=pyrrha_config
    )


@main.route('/corpus/<int:corpus_id>/tokens/needs-review/data')
@login_required
@requires_corpus_access("corpus_id")
def tokens_needs_review_data(corpus_id):
    """ JSON endpoint: paginated tokens flagged for review. """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first_or_404()
    tokens = corpus.get_needs_review().paginate(
        page=int_or(request.args.get("page"), 1),
        per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
    )
    changed = corpus.changed(tokens.items)
    tokens_data = []
    for tok in tokens.items:
        d = tok.to_dict()
        d["changed"] = tok.id in changed
        d["similar"] = 0
        d["similar_link"] = None
        d["left_context"] = tok.left_context or ""
        d["right_context"] = tok.right_context or ""
        tokens_data.append(d)
    return jsonify({
        "tokens": tokens_data,
        "page": tokens.page,
        "pages": tokens.pages,
        "total": tokens.total,
        "per_page": tokens.per_page,
        "bookmark_token_id": None,
    })


@main.route('/corpus/<int:corpus_id>/tokens')
@login_required
@requires_corpus_access("corpus_id")
def tokens_export(corpus_id):
    """ Export tokens to CSV

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.get_or_404(corpus_id)
    format = request.args.get("format", "").lower()
    filename = slugify(corpus.name)
    allowed_columns = corpus.displayed_columns_by_name
    if format in ["tsv"]:
        if format == "tsv":
            has_refs = db.session.query(
                WordToken.query.filter(
                    WordToken.corpus == corpus_id,
                    WordToken.token_reference.isnot(None)
                ).exists()
            ).scalar()
            fieldnames = (["token_reference"] if has_refs else []) + ["form", "lemma", "POS", "morph", "gloss"]

            def generate():
                out = StringIO()
                w = DictWriter(out, fieldnames=fieldnames, **TSV_CONFIG)
                w.writeheader()
                yield out.getvalue()
                for tok in corpus.get_tokens().yield_per(500):
                    out = StringIO()
                    w = DictWriter(out, fieldnames=fieldnames, **TSV_CONFIG)
                    row = {"form": tok.form}
                    if has_refs:
                        row["token_reference"] = tok.token_reference or ""
                    for field in ("lemma", "POS", "morph", "gloss"):
                        if field in allowed_columns:
                            row[field] = getattr(tok, field)
                    w.writerow(row)
                    yield out.getvalue()

            return Response(
                response=stream_with_context(generate()),
                status=200,
                content_type="text/tab-separated-values",
                headers={
                    "Content-Disposition": 'attachment; filename="{}.tsv"'.format(filename)
                }
            )
    elif format == "standoff-tei":
        tokens = corpus.get_tokens().all()
        base = tokens[0].id - 1
        return Response(
            stream_with_context(stream_template(
                "tei/standoff.xml",
                base=base,
                tokens=tokens,
                allowed_columns=allowed_columns,
                delimiter=corpus.delimiter_token
            )),
            status=200,
            headers={"Content-Disposition": 'attachment; filename="{}-standoff.xml"'.format(filename)},
            mimetype="text/xml"
        )
    elif format == "tei-geste":
        tokens = corpus.get_tokens().all()
        base = tokens[0].id - 1
        return Response(
            stream_with_context(stream_template(
                "tei/geste.xml",
                base=base,
                tokens=tokens,
                allowed_columns=allowed_columns,
                history=TokenHistory.query.filter_by(corpus=corpus_id).all(),
                delimiter=corpus.delimiter_token
            )),
            status=200,
            headers={"Content-Disposition": 'attachment; filename="{}.xml"'.format(filename)},
            mimetype="text/xml"
        )
    elif format == "tei-msd":
        tokens = corpus.get_tokens().all()
        base = tokens[0].id - 1
        return Response(
            stream_with_context(stream_template(
                "tei/TEI.xml",
                base=base,
                tokens=tokens,
                allowed_columns=allowed_columns,
                history=TokenHistory.query.filter_by(corpus=corpus_id).all(),
                delimiter=corpus.delimiter_token
            )),
            status=200,
            headers={"Content-Disposition": 'attachment; filename="{}.xml"'.format(filename)},
            mimetype="text/xml"
        )
    return render_template_with_nav_info(
        template="main/tokens_export.html",
        corpus=corpus
    )


@main.route('/corpus/get/<int:corpus_id>/history')
@login_required
@requires_corpus_access("corpus_id")
def _tokens_history_compat(corpus_id):
    return redirect(url_for('main.tokens_history', corpus_id=corpus_id), 301)


@main.route('/corpus/<int:corpus_id>/tokens/history')
@login_required
@requires_corpus_access("corpus_id")
def tokens_history(corpus_id):
    """ History of changes in the corpus

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.get_or_404(corpus_id)
    tokens = corpus.get_history(page=int_or(request.args.get("page"), 1), limit=int_or(request.args.get("limit"), 20))
    return render_template_with_nav_info('main/tokens_history.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/history/download')
@login_required
@requires_corpus_access("corpus_id")
def tokens_history_download(corpus_id):
    """ Download annotation history of the corpus as TSV

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.get_or_404(corpus_id)
    visible = corpus.displayed_columns_by_name
    filename = slugify(corpus.name)

    fieldnames = ["user", "edit", "context"]
    for col in ("lemma", "POS", "morph", "gloss"):
        if col in visible:
            fieldnames += [col + "_old", col + "_new"]

    def generate():
        output = StringIO()
        writer = DictWriter(output, fieldnames=fieldnames, **TSV_CONFIG)
        writer.writeheader()
        yield output.getvalue()

        records = (
            ChangeRecord.query
            .filter_by(corpus=corpus_id)
            .order_by(ChangeRecord.created_on.desc())
            .options(selectinload(ChangeRecord.word_token), selectinload(ChangeRecord.user))
            .yield_per(500)
        )
        for record in records:
            output = StringIO()
            writer = DictWriter(output, fieldnames=fieldnames, **TSV_CONFIG)
            ctx = ""
            if record.word_token:
                ctx = "{} {} {}".format(
                    record.word_token.left_context or "",
                    record.word_token.form,
                    record.word_token.right_context or ""
                ).strip()
            row = {
                "user": "{}.{}".format(record.user.first_name[0], record.user.last_name),
                "edit": record.created_on.isoformat(),
                "context": ctx,
            }
            for col in ("lemma", "POS", "morph", "gloss"):
                if col in visible:
                    row[col + "_old"] = getattr(record, col) or ""
                    row[col + "_new"] = getattr(record, col + "_new") or ""
            writer.writerow(row)
            yield output.getvalue()

    return Response(
        response=stream_with_context(generate()),
        status=200,
        content_type="text/tab-separated-values",
        headers={
            "Content-Disposition": 'attachment; filename="{}-history.tsv"'.format(filename)
        }
    )


def _search_token_dict(form):
    return {
        key: value
        for key, value in form.items()
        if key not in {"caseBox", "page", "limit", "orderBy", "desc"}
    }


@main.route('/corpus/<int:corpus_id>/tokens/search', methods=["POST", "GET"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_search_through_fields(corpus_id):
    """ Page to search tokens through fields (Form, POS, Lemma, Morph) within a corpus

    :param corpus_id: Id of the corpus
    """
    corpus = Corpus.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)

    form: Dict[str, str] = request.form if request.method == "POST" else request.args
    token_dict = _search_token_dict(form)

    # Only extract prefill values for the search form — no DB query on the shell view
    input_values = {k: string_to_none(form.get(k)) for k in ('form', 'lemma', 'POS', 'morph')}
    input_values = {k: v for k, v in input_values.items() if v}

    visible_cols = list(corpus.displayed_columns_by_name.keys())
    pyrrha_config = {
        "corpus_id": corpus.id,
        "visible_columns": visible_cols,
        "urls": _corpus_urls(
            corpus,
            data_url=url_for("main.tokens_search_data", corpus_id=corpus.id)
        ),
    }

    return render_template_with_nav_info(
        'main/tokens_search_through_fields.html',
        corpus=corpus,
        pyrrha_config=pyrrha_config,
        has_results=bool(token_dict),
        orderBy=request.args.get("orderBy", "order_id"),
        desc=request.args.get("desc", "0"),
        **input_values
    )


@main.route('/corpus/<int:corpus_id>/tokens/search/data')
@login_required
@requires_corpus_access("corpus_id")
def tokens_search_data(corpus_id):
    """ JSON endpoint: paginated search results for the annotation table. """
    corpus = Corpus.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)

    token_dict = _search_token_dict(request.args)
    if not token_dict:
        return jsonify({"tokens": [], "page": 1, "pages": 0, "total": 0, "per_page": 100, "bookmark_token_id": None})

    tokens_q, _, _ = corpus.token_search(
        token_dict=token_dict,
        case_sensitive='caseBox' not in request.args,
        desc=int(request.args.get("desc", "0"))
    )
    tokens = tokens_q.paginate(
        page=int_or(request.args.get("page"), 1),
        per_page=int_or(request.args.get("limit"), 100)
    )

    if "similar" in corpus.displayed_columns_by_name:
        WordToken.get_similar_for_batch(corpus, tokens.items)

    changed = corpus.changed(tokens.items)
    tokens_data = []
    for tok in tokens.items:
        d = tok.to_dict()
        d["changed"] = tok.id in changed
        d["similar"] = getattr(tok, "similar", 0)
        d["similar_link"] = url_for(
            "main.tokens_similar_to_token", corpus_id=corpus.id, token_id=tok.id
        ) if d["similar"] else None
        d["left_context"] = tok.left_context or ""
        d["right_context"] = tok.right_context or ""
        tokens_data.append(d)

    return jsonify({
        "tokens": tokens_data,
        "page": tokens.page,
        "pages": tokens.pages,
        "total": tokens.total,
        "per_page": tokens.per_page,
        "bookmark_token_id": None,
    })


@main.route('/corpus/<int:corpus_id>/tokens/edit/<int:token_id>', methods=["GET", "POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_form(corpus_id, token_id):
    """ Page to edit the form of a token

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    """
    corpus = Corpus.get_or_404(corpus_id)
    token = WordToken.query.filter_by(**{"corpus": corpus_id, "id": token_id}).first_or_404()
    page = math.floor(token.order_id / current_app.config["PAGINATION_DEFAULT_TOKENS"]) + 1
    go_back_url = url_for(".tokens_correct", corpus_id=corpus_id, page=page) + "#tok" + str(token.order_id)
    if request.method == "POST" and request.form.get("form"):
        token.edit_form(request.form.get("form"), corpus=corpus, user=current_user)
        flash("The form has been updated.", category="success")
        return redirect(go_back_url)
    return render_template_with_nav_info(
        "main/tokens_edit_form.html", corpus=corpus, token=token,
        go_back=go_back_url
    )


@main.route('/corpus/<int:corpus_id>/tokens/remove/<int:token_id>', methods=["GET", "POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_del_row(corpus_id, token_id):
    """

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    :return:
    """
    corpus = Corpus.get_or_404(corpus_id)
    token = WordToken.query.filter_by(**{"corpus": corpus_id, "id": token_id}).first_or_404()
    page = math.floor(token.order_id / current_app.config["PAGINATION_DEFAULT_TOKENS"]) + 1
    go_back_url = url_for(".tokens_correct", corpus_id=corpus_id, page=page) + "#tok" + str(token.order_id)

    if request.method == "POST":
        if request.form.get("form") == token.form:
            token.del_form(corpus=corpus, user=current_user)
            flash("The form has been deleted.", category="success")
        else:
            flash("The form was not matched", category="error")
        return redirect(go_back_url)

    return render_template_with_nav_info(
        "main/tokens_del_row.html", corpus=corpus, token=token,
        go_back=go_back_url
    )


@main.route('/corpus/<int:corpus_id>/tokens/insert/<int:token_id>', methods=["GET", "POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_add_row(corpus_id, token_id):
    """

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    :return:
    """
    corpus = Corpus.get_or_404(corpus_id)
    token = WordToken.query.filter_by(**{"corpus": corpus_id, "id": token_id}).first_or_404()
    page = math.floor(token.order_id / current_app.config["PAGINATION_DEFAULT_TOKENS"]) + 1
    go_back_url = url_for(".tokens_correct", corpus_id=corpus_id, page=page) + "#tok" + str(token.order_id)

    if request.method == "POST" and request.form.get("form"):
        token.add_form(request.form.get("form"), corpus=corpus, user=current_user)
        flash("The form has been updated.", category="success")
        return redirect(go_back_url)

    return render_template_with_nav_info(
        "main/tokens_add_row.html", corpus=corpus, token=token,
        go_back=go_back_url
    )


@main.route('/corpus/<int:corpus_id>/tokens/modifications_history', methods=["GET"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_history(corpus_id):
    """

    :param corpus_id: Id of the corpus
    :return:
    """
    corpus = Corpus.get_or_404(corpus_id)
    tokens = TokenHistory.query.filter_by(corpus=corpus.id).paginate(
            page=int_or(request.args.get("page"), 1),
            per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
        )
    return render_template_with_nav_info("main/tokens_edit_history.html", corpus=corpus,
                                         tokens=tokens)
