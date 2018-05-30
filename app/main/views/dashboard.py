from flask import request, url_for, redirect, abort, flash
from flask_login import login_required, current_user

from app import db
from app.main.views.utils import render_template_with_nav_info
from app.models import Corpus, User, Role
from app.models.linguistic import CorpusUser
from .. import main


@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """admin dashboard page."""
    return render_template_with_nav_info('main/dashboard.html', current_user=current_user)


@main.route('/dashboard/manage-corpus-users/<int:corpus_id>', methods=['GET', 'POST'])
@login_required
def manage_corpus_users(corpus_id):
    """
         Save or display corpus accesses
     """
    corpus = Corpus.query.filter(Corpus.id == corpus_id).first()
    if corpus.has_access(current_user) or current_user.is_admin():
        # only owners can give/remove access & promote a user to owner
        if request.method == "POST" and (corpus.is_owned_by(current_user) or current_user.is_admin()):
            users = [
                User.query.filter(User.id == user_id).first()
                for user_id in [int(u) for u in request.form.getlist("user_id")]
            ]
            ownerships = [int(u) for u in request.form.getlist("ownership")]

            # previous rights
            prev_cu = CorpusUser.query.filter(CorpusUser.corpus_id == corpus_id).all()

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
                corpus=corpus, current_user=current_user, users=users, roles=roles
            )
    else:
        return abort(403)
