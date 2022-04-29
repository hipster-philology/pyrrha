from flask import request, flash, redirect, url_for, Blueprint, abort, jsonify, make_response, current_app
from flask_login import current_user, login_required
from functools import wraps

import sqlalchemy.exc
from werkzeug.exceptions import BadRequest, NotFound, Forbidden


from app.main.views.utils import render_template_with_nav_info
from app.models import ControlLists, AllowedLemma, WordToken, User, PublicationStatus, CorpusCustomDictionary
from app import db, email
from ..utils import PyrrhaError
from ..utils.forms import strip_or_none
from ..utils.tsv import StringDictReader
from ..utils.response import format_api_like_reply
from .forms import SendMailToAdmin, Rename

AUTOCOMPLETE_LIMIT = 20


# Create the current blueprint
control_lists_bp = Blueprint('control_lists_bp', __name__)


def cl_editable(control_list_param: str):
    """ Rewrites a function by checking that the use have the rights to edit the CL. Passes
    the control list as an object in kwargs

    :param control_list_param: Name of the control list param
    :return: Wrapped function
    """

    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            control_list, is_owner = ControlLists.get_linked_or_404(
                control_list_id=kwargs[control_list_param],
                user=current_user
            )
            can_edit = is_owner or current_user.is_admin()
            if not can_edit:
                flash("You are not an owner of the list.", category="error")
                return redirect(url_for(".get", control_list_id=kwargs[control_list_param]))
            return func(*args, control_list=control_list, **kwargs)
        return decorated_view
    return wrapper


@control_lists_bp.route('/controls', methods=["GET"])
@login_required
def home():
    return "Not written", 404


@control_lists_bp.route('/controls/<int:control_list_id>', methods=["GET"])
@login_required
def get(control_list_id):
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)
    return render_template_with_nav_info(
        "control_lists/control_list.html",
        control_list=control_list,
        is_owner=is_owner,
        can_edit=is_owner or current_user.is_admin(),
    )


@control_lists_bp.route('/controls/<int:control_list_id>/read/lemma', methods=["GET", "UPDATE", "DELETE"])
@login_required
def lemma_list(control_list_id):
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)
    can_edit = is_owner or current_user.is_admin()
    if request.method == "DELETE" and can_edit:
        value = request.args.get("id")
        lemma = AllowedLemma.query.get_or_404(value)
        try:
            AllowedLemma.query.filter(
                AllowedLemma.id == lemma.id,
                AllowedLemma.control_list == control_list_id
            ).delete()
            db.session.commit()
            return "", 200
        except Exception as E:
            db.session.rollback()
            return abort(403)
    elif request.method == "UPDATE" and request.mimetype == "application/json" and can_edit:
        form = request.get_json().get("lemmas", None)
        if not form:
            return abort(400, jsonify({"message": "No lemma were passed."}))
        lemmas = list(set(form.split()))
        try:
            AllowedLemma.add_batch(lemmas, control_list.id, _commit=True)
            return jsonify({"message": "Data saved"})
        except ValueError as E:
            db.session.rollback()
            return make_response(jsonify({"message": str(E)}), 400)
        except sqlalchemy.exc.StatementError as E:
            db.session.rollback()
            error = str(E.orig)
            if error.startswith("UNIQUE constraint failed"):
                return make_response(jsonify({"message": "One of the lemma you submitted already exist. "
                                                         "Remove this lemma and resubmit."}), 400)
            return make_response(jsonify({"message": "Database error. Contact the administrator."}), 400)
        except Exception as E:
            db.session.rollback()
            return make_response(jsonify({"message": "Unknown Error"}), 400)
    elif request.method == "GET":
        kwargs = {}
        page = request.args.get("page", "1")
        page = (page.isnumeric()) and int(page) or 1

        limit = request.args.get("limit", "1000")
        limit = (limit.isnumeric()) and int(limit) or 1
        kw = strip_or_none(request.args.get("kw", ""))
        template = "control_lists/read_lemma.html"
        allowed_values = control_list.get_allowed_values(
            allowed_type="lemma",
            kw=kw
        ).paginate(page=page, per_page=limit)
        kwargs["kw"] = kw

        return render_template_with_nav_info(
            template=template,
            control_list=control_list,
            is_owner=is_owner,
            allowed_type="lemma",
            can_edit=is_owner or current_user.is_admin(),
            allowed_values=allowed_values,
            readable=False,
            **kwargs
        )
    return abort(405)


