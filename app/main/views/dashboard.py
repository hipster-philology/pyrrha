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
        if request.method == "POST":
            users = [
                User.query.filter(User.id == user_id).first()
                for user_id in [int(u) for u in request.form.getlist("user_id")]
            ]
            try:
                for cu in CorpusUser.query.filter(CorpusUser.corpus_id == corpus_id).all():
                    db.session.delete(cu)
                for cu in [CorpusUser(corpus=corpus, user=user) for user in users]:
                    db.session.add(cu)
                db.session.commit()
                flash('Modifications have been saved.', 'success')
            except Exception as e:
                db.session.rollback()
            return redirect(url_for('main.dashboard'))
        else:
            users = User.query.all()
            roles = Role.query.all()
            return render_template_with_nav_info(
                'main/dashboard_manage_corpus_users.html',
                corpus=corpus, current_user=current_user, users=users, roles=roles
            )
    else:
        return abort(403)
