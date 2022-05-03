from flask import request, flash, redirect, url_for, abort, current_app, jsonify
from flask_login import current_user, login_required
import sqlalchemy.exc
from sqlalchemy import func, distinct, text
from typing import List


from app import db

from app.models import CorpusUser, ControlLists, ControlListsUser, WordToken, ChangeRecord, Bookmark, Favorite, User, \
    CorpusCustomDictionary

from .utils import render_template_with_nav_info
from app.utils import ValidationError
from app.utils.forms import create_input_format_convertion, read_input_tokens
from .. import main
from ...utils.forms import strip_or_none
from ...models import Corpus, Column
from ...utils.response import format_api_like_reply
from ...errors import MissingTokenColumnValue, NoTokensInput
from .utils import requires_corpus_admin_access, requires_corpus_access
from ..forms import Delete
from app.utils import PreferencesUpdateError, PersonalDictionaryError

AUTOCOMPLETE_LIMIT = 20


def _get_available():
    """Prepare dictionary of available control lists.

    :returns: available control lists
    :rtype: dict
    """
    lists = {"public": [], "submitted": [], "private": []}
    for cl in ControlLists.get_available(current_user):
        lists[cl.str_public].append(cl)
    return lists


@main.route('/corpus/new', methods=["POST", "GET"])
@login_required
def corpus_new():
    """ Register a new corpus
    """
    lemmatizers = current_app.config.get("LEMMATIZERS", [])

    def normal_view():
        return render_template_with_nav_info(
            'main/corpus_new.html',
            lemmatizers=lemmatizers,
            public_control_lists=_get_available(),
            tsv=request.form.get("tsv", "")
        )

    def error():
        return normal_view(), 400

    if request.method == "POST":
        if not current_user.is_authenticated:
            abort(403)
        elif not len(strip_or_none(request.form.get("name", ""))):
            flash("You forgot to give a name to your corpus", category="error")
            return error()
        else:
            form_kwargs = {
                "name": request.form.get("name"),
                "context_left": request.form.get("context_left", None),
                "context_right": request.form.get("context_right", None),
                "delimiter_token": strip_or_none(request.form.get("sep_token", "")) or None,
                "columns": [
                    Column(heading="Lemma"),
                    Column(heading="POS"),
                    Column(heading="Morph"),
                    Column(heading="Similar"),
                ]
            }
            for column in form_kwargs["columns"]:
                column.hidden = bool(
                    request.form.get(f"{column.heading.lower()}Column", "")
                )
            if (
                "lemmaColumn" in request.form
                and "posColumn" in request.form
                and "morphColumn" in request.form
            ):
                flash(
                    "You can't disable Lemma and POS and Morph. Keep at least one of them.",
                    category="error"
                )
                return error()

            if request.form.get("control_list") == "reuse":
                tokens = read_input_tokens(request.form.get("tsv"))
                try:
                    control_list = ControlLists.query.get_or_404(request.form.get("control_list_select"))
                except Exception:
                    flash("This control list does not exist", category="error")
                    return error()
                form_kwargs.update({"word_tokens_dict": tokens,
                                    "control_list": control_list})
                cl_owner = False
            else:
                tokens, allowed_lemma, allowed_morph, allowed_POS = create_input_format_convertion(
                    request.form.get("tsv"),
                    request.form.get("allowed_lemma", None),
                    request.form.get("allowed_morph", None),
                    request.form.get("allowed_POS", None)
                )
                cl_owner = True
                form_kwargs.update({"word_tokens_dict": tokens, "allowed_lemma": allowed_lemma,
                                    "allowed_POS": allowed_POS, "allowed_morph": allowed_morph})

            try:
                corpus: Corpus = Corpus.create(**form_kwargs)
                db.session.add(CorpusUser(corpus=corpus, user=current_user, is_owner=True))
                # Add a link to the control list
                ControlLists.link(corpus.control_lists_id, current_user.id, is_owner=cl_owner)
                db.session.commit()
                flash("New corpus registered", category="success")
            except (sqlalchemy.exc.StatementError, sqlalchemy.exc.IntegrityError) as e:
                db.session.rollback()
                flash("The corpus cannot be registered. Check your data", category="error")
                if str(e.orig) == "UNIQUE constraint failed: corpus.name":
                    flash("You have already a corpus going by the name {}".format(request.form.get("name")),
                          category="error")
                return error()
            except MissingTokenColumnValue as exc:
                db.session.rollback()
                flash("At least one line of your corpus is missing a token/form. Check line %s " % exc.line,
                      category="error")
                return error()
            except NoTokensInput:
                db.session.rollback()
                flash("You did not input any text.", category="error")
                return error()
            except ValidationError as exception:
                db.session.rollback()
                flash(exception, category="error")
                return error()
            except Exception as e:
                db.session.rollback()
                flash("The corpus cannot be registered. Check your data", category="error")
                return error()
            return redirect(url_for(".corpus_get", corpus_id=corpus.id))

    return normal_view()


