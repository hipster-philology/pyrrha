from flask import request, url_for, redirect, abort, flash
from flask_login import login_required, current_user
from typing import List

from app import db
from app.main.views.utils import render_template_with_nav_info
from app.models import Corpus, User, Role, ControlLists, CorpusUser, ControlListsUser, WordToken
from .. import main


@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """admin dashboard page."""
    corpora = Corpus.for_user(current_user)
    if current_user.is_admin():
        control_lists = db.session.query(ControlLists).all()
    else:
        control_lists = ControlLists.for_user(current_user)
    return render_template_with_nav_info(
        'main/dashboard.html',
        current_user=current_user,
        dashboard_corpora=corpora,
        dashboard_control_lists=control_lists
    )


@main.route('/dashboard/manage-control-lists-users/<cl_id>', methods=['GET', 'POST'])
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
def list_corpora():

    if current_user.is_admin():
        corpora = Corpus.query.all()
    else:
        corpora = Corpus.for_user(current_user)
    # ToDo: To Slow
    # amounts = {
    #     wt.corpus: wt.order_id
    #     for wt in WordToken.query.filter(
    #             db.and_(
    #                 Corpus.id.in_([corpus.id for corpus in corpora]),
    #                 WordToken.corpus == Corpus.id
    #             )
    #         ).order_by(WordToken.order_id.desc()).distinct(WordToken.corpus).all()
    # }
    return render_template_with_nav_info("main/dashboard_corpus_table.html", corpora=corpora)


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
            return redirect(url_for('main.dashboard'))

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
