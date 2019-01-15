from flask import request, jsonify, url_for, abort, render_template
from flask_login import current_user, login_required
from sqlalchemy.sql.elements import or_, and_

from .utils import render_template_with_nav_info, request_wants_json, requires_corpus_access
from .. import main
from ...models import WordToken, Corpus, ChangeRecord
from ...utils.forms import string_to_none, strip_or_none, column_search_filter, prepare_search_string
from ...utils.pagination import int_or


@main.route('/corpus/<int:corpus_id>/tokens/edit')
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit(corpus_id):
    """ Page to edit word tokens

    :param corpus_id: Id of the corpus
    """
    corpus = Corpus.query.filter_by(**{"id": corpus_id}).first()
    tokens = corpus\
        .get_tokens()\
        .paginate(page=int_or(request.args.get("page"), 1), per_page=int_or(request.args.get("limit"), 100))

    maps = {}
    for token in tokens.items:
        key = (token.form, token.lemma, token.POS, token.morph)
        if key not in maps:
            maps[key] = \
                WordToken.similar_as(corpus.id, *key)
        token.similar = maps[key]

    return render_template_with_nav_info('main/tokens_edit.html', corpus=corpus, tokens=tokens)


@main.route('/corpus/<int:corpus_id>/tokens/unallowed/<allowed_type>/edit')
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_unallowed(corpus_id, allowed_type):
    """ Page to edit tokens that have unallowed values

    :param corpus_id: Id of the corpus
    :param allowed_type: Type of allowed value to check agains (lemma, POS, morph)
    """
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
        'main/tokens_similar_to_record.html', corpus=corpus, tokens=tokens, record=record
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
    return render_template_with_nav_info(
        # The Dict is a small hack to emulate paginate
        'main/tokens_similar_to_token.html',
        corpus=corpus, tokens=tokens.paginate(per_page=1000), mode=mode, token=token
    )


@main.route('/corpus/<int:corpus_id>/tokens/edit/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_single(corpus_id, token_id):
    """ Edit a single token values

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    try:
        token, change_record = WordToken.update(
            user_id=current_user.id,
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
        response.status_code = 400
        return response


@main.route('/corpus/<int:corpus_id>/tokens/similar/<int:record_id>/update', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_from_record(corpus_id, record_id):
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
    format = request.args.get("format")
    if format in ["tsv"]:
        tokens = corpus.get_tokens().all()
        if format == "tsv":
            headers = ["\t".join(["form", "lemma", "POS", "morph"])]
            return "\n".join(headers+[tok.tsv for tok in tokens]), \
                   200, \
                   {
                       "Content-Type": "text/tab-separated-values; charset= utf-8",
                       "Content-Disposition": 'attachment; filename="pyrrha-correction.tsv"'
                   }
    elif format in ["tei", "tei-geste"]:
        tokens = corpus.get_tokens().all()
        base = tokens[0].id - 1
        #if format == "tei-geste": Right now only 1 format
        response = render_template("tei/geste.xml", base=base, tokens=tokens, delimiter=corpus.delimiter_token)
        return response, 200, {
           "Content-Type": "text/xml; charset= utf-8",
           "Content-Disposition": 'attachment; filename="pyrrha-correction.xml"'
        }

    return render_template_with_nav_info(
        template="main/tokens_view.html",
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

    kargs = {}

    # make a dict with values splitted for each OR operator
    fields = {}
    for name in ("lemma", "form", "POS", "morph"):
        if request.method == "POST":
            value = strip_or_none(request.form.get(name))
        else:
            value = strip_or_none(request.args.get(name))
        # split values with the '|' OR operator but keep escaped '\|' ones
        if value is None:
            fields[name] = ""
        else:
            fields[name] = prepare_search_string(value)
        kargs[name] = value

    # all search combinations
    search_branches = [
        {"lemma": lemma, "form": form, "POS": pos, "morph": morph}
        for lemma in fields["lemma"]
        for form in fields["form"]
        for pos in fields["POS"]
        for morph in fields["morph"]
    ]

    value_filters = []
    # for each branch filter (= OR clauses if any)
    for search_branch in search_branches:
        branch_filters = [WordToken.corpus == corpus_id]

        # for each field (lemma, pos, form, morph)
        for name, value in search_branch.items():
            branch_filters.extend(column_search_filter(getattr(WordToken, name), value))

        value_filters.append(branch_filters)

    # there is at least one OR clause
    if len(value_filters) > 1:
        and_filters = [and_(*branch_filters) for branch_filters in value_filters]
        flattened_filters = or_(*and_filters)
        tokens = WordToken.query.filter(flattened_filters).order_by(WordToken.order_id)
    else:
        if len(value_filters) == 1:
            value_filters = value_filters[0]
        tokens = WordToken.query.filter(*value_filters).order_by(WordToken.order_id)

    page = int_or(request.args.get("page"), 1)
    per_page = int_or(request.args.get("limit"), 100)
    tokens = tokens.paginate(page=page, per_page=per_page)

    return render_template_with_nav_info('main/tokens_search_through_fields.html',
                                         corpus=corpus, tokens=tokens, **kargs)


@main.route('/corpus/<int:corpus_id>/tokens/correct/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_edit_form(corpus_id, token_id):
    """

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    :return:
    """
    corpus = Corpus.query.get_or_404(corpus_id)


@main.route('/corpus/<int:corpus_id>/tokens/correct/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_remove_row(corpus_id, token_id):
    """

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    :return:
    """
    corpus = Corpus.query.get_or_404(corpus_id)


@main.route('/corpus/<int:corpus_id>/tokens/correct/<int:token_id>', methods=["POST"])
@login_required
@requires_corpus_access("corpus_id")
def tokens_add_row(corpus_id, token_id):
    """

    :param corpus_id: Id of the corpus
    :param token_id: Id of the token
    :return:
    """
    corpus = Corpus.query.get_or_404(corpus_id)