@control_lists_bp.route('/controls/<int:control_list_id>/read/<allowed_type>', methods=["GET"])
@login_required
def read_allowed_values(control_list_id, allowed_type):
    if allowed_type not in ["POS", "morph"]:
        flash("The category you selected is wrong petit coquin !", category="error")
        return redirect(url_for(".get", control_list_id=control_list_id))

    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)
    kwargs = {}

    template = "control_lists/read.html"
    allowed_values = control_list.get_allowed_values(allowed_type=allowed_type).all()

    return render_template_with_nav_info(
        template=template,
        control_list=control_list,
        is_owner=is_owner,
        can_edit=is_owner or current_user.is_admin(),
        allowed_type=allowed_type,
        allowed_values=allowed_values,
        readable=allowed_type == "morph",
        **kwargs
    )


@control_lists_bp.route('/controls/<int:cl_id>/edit/<allowed_type>', methods=["GET", "POST"])
@login_required
@cl_editable("cl_id")
def edit(cl_id, allowed_type, control_list):
    """ Find allowed values and allow their edition

    :param cl_id: Id of the Control List
    :param allowed_type: Type of allowed value (lemma, morph, POS)
    """
    if allowed_type not in ["lemma", "POS", "morph"]:
        raise NotFound("Unknown type of resource.")

    # In case of Post
    if request.method == "POST":
        allowed_values = request.form.get("allowed_values")
        if allowed_type == "lemma":
            allowed_values = [
                x.replace('\r', '')
                for x in allowed_values.split("\n")
                if len(x.replace('\r', '').strip()) > 0
            ]
        elif allowed_type == "POS":
            allowed_values = [
                x.replace('\r', '')
                for x in allowed_values.split(",")
                if len(x.replace('\r', '').strip()) > 0
            ]
        else:
            allowed_values = list(StringDictReader(allowed_values))
        try:
            control_list.update_allowed_values(allowed_type, allowed_values)
            flash("Control List Updated", category="success")
        except PyrrhaError as exception:
            flash("A Pyrrha error occurred: {}".format(exception), category="error")
        except:
            flash("An unknown error occurred", category="error")

    values = control_list.get_allowed_values(allowed_type=allowed_type, order_by="id")
    if allowed_type == "lemma":
        format_message = "This should be formatted as a list of lemma separated by new line"
        values = "\n".join([d.label for d in values])
    elif allowed_type == "POS":
        format_message = "This should be formatted as a list of POS separated by comma and no space"
        values = ",".join([d.label for d in values])
    else:
        format_message = "The TSV should at least have the header : label and could have a readable column for human"
        values = "\n".join(
            ["label\treadable"] + ["{}\t{}".format(d.label, d.readable) for d in values]
        )
    return render_template_with_nav_info(
        "control_lists/edit.html",
        format_message=format_message,
        values=values,
        allowed_type=allowed_type,
        control_list=control_list
    )


@control_lists_bp.route('/controls/<int:control_list_id>/api/<allowed_type>')
@login_required
def search_api(control_list_id, allowed_type):
    """ Find allowed values

    :param control_list_id: Id of the Control List
    :param allowed_type: Type of allowed value (lemma, morph, POS)
    """
    return jsonify(
        [
            format_api_like_reply(result, allowed_type)
            for result in WordToken.get_like(
                filter_id=control_list_id,
                form=request.args.get("form"),
                group_by=True,
                type_like=allowed_type,
                allowed_list=True
            ).limit(AUTOCOMPLETE_LIMIT)
            if result is not None
        ]
    )


@control_lists_bp.route('/controls/<int:control_list_id>/contact', methods=["GET", "POST"])
@login_required
def contact(control_list_id):
    """ This routes allows user to send email to list administrators
    """
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)

    form = SendMailToAdmin(prefix="mail")

    if request.method == "POST" and form.validate_on_submit():
        control_list_link = url_for('control_lists_bp.get', control_list_id=control_list_id, _external=True)
        email.send_email_async(
            app=current_app._get_current_object(),
            bcc=[u[3] for u in control_list.owners] + [current_user.email],
            recipient=[],
            subject='[Pyrrha Control List] ' + form.title.data,
            template='control_lists/email/contact',
            # current_user is a LocalProxy, we want the underlying user
            # object
            user=current_user._get_current_object(),
            message=form.message.data,
            control_list_title=control_list.name,
            url=control_list_link)
        flash('The email has been sent to the control list administrators.', 'success')
        return redirect(url_for('control_lists_bp.contact', control_list_id=control_list_id))
    return render_template_with_nav_info('control_lists/contact.html', form=form, control_list=control_list)


