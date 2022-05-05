from flask import request, jsonify, url_for, abort, render_template, current_app, redirect, flash, Response, \
    stream_with_context
from flask_login import current_user, login_required
from slugify import slugify
from sqlalchemy.sql.elements import or_, and_, not_
from sqlalchemy import func
import math
from csv import DictWriter

from .utils import render_template_with_nav_info, request_wants_json, requires_corpus_access
from .. import main
from ... import db
from ...models import WordToken, Corpus, ChangeRecord, TokenHistory, Bookmark, CorpusCustomDictionary
from ...utils.forms import string_to_none, strip_or_none, column_search_filter, prepare_search_string
from ...utils.pagination import int_or
from ...utils.tsv import TSV_CONFIG, stream_tsv
from ...utils.tsv import TSV_CONFIG, stream_tsv
from ...utils.response import stream_template
from io import StringIO
from itertools import product


@main.route('/corpus/<int:corpus_id>/tokens/correct')
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct(corpus_id):
    """ Page to edit word tokens

    :param corpus_id: Id of the corpus
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    current_user.bookmark: Bookmark = corpus.get_bookmark(current_user)

    tokens = corpus\
        .get_tokens()\
        .paginate(
            page=int_or(request.args.get("page"), 1),
            per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
        )

    if "similar" in corpus.displayed_columns_by_name:
        WordToken.get_similar_for_batch(corpus, tokens.items)

    changed = corpus.changed(tokens.items)

    return render_template_with_nav_info('main/tokens_correct.html', corpus=corpus, tokens=tokens, changed=changed)


@main.route('/corpus/<int:corpus_id>/tokens/unallowed/<allowed_type>/correct')
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_unallowed(corpus_id, allowed_type):
    """ Page to edit tokens that have unallowed values

    :param corpus_id: Id of the corpus
    :param allowed_type: Type of allowed value to check agains (lemma, POS, morph)
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus\
        .get_unallowed(allowed_type)\
        .paginate(
            page=int_or(request.args.get("page"), 1),
            per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
        )
    return render_template_with_nav_info(
        'main/tokens_correct_unallowed.html',
        corpus=corpus,
        tokens=tokens,
        allowed_type=allowed_type,
        changed=corpus.changed(tokens.items)
    )


