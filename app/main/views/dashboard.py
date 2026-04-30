from flask import request, url_for, redirect, abort, flash
from flask_login import login_required, current_user
from typing import List

from app import db
from app.decorators import admin_required
from app.main.views.utils import render_template_with_nav_info
from app.models import Corpus, User, Role, ControlLists, CorpusUser, ControlListsUser, WordToken
from .. import main


@main.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    return render_template_with_nav_info('main/dashboard.html')


@main.route('/control-lists', methods=['GET'])
@login_required
def user_control_lists():
    """User's control lists management page."""
    return render_template_with_nav_info('main/user_control_lists.html')


@main.route('/dashboard/manage-control-lists-users/<int:cl_id>', methods=['GET', 'POST'])
@login_required
def manage_control_lists_user(cl_id):
    """ Save or display corpus accesses

    :param cl_id: ID of the control list
     """
    control_list = ControlLists.query.filter(ControlLists.id == cl_id).first()

    can_read = current_user.is_admin() or control_list.has_access(current_user)
    can_edit = current_user.is_admin() or control_list.is_owned_by(current_user)

    if can_read:
        # only owners can give/remove access & promote a user to owner
        if request.method == "POST" and can_edit:
            users = [
                User.query.filter(User.id == user_id).first()
                for user_id in [int(u) for u in request.form.getlist("user_id")]
            ]
            ownerships = [int(u) for u in request.form.getlist("ownership") if u.isdigit()]

            # previous rights
            prev_cu = ControlListsUser.query.filter(ControlListsUser.control_lists_id == cl_id).all()

            # should not be able to delete the last owner
            if len(prev_cu) > 0 and True not in set([user.id in ownerships for user in users]):
                abort(403)

            # update corpus users
            try:
                for cu in prev_cu:
                    db.session.delete(cu)
                for cu in [
                    ControlListsUser(control_lists_id=control_list.id, user_id=user.id, is_owner=user.id in ownerships)
                    for user in users
                ]:
                    db.session.add(cu)
                db.session.commit()
                flash('Modifications have been saved.', 'success')
            except Exception as e:
                db.session.rollback()
                raise e
            return redirect(url_for('main.manage_control_lists_user', cl_id=cl_id))

        else:
            # GET method
            users = User.query.all()
            roles = Role.query.all()
            return render_template_with_nav_info(
                'main/dashboard_manage_control_lists_users.html',
                control_list=control_list, current_user=current_user, users=users, roles=roles,
                can_read=can_read, can_edit=can_edit
            )
    else:
        return abort(403)


def update_control_list_user(
        corpus: Corpus,
        clu_list: List[ControlListsUser],
        users: List[User],
        _commit: bool = True
):
    """ Update control list user list permission for a given corpus. """
    clu_owner_id_list = []
    for clu in clu_list:
        if clu.is_owner:
            clu_owner_id_list.append(clu.user_id)
        db.session.delete(clu)
    for clu in [
        ControlListsUser(
            control_lists_id=corpus.control_lists_id,
            user_id=user.id, is_owner=user.id in clu_owner_id_list) for user in users]:
        db.session.add(clu)
    if _commit:
        db.session.commit()


@main.route('/dashboard/corpora', methods=['GET'])
@login_required
@admin_required
def admin_list_corpora():
    return render_template_with_nav_info("main/dashboard_corpus_table.html")


# Backward-compat endpoint — Playwright tests navigate via url_for('main.list_corpora')
@main.route('/dashboard/corpora/compat', methods=['GET'], endpoint='list_corpora')
@login_required
@admin_required
def _admin_list_corpora_compat():
    return redirect(url_for('main.admin_list_corpora'))


@main.route('/dashboard/control-lists', methods=['GET'])
@login_required
@admin_required
def admin_list_control_lists():
    return render_template_with_nav_info("main/dashboard_control_lists_table.html")


@main.route('/dashboard/manage-corpus-users/<int:corpus_id>', methods=['GET', 'POST'])
@login_required
def manage_corpus_users(corpus_id):
    """
         Save or display corpus accesses
     """
    corpus = Corpus.query.filter(Corpus.id == corpus_id).first()

    can_read = corpus.has_access(current_user)
    can_edit = current_user.is_admin() or corpus.is_owned_by(current_user)

    if can_read is True:
        # only owners can give/remove access & promote a user to owner
        if request.method == "POST" and can_edit:
            users = [
                User.query.filter(User.id == user_id).first()
                for user_id in [int(u) for u in request.form.getlist("user_id")]
            ]
            ownerships = [int(u) for u in request.form.getlist("ownership") if u.isdigit()]

            # previous rights
            prev_cu = CorpusUser.query.filter(CorpusUser.corpus_id == corpus_id).all()
            prev_clu = ControlListsUser.query.filter(
                ControlListsUser.control_lists_id == corpus.control_lists_id).all()

            # should not be able to delete the last owner
            if len(prev_cu) > 0 and True not in set([user.id in ownerships for user in users]):
                abort(403)

            # update corpus users
            try:
                for cu in prev_cu:
                    db.session.delete(cu)
                for cu in [CorpusUser(corpus=corpus, user=user, is_owner=user.id in ownerships)
                           for user in users]:
                    db.session.add(cu)
                update_control_list_user(corpus, prev_clu, users, _commit=False)
                db.session.commit()
                flash('Modifications have been saved.', 'success')
            except Exception as e:
                db.session.rollback()
            return redirect(url_for('main.manage_corpus_users', corpus_id=corpus_id))

        else:
            # GET method
            users = User.query.all()
            roles = Role.query.all()
            return render_template_with_nav_info(
                'main/dashboard_manage_corpus_users.html',
                corpus=corpus, current_user=current_user, users=users, roles=roles,
                can_read=can_read, can_edit=can_edit
            )
    else:
        return abort(403)
