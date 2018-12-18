from flask import request, flash, redirect, url_for, Blueprint, abort, jsonify, make_response
from flask_login import current_user, login_required
import sqlalchemy.exc
from werkzeug.exceptions import BadRequest


from app.main.views.utils import render_template_with_nav_info
from app.models import ControlLists, AllowedLemma
from app import db
from ..utils.forms import strip_or_none
from ..utils.tsv import StringDictReader

AUTOCOMPLETE_LIMIT = 20


# Create the current blueprint
control_lists_bp = Blueprint('control_lists_bp', __name__)


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


@control_lists_bp.route('/controls/<int:control_list_id>/read/lemma', methods=["GET", "UPDATE"])
@login_required
def lemma_list(control_list_id):
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=control_list_id, user=current_user)
    can_edit = is_owner or current_user.is_admin()
    if request.method == "UPDATE" and request.mimetype == "application/json" and can_edit:
        form = request.get_json().get("lemmas", None)
        if not form:
            abort(400, jsonify({"message": "No lemma were passed."}))
        lemmas = list(set(form.split()))
        try:
            AllowedLemma.add_batch(lemmas, control_list.id, _commit=True)
            return jsonify({"message": "Data saved"})
        except ValueError as E:
            db.session.rollback()
            print(jsonify({"message": str(E)}))
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
    abort(405)


@control_lists_bp.route('/controls/<int:control_list_id>/read/<allowed_type>', methods=["GET"])
@login_required
def read_allowed_values(control_list_id, allowed_type):
    if allowed_type not in ["POS", "morph"]:
        flash("The category you selected is wrong petit coquin !", category="error")
        redirect(url_for(".get", control_list_id=control_list_id))

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
def edit(cl_id, allowed_type):
    """ Find allowed values and allow their edition

    :param cl_id: Id of the corpus
    :param allowed_type: Type of allowed value (lemma, morph, POS)
    """
    if allowed_type not in ["lemma", "POS", "morph"]:
        raise BadRequest("Unknown type of resource.")
    control_list, is_owner = ControlLists.get_linked_or_404(control_list_id=cl_id, user=current_user)

    can_edit = is_owner or current_user.is_admin()

    if not can_edit:
        abort(403)

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
        success = control_list.update_allowed_values(allowed_type, allowed_values)
        if success:
            flash("Control List Updated", category="success")
        else:
            flash("An error occured", category="errors")

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
