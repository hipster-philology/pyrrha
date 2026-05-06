from flask import request, jsonify, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Corpus, CorpusUser, ControlLists, ControlListsUser, Favorite
from app.models.corpus import WordToken, ChangeRecord
from app.models.user import User
from app.utils.pagination import int_or
from .. import main


def _paginate_query(query, page, per_page):
    per_page = min(int_or(per_page, 20), 100)
    page = int_or(page, 1)
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _corpus_subqueries():
    user_count = (
        db.session.query(func.count(CorpusUser.user_id))
        .filter(CorpusUser.corpus_id == Corpus.id)
        .correlate(Corpus)
        .scalar_subquery()
    )
    token_count = (
        db.session.query(func.count(WordToken.id))
        .filter(WordToken.corpus == Corpus.id)
        .correlate(Corpus)
        .scalar_subquery()
    )
    last_change = (
        db.session.query(func.max(ChangeRecord.created_on))
        .filter(ChangeRecord.corpus == Corpus.id)
        .correlate(Corpus)
        .scalar_subquery()
    )
    is_fav = (
        db.session.query(func.count(Favorite.corpus_id))
        .filter(
            Favorite.corpus_id == Corpus.id,
            Favorite.user_id == current_user.id,
        )
        .correlate(Corpus)
        .scalar_subquery()
    )
    owner_sort = (
        db.session.query(func.min(User.last_name))
        .join(CorpusUser, CorpusUser.user_id == User.id)
        .filter(CorpusUser.corpus_id == Corpus.id, CorpusUser.is_owner == True)
        .correlate(Corpus)
        .scalar_subquery()
    )
    needs_review_count = (
        db.session.query(func.count(WordToken.id))
        .filter(WordToken.corpus == Corpus.id, WordToken.needs_review == True)
        .correlate(Corpus)
        .scalar_subquery()
    )
    return user_count, token_count, last_change, is_fav, owner_sort, needs_review_count


@main.route('/api/browse/corpora')
@login_required
def browse_corpora_api():
    search = request.args.get('search', '').strip()
    wants_admin = request.args.get('admin', '') == '1'
    if wants_admin and not current_user.is_admin():
        abort(403)
    admin_view = wants_admin

    user_count_sq, token_count_sq, last_change_sq, is_fav_sq, owner_sort_sq, needs_review_count_sq = _corpus_subqueries()

    base = db.session.query(
        Corpus,
        user_count_sq.label('user_count'),
        token_count_sq.label('token_count'),
        last_change_sq.label('last_change'),
        is_fav_sq.label('is_fav'),
        needs_review_count_sq.label('needs_review_count'),
    )

    if not admin_view:
        base = base.filter(
            CorpusUser.corpus_id == Corpus.id,
            CorpusUser.user_id == current_user.id,
            Corpus.status == 'active',
        )

    if search:
        pattern = f'%{search}%'
        owner_match = (
            db.session.query(CorpusUser)
            .join(User, User.id == CorpusUser.user_id)
            .filter(
                CorpusUser.corpus_id == Corpus.id,
                CorpusUser.is_owner == True,
                db.or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    (User.first_name + ' ' + User.last_name).ilike(pattern),
                )
            )
            .correlate(Corpus)
            .exists()
        )
        base = base.filter(db.or_(Corpus.name.ilike(pattern), owner_match))

    sort_cols = {
        'name':        Corpus.name,
        'token_count': token_count_sq,
        'user_count':  user_count_sq,
        'last_change': last_change_sq,
        'owners':      owner_sort_sq,
    }
    sort_key = request.args.get('sort', 'name')
    sort_col = sort_cols.get(sort_key, Corpus.name)
    if request.args.get('order', 'asc') == 'desc':
        sort_col = sort_col.desc()
    base = base.order_by(sort_col)

    pagination = _paginate_query(base, request.args.get('page'), request.args.get('per_page'))

    # Single extra query for owners of all corpora on this page
    corpus_ids = [row[0].id for row in pagination.items]
    owners_rows = (
        db.session.query(CorpusUser.corpus_id, User.first_name, User.last_name)
        .join(User, User.id == CorpusUser.user_id)
        .filter(CorpusUser.corpus_id.in_(corpus_ids), CorpusUser.is_owner == True)
        .all()
    )
    owners_by_corpus = {}
    for corpus_id, first, last in owners_rows:
        owners_by_corpus.setdefault(corpus_id, []).append(f'{first} {last}')

    items = []
    for corpus, user_count, token_count, last_change, is_fav, needs_review_count in pagination.items:
        items.append({
            'id': corpus.id,
            'name': corpus.name,
            'owners': ', '.join(owners_by_corpus.get(corpus.id, [])),
            'last_change': last_change.strftime('%Y-%m-%d') if last_change else None,
            'user_count': user_count,
            'token_count': token_count,
            'is_fav': bool(is_fav),
            'fav_icon': 'fa-star' if is_fav else 'fa-star-o',
            'needs_review_count': needs_review_count or 0,
            'url_correct': url_for('main.tokens_correct', corpus_id=corpus.id),
            'url_export': url_for('main.tokens_export', corpus_id=corpus.id),
            'url_manage': url_for('main.manage_corpus_users', corpus_id=corpus.id),
            'url_fav': url_for('main.corpus_fav', corpus_id=corpus.id),
            'url_get': url_for('main.corpus_info', corpus_id=corpus.id),
            'url_needs_review': url_for('main.tokens_needs_review', corpus_id=corpus.id) if needs_review_count else None,
        })

    return jsonify({
        'items': items,
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'per_page': pagination.per_page,
    })


@main.route('/api/browse/control-lists')
@login_required
def browse_control_lists_api():
    search = request.args.get('search', '').strip()

    if current_user.is_admin():
        query = db.session.query(ControlLists)
    else:
        query = db.session.query(ControlLists).filter(
            ControlListsUser.user_id == current_user.id,
            ControlListsUser.control_lists_id == ControlLists.id,
        )

    if search:
        query = query.filter(ControlLists.name.ilike(f'%{search}%'))

    query = query.order_by(ControlLists.name)
    pagination = _paginate_query(query, request.args.get('page'), request.args.get('per_page'))

    items = []
    for cl in pagination.items:
        items.append({
            'id': cl.id,
            'name': cl.name,
            'str_public': cl.str_public,
            'url_manage': url_for('main.manage_control_lists_user', cl_id=cl.id),
            'url_get': url_for('control_lists_bp.get', control_list_id=cl.id),
        })

    return jsonify({
        'items': items,
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'per_page': pagination.per_page,
    })