@main.route('/corpus/<int:corpus_id>/tokens/changes/similar/<int:record_id>')
@login_required
@requires_corpus_access("corpus_id")
def tokens_similar_to_record(corpus_id, record_id):
    """ Find similar tokens to old values behind a changerecord

    :param corpus_id: ID of the corpus
    :param record_id: Id of the change record
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    record = ChangeRecord.query.filter_by(**{"id": record_id}).first_or_404()
    tokens = WordToken.get_similar_to_record(change_record=record).paginate(per_page=1000)
    return render_template_with_nav_info(
        # The Dict is a small hack to emulate paginate
        'main/tokens_similar_to_record.html', corpus=corpus, tokens=tokens, record=record,
        changed=corpus.changed(tokens.items)
    )


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:token_id>')
@login_required
@requires_corpus_access("corpus_id")
def tokens_similar_to_token(corpus_id, token_id):
    """ Find tokens similar to a given tokens

    :param corpus_id: Id of the corpus
    :param token_id: Id of the tokens


    .. note:: Takes a mode GET argument (default : partial) that sets the way matching are effected
    """
    mode = request.args.get("mode", "partial")
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    token = WordToken.query.filter_by(**{"id": token_id, "corpus": corpus_id}).first_or_404()
    tokens = WordToken.get_nearly_similar_to(token, mode=mode)
    if request_wants_json():
        if request.args.get("hits", "false").lower() == "true":
            return jsonify([
                tok.to_dict() for tok in tokens.all()
            ])
        return jsonify({"count": tokens.count()})
    tokens = tokens.paginate(per_page=1000)
    return render_template_with_nav_info(
        # The Dict is a small hack to emulate paginate
        'main/tokens_similar_to_token.html',
        corpus=corpus, tokens=tokens, mode=mode, token=token,
        changed=corpus.changed(tokens.items)
    )


@main.route('/corpus/<int:corpus_id>/tokens/correct/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_correct_single(corpus_id, token_id):
    """ Edit a single token values

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    try:
        token, change_record = WordToken.update(
            user_id=current_user.id,
            token_id=token_id, corpus_id=corpus_id,
            lemma=string_to_none(request.form.get("lemma")),
            POS=string_to_none(request.form.get("POS")),
            morph=string_to_none(request.form.get("morph"))
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


@main.route('/corpus/<int:corpus_id>/tokens')
@login_required
@requires_corpus_access("corpus_id")
def tokens_export(corpus_id):
    """ Export tokens to CSV

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    format = request.args.get("format", "").lower()
    filename = slugify(corpus.name)
    allowed_columns = corpus.displayed_columns_by_name
    if format in ["tsv"]:
        tokens = corpus.get_tokens().all()
        if format == "tsv":
            output = StringIO()
            fieldnames = ["form", "lemma", "POS", "morph"]
            writer = DictWriter(output, fieldnames=fieldnames, **TSV_CONFIG)
            writer.writeheader()
            for tok in tokens:
                row = {"form": tok.form}
                for field in ("lemma", "POS", "morph"):
                    if field in allowed_columns:
                        row[field] = getattr(tok, field)
                writer.writerow(row)
            output.seek(0)
            return Response(
                response=stream_with_context(stream_tsv(output)),
                status=200,
                content_type="text/tab-separated-values",
                headers={
                    "Content-Disposition": 'attachment; filename="{}.tsv"'.format(filename)
                }
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
def tokens_history(corpus_id):
    """ History of changes in the corpus

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = corpus.get_history(page=int_or(request.args.get("page"), 1), limit=int_or(request.args.get("limit"), 20))
    return render_template_with_nav_info('main/tokens_history.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/search', methods=["POST", "GET"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_search_through_fields(corpus_id):
    """ Page to search tokens through fields (Form, POS, Lemma, Morph) within a corpus

    :param corpus_id: Id of the corpus
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)

    columns = tuple(["form"] + [
        col if col == "POS" else col.lower()
        for col in corpus.get_columns_headings()
    ])

    input_values = {}

    # make a dict with values splitted for each OR operator
    fields = {}
    source_dict = request.form if request.method == "POST" else request.args

    for name in columns:
        value = strip_or_none(source_dict.get(name))
        input_values[name] = value

        # split values with the '|' OR operator but keep escaped '\|' ones
        fields[name] = prepare_search_string(value) if value is not None else ""

    # all search combinations
    search_branches = [
        dict(prod)
        for prod in product(*[
            [
                (field, value)
                for value in fields[field]
            ]
            for field in fields
        ])
    ]

    value_filters = []
    # for each branch filter (= OR clauses if any)
    for search_branch in search_branches:
        branch_filters = [WordToken.corpus == corpus_id]

        # for each field (lemma, pos, form, morph)
        for name, value in search_branch.items():
            branch_filters.extend(column_search_filter(getattr(WordToken, name), value))

        value_filters.append(branch_filters)

    if not value_filters:  # If the search is empty, we only search for the corpus_id
        value_filters.append([WordToken.corpus == corpus_id])

    # there is at least one OR clause
    # get sort arguments (sort per default by WordToken.order_id)
    order_by_key = request.args.get("orderBy")
    order_by = {
        "order_id": WordToken.order_id,
        "lemma": func.lower(WordToken.lemma),
        "pos": func.lower(WordToken.POS),
        "form": func.lower(WordToken.form),
        "morph": func.lower(WordToken.morph),
     }
    if order_by_key not in order_by:
        order_by_key = "order_id"
    order_by = order_by.get(order_by_key)

    args = []

    if len(value_filters) > 1:
        and_filters = [and_(*branch_filters) for branch_filters in value_filters]
        args = [or_(*and_filters)]
    elif len(value_filters) == 1:
        args = value_filters[0]

    tokens = WordToken.query.filter(*args).order_by(
        order_by.desc()
        if bool(int(request.args.get("desc", "0")))  # default sort order is ascending
        else order_by
    )

    page = int_or(request.args.get("page"), 1)
    per_page = int_or(request.args.get("limit"), 100)
    tokens = tokens.paginate(page=page, per_page=per_page)

    return render_template_with_nav_info('main/tokens_search_through_fields.html',
                                         search_kwargs={"corpus_id": corpus.id, **input_values},
                                         changed=corpus.changed(tokens.items),
                                         desc=request.args.get("desc", "0"),
                                         orderBy=order_by_key,
                                         corpus=corpus, tokens=tokens, **input_values)


@main.route('/corpus/<int:corpus_id>/tokens/edit/<int:token_id>', methods=["GET", "POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_form(corpus_id, token_id):
    """ Page to edit the form of a token

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    """
    corpus = Corpus.query.get_or_404(corpus_id)
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
    corpus = Corpus.query.get_or_404(corpus_id)
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
    corpus = Corpus.query.get_or_404(corpus_id)
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
    corpus = Corpus.query.get_or_404(corpus_id)
    tokens = TokenHistory.query.filter_by(corpus=corpus.id).paginate(
            page=int_or(request.args.get("page"), 1),
            per_page=int_or(request.args.get("limit"), current_app.config["PAGINATION_DEFAULT_TOKENS"])
        )
    return render_template_with_nav_info("main/tokens_edit_history.html", corpus=corpus,
                                         tokens=tokens)