@control_lists_bp.route('/controls/<int:control_list_id>/rename', methods=["GET", "POST"])
@login_required
@cl_editable("control_list_id")
def rename(control_list_id, control_list):
    """ This routes allows user to send email to list administrators
    """
    form = Rename(prefix="rename")
    control_list_link = url_for('control_lists_bp.get', control_list_id=control_list_id, _external=True)


    if request.method == "POST" and form.validate_on_submit():
        control_list.name = form.title.data
        db.session.add(control_list)
        try:
            db.session.commit()
            flash("The name of the list has been updated.", category="success")
        except:
            flash("There was an error when we tried to rename your control list.", category="error")
        return redirect(control_list_link)
    return render_template_with_nav_info('control_lists/rename.html', form=form, control_list=control_list)


@control_lists_bp.route('/controls/<int:control_list_id>/propose_as_public', methods=["GET", "POST"])
@login_required
def propose_as_public(control_list_id):
    """ This routes allows user to send email to application administrators
    to propose a list as public for everyone to use

    """
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)

    if not is_owner:
        flash("You are not an owner of the list.", category="error")
        return redirect(url_for("control_lists_bp.get", control_list_id=control_list_id))
    elif control_list.public != PublicationStatus.private:
        flash("This list is already public or submitted.", category="warning")
        return redirect(url_for("control_lists_bp.get", control_list_id=control_list_id))

    form = SendMailToAdmin(prefix="mail")

    if form.validate_on_submit():
        admins = User.get_admins()
        control_list_link = url_for('control_lists_bp.get', control_list_id=control_list_id, _external=True)
        control_list.public = PublicationStatus.submitted
        db.session.add(control_list)
        try:
            email.send_email_async(
                app=current_app._get_current_object(),
                bcc=[u.email for u in admins] + [current_user.email],
                recipient=[],
                subject='[Pyrrha Control List] ' + form.title.data,
                template='control_lists/email/contact',
                # current_user is a LocalProxy, we want the underlying user
                # object
                user=current_user._get_current_object(),
                message=form.message.data,
                control_list_title=control_list.name,
                url=control_list_link)
            flash('The email has been sent to the administrators.', 'success')
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("There was an error during the messaging step")
    return render_template_with_nav_info('control_lists/propose_as_public.html', form=form, control_list=control_list)


@control_lists_bp.route('/controls/<int:control_list_id>/go_public', methods=["GET"])
@login_required
def go_public(control_list_id):
    """ This routes makes a list public

    """
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)
    if not current_user.is_admin():
        flash("You do not have the rights for this action.", category="error")
    elif control_list.public == PublicationStatus.public:
        flash("This list is already public.", category="warning")
    else:
        control_list.public = PublicationStatus.public
        db.session.add(control_list)
        try:
            db.session.commit()
            flash('This list is now public.', 'success')
        except Exception:
            db.session.rollback()
            flash("There was an error during the update.", category="error")

    return redirect(url_for("control_lists_bp.get", control_list_id=control_list_id))


@control_lists_bp.route("/controls/<int:control_list_id>/informations/edit", methods=["GET", "POST"])
@login_required
@cl_editable("control_list_id")
def information_edit(control_list_id, control_list):
    if request.method == "POST":
        control_list.description = request.form.get("cl_description")
        control_list.language = request.form.get("cl_language")
        control_list.notes = request.form.get("cl_notes")
        control_list.bibliography = request.form.get("cl_bibliography")
        db.session.add(control_list)
        db.session.commit()
    return render_template_with_nav_info('control_lists/information_edit.html', control_list=control_list)


@control_lists_bp.route("/controls/<int:control_list_id>/informations", methods=["GET"])
@login_required
def information_read(control_list_id):
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)
    return render_template_with_nav_info('control_lists/information_read.html', control_list=control_list)