@main.route('/corpus/favorite/<int:corpus_id>')
@login_required
@requires_corpus_access("corpus_id")
def corpus_fav(corpus_id):
    """ Mark a corpus as favorite """
    corpus = Corpus.query.get_or_404(corpus_id)
    corpus.toggle_favorite(current_user.id)
    return redirect(url_for("main.index"))


@main.route('/corpus/get/<int:corpus_id>')
@login_required
@requires_corpus_access("corpus_id")
def corpus_get(corpus_id):
    """ Main page about the corpus

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.query.get_or_404(corpus_id)

    limit_corr = request.args.get("limit", 10)
    if isinstance(limit_corr, str):
        if limit_corr.isnumeric():
            limit_corr = min(int(limit_corr), 100)
            limit_corr = max(10, limit_corr)
        else:
            limit_corr = 10

    if "lemma" in corpus.displayed_columns_by_name:
        lemma_cor = db.session.query(
                func.count(ChangeRecord.lemma_new).label("record_count"),
                ChangeRecord.lemma_new,
                ChangeRecord.lemma
            ).group_by(
                ChangeRecord.lemma_new, ChangeRecord.lemma
            ).filter(
                ChangeRecord.corpus == corpus.id,
                ChangeRecord.lemma_new != ChangeRecord.lemma
            ).order_by(
                text("record_count DESC")
            ).limit(limit_corr).all()
    else:
        lemma_cor = None
    if "morph" in corpus.displayed_columns_by_name:
        morph_cor = db.session.query(
                func.count(ChangeRecord.morph_new).label("record_count"),
                ChangeRecord.morph_new,
                ChangeRecord.morph
            ).group_by(
                ChangeRecord.morph_new, ChangeRecord.morph
            ).filter(
                ChangeRecord.corpus == corpus.id,
                ChangeRecord.morph_new != ChangeRecord.morph
            ).order_by(
                text("record_count DESC")
            ).limit(limit_corr).all()
    else:
        morph_cor = None
    if "POS" in corpus.displayed_columns_by_name:
        pos_cor = db.session.query(
                func.count(ChangeRecord.POS_new).label("record_count"),
                ChangeRecord.POS_new,
                ChangeRecord.POS
            ).group_by(
                ChangeRecord.POS, ChangeRecord.POS_new
            ).filter(
                ChangeRecord.corpus == corpus.id,
                ChangeRecord.POS_new != ChangeRecord.POS
            ).order_by(
                text("record_count DESC")
            ).limit(limit_corr).all()
    else:
        pos_cor = None
    return render_template_with_nav_info('main/corpus_info.html', corpus=corpus, stats=corpus.statistics,
                                         lemma_cor=lemma_cor, pos_cor=pos_cor, morph_cor=morph_cor)


@main.route("/corpus/<int:corpus_id>/bookmark")
@login_required
@requires_corpus_access("corpus_id")
def corpus_bookmark(corpus_id):
    token = request.args.get("token_id", None)
    page = request.args.get("page", None)
    if token and page:
        bm = Bookmark.mark(corpus_id, current_user.id, token, page)
        link = "{uri}#token_{token}_row".format(
            uri=url_for("main.tokens_correct", corpus_id=corpus_id, page=bm.page),
            token=bm.token_id
        )
    else:
        bm = Corpus.query.get_or_404(corpus_id).get_bookmark(current_user)
        if bm:
            link = "{uri}#token_{token}_row".format(
                uri=url_for("main.tokens_correct", corpus_id=corpus_id, page=bm.page),
                token=bm.token_id
            )
        else:
            flash("No bookmark found for this corpus on your account", category="warning")
            link = url_for("main.tokens_correct", corpus_id=corpus_id)
    return redirect(link)


@main.route('/corpus/<int:corpus_id>/delete', methods=["GET", "POST"])
@requires_corpus_admin_access("corpus_id")
def corpus_delete(corpus_id: int):
    corpus = Corpus.query.get_or_404(corpus_id)

    form = Delete(prefix="delete")
    if request.method == "POST" and form.validate():
        if form.name.data == corpus.name.strip():
            # Enjoy cascade deletion
            db.session.delete(corpus)
            db.session.commit()
            flash("The corpus has been removed", category="success")
            return redirect(url_for(".index"))
        else:
            flash("The corpus name you entered is not the one expected.", category="error")
    return render_template_with_nav_info(
        template="main/corpus_delete.html", corpus=corpus, form=form
    )


def switch_control_lists_access(
    corpus: Corpus,
    users: List[User],
    old_control_lists_id: int,
):
    """Switch user access from one control list to another.

    :param list users: list of users to switch
    :param int old_control_lists_id: ID of old control list
    """
    for user in users:
        # do not delete access to old control list if another corpus uses it
        for user_corpus in Corpus.for_user(user):
            if user_corpus.control_lists_id == old_control_lists_id and user_corpus.id != corpus.id:
                break
        else:
            control_lists_user = ControlListsUser.query.filter(
                ControlListsUser.control_lists_id == old_control_lists_id,
                ControlListsUser.user_id == user.id,
            ).one_or_none()
            # do not delete access to old control list if user is owner
            if control_lists_user and not control_lists_user.is_owner:
                db.session.delete(control_lists_user)
        # add access to new control list
        ControlLists.link(corpus.control_lists_id, user.id)
    db.session.commit()


@main.route('/corpus/<int:corpus_id>/switch_cl', methods=["GET"])
@login_required
@requires_corpus_admin_access("corpus_id")
def control_list_switch(corpus_id: int):
    """Switch control list."""
    corpus = Corpus.query.get_or_404(corpus_id)
    current_control_lists = ControlLists.query.get_or_404(corpus.control_lists_id)
    if request.args.get("control_list_select"):
        try:
            control_list = ControlLists.query.get_or_404(
                request.args.get("control_list_select")
            )
            users = [
                current_user,
                *[
                    User.query.filter(User.id == corpus_user.user_id).one()
                    for corpus_user in CorpusUser.query.filter(CorpusUser.corpus_id == corpus_id)
                ]
            ]
            corpus.control_lists_id = control_list.id
            switch_control_lists_access(corpus, users, current_control_lists.id)
            flash(
                "The control list has been switched to {}".format(control_list.name),
                category="success"
            )
            current_control_lists = control_list
        except Exception:
            db.session.rollback()
            flash(
                "An unknown error occurred, the control list has not been switched",
                category="error"
            )
    return render_template_with_nav_info(
        template="main/control_list_switch.html",
        public_control_lists=_get_available(),
        current_control_lists=current_control_lists
    )



@main.route('/corpus/<int:corpus_id>/fixtures')
def generate_fixtures(corpus_id):
    corpus = Corpus.query.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)
    tokens = corpus.get_tokens().all()
    allowed_lemma = corpus.get_allowed_values(allowed_type="lemma")
    allowed_POS = corpus.get_allowed_values(allowed_type="POS")
    return render_template_with_nav_info(
        template="main/corpus_generate_fixtures.html", tokens=tokens,
        allowed_lemma=allowed_lemma, allowed_pos=allowed_POS
    )


@main.route('/corpus/<int:corpus_id>/api/<allowed_type>')
def search_value_api(corpus_id, allowed_type):
    """ Find allowed values

    :param corpus_id: Id of the Corpus
    :param allowed_type: Type of allowed value (lemma, morph, POS)
    """
    form = request.args.get("form", "")
    if not form.strip():
        return jsonify([])
    corpus = Corpus.query.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)
    return jsonify(
        [
            format_api_like_reply(result, allowed_type)
            for result in WordToken.get_like(
                filter_id=corpus_id,
                form=form,
                group_by=True,
                type_like=allowed_type,
                allowed_list=False
            ).limit(AUTOCOMPLETE_LIMIT)
            if result is not None
        ]
    )


@main.route('/corpus/<int:corpus_id>/api/custom-dictionary/<category>')
def custom_dictionary_search_value_api(corpus_id, category):
    """ Find values in the corpus custom dictionary

    :param corpus_id: Id of the Corpus
    :param category: Type of value (lemma, morph, POS)
    """
    form = request.args.get("form", "")
    if not form.strip():
        return jsonify([])
    corpus = Corpus.query.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)
    return jsonify(
        [
            format_api_like_reply(result, category)
            for result in CorpusCustomDictionary.get_like(
                corpus_id=corpus_id,
                form=form,
                group_by=True,
                category=category
            ).limit(AUTOCOMPLETE_LIMIT)
            if result is not None
        ]
    )


@main.route("/corpus/<int:corpus_id>/preferences", methods=["GET", "POST"])
@login_required
@requires_corpus_access("corpus_id")
def preferences(corpus_id: int):
    """Show preferences view."""
    corpus = Corpus.query.get_or_404(corpus_id)
    corpus_user = CorpusUser.query.filter(
        CorpusUser.corpus_id == corpus_id,
        CorpusUser.user_id == current_user.id
    ).one_or_none()
    if corpus_user:
        is_owner = corpus_user.is_owner
    else:
        is_owner = current_user.id in (admin.id for admin in User.get_admins())
    if is_owner and request.method == "POST":
        context_left = corpus.context_left
        context_right = corpus.context_right
        new_context_left = int(request.form.get("context_left", context_left))
        new_context_right = int(request.form.get("context_right", context_right))
        try:
            corpus.update_delimiter_token(
                delimiter_token=request.form.get("sep_token", "").strip()
            )
            corpus.update_contexts(
                context_left=new_context_left,
                context_right=new_context_right,
            )
            corpus.update_columns(
                {
                    column.heading.lower(): bool(request.form.get(f"{column.heading.lower()}Column", ""))
                    for column in corpus.columns
                }
            )
        except PreferencesUpdateError as exception:
            flash(
                f"Faild to update preferences: {exception}",
                category="error"
            )
        else:
            flash(
                f"Updated preferences",
                category="success"
            )
    return render_template_with_nav_info(
        "main/corpus_preferences.html",
        sep_token=corpus.delimiter_token or "",
        read_only=not is_owner,
        corpus_id=corpus_id,
        context_left=corpus.context_left,
        context_right=corpus.context_right,
        corpus=corpus
    )


@main.route("/corpus/<int:corpus_id>/custom-dict", methods=["GET", "POST", "PATCH"])
@login_required
@requires_corpus_access("corpus_id")
def corpus_custom_dict(corpus_id: int):
    """Show preferences view."""
    corpus = Corpus.query.get_or_404(corpus_id)

    if request.method == "PATCH":
        category = request.form.get("category", None)
        value = request.form.get("value", None)
        try:
            if not category:
                raise PersonalDictionaryError("Category is missing")
            elif not value:
                raise PersonalDictionaryError("Value is missing")
            corpus.insert_custom_dictionary_value(category=category, string=value)
            return jsonify({
                "status": True,
                "message": "New value saved."
            })
        except PersonalDictionaryError:
            resp = jsonify({
                "message": "Unable to add to custom dictionary",
                "status": False
            })
            resp.status_code = 403
            return resp
    elif request.method == "POST":
        pos = request.form.get("POS", "")
        lemma = request.form.get("lemma", "")
        morph = request.form.get("morph", "")
        try:
            corpus.custom_dictionaries_update(
                "POS", pos
            )
            corpus.custom_dictionaries_update(
                "lemma", lemma
            )
            corpus.custom_dictionaries_update(
                "morph", morph
            )
        except PersonalDictionaryError as exception:
            flash(
                f"Faild to update dictionary: {exception}",
                category="error"
            )
        else:
            flash(
                f"Updated custom dictionary",
                category="success"
            )
    return render_template_with_nav_info(
        "main/corpus_custom_dictionary.html",
        POS=corpus.get_custom_dictionary("POS", formatted=True),
        lemma=corpus.get_custom_dictionary("lemma", formatted=True),
        morph=corpus.get_custom_dictionary("morph", formatted=True),
        corpus=corpus
    )
