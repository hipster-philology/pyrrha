from flask import request, flash, redirect, url_for, abort, current_app, jsonify
from flask_login import current_user, login_required
import sqlalchemy.exc


from app import db
from app.models import CorpusUser, ControlLists, WordToken
from .utils import render_template_with_nav_info
from app.utils.forms import create_input_format_convertion, read_input_tokens
from .. import main
from ...utils.forms import strip_or_none
from ...models import Corpus
from ...utils.response import format_api_like_reply
from ...errors import MissingTokenColumnValue, NoTokensInput

AUTOCOMPLETE_LIMIT = 20


@main.route('/corpus/new', methods=["POST", "GET"])
@login_required
def corpus_new():
    """ Register a new corpus
    """
    lemmatizers = current_app.config.get("LEMMATIZERS", [])

    def normal_view():
        lists = {"public": [], "submitted": [], "private": []}
        for cl in ControlLists.get_available(current_user):
            lists[cl.str_public].append(cl)

        return render_template_with_nav_info(
            'main/corpus_new.html',
            lemmatizers=lemmatizers,
            public_control_lists=lists,
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
                "delimiter_token": strip_or_none(request.form.get("sep_token", "")) or None
            }

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
                corpus = Corpus.create(**form_kwargs)
                db.session.add(CorpusUser(corpus=corpus, user=current_user, is_owner=True))
                # Add a link to the control list
                ControlLists.link(corpus=corpus, user=current_user, is_owner=cl_owner)
                db.session.commit()
                flash("New corpus registered", category="success")
                return redirect(url_for(".corpus_get", corpus_id=corpus.id))
            except (sqlalchemy.exc.StatementError, sqlalchemy.exc.IntegrityError) as e:
                db.session.rollback()
                flash("The corpus cannot be registered. Check your data", category="error")
                if str(e.orig) == "UNIQUE constraint failed: corpus.name":
                    flash("You have already a corpus going by the name {}".format(request.form.get("name")),
                          category="error")
                return error()
            except MissingTokenColumnValue as exc:
                db.session.rollback()
                flash("At least one line of your corpus is missing a token/form. Check line %s " % exc.line, category="error")
                return error()
            except NoTokensInput:
                db.session.rollback()
                flash("You did not input any text.", category="error")
                return error()
            except Exception as e:
                db.session.rollback()
                flash("The corpus cannot be registered. Check your data", category="error")
                return error()

    return normal_view()


@main.route('/corpus/get/<int:corpus_id>')
@login_required
def corpus_get(corpus_id):
    """ Main page about the corpus

    :param corpus_id: ID of the corpus
    """
    corpus = Corpus.query.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)
    return render_template_with_nav_info('main/corpus_info.html', corpus=corpus)


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
    corpus = Corpus.query.get_or_404(corpus_id)
    if not corpus.has_access(current_user):
        abort(403)
    return jsonify(
        [
            format_api_like_reply(result, allowed_type)
            for result in WordToken.get_like(
                filter_id=corpus_id,
                form=request.args.get("form"),
                group_by=True,
                type_like=allowed_type,
                allowed_list=False
            ).limit(AUTOCOMPLETE_LIMIT)
            if result is not None
        ]
    )
