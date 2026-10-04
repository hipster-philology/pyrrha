from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    url_for,
    current_app)
from flask_babel import gettext as _, lazy_gettext as _l
from flask_login import current_user, login_required

from app import db
from app.admin.forms import (
    ChangeAccountTypeForm,
    ChangeUserEmailForm,
    InviteUserForm,
    NewUserForm,
    ChangeAccountStatusForm)
from app.decorators import admin_required
from app.email import send_email_async
from app.main.views.utils import render_template_with_nav_info
from app.models import Role, User

admin = Blueprint('admin', __name__)


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('User %(name)s successfully created', name=user.full_name()),
              'form-success')
    return render_template_with_nav_info('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        send_email_async(
            app=current_app._get_current_object(),
            recipient=user.email,
            subject=_l('You Are Invited To Join'),
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash(_('User %(name)s successfully invited', name=user.full_name()),
              'form-success')
    return render_template_with_nav_info('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template_with_nav_info(
        'admin/registered_users.html', current_user=current_user, users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template_with_nav_info('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash(_('Email for user %(name)s successfully changed to %(email)s.',
            name=user.full_name(), email=user.email), 'form-success')
    return render_template_with_nav_info('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<int:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash(_('You cannot change the type of your own account. Please ask '
              'another administrator to do this.'), 'danger')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash(_('Role for user %(name)s successfully changed to %(role)s.',
            name=user.full_name(), role=user.role.name), 'form-success')
    return render_template_with_nav_info('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<int:user_id>/change-account-status', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_status(user_id):
    """Change a user's account status (active/inactive)."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    form = ChangeAccountStatusForm()

    if form.validate_on_submit():
        user.confirmed = not user.confirmed
        db.session.add(user)
        db.session.commit()
        flash(_('Status for user %(name)s successfully changed to %(status)s.',
            name=user.full_name(), status=_('Confirmed') if user.confirmed else _('Unconfirmed')), 'form-success')
    else:
        form = ChangeAccountStatusForm(status=user.confirmed)

    return render_template_with_nav_info('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template_with_nav_info('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash(_('You cannot delete your own account. Please ask another '
              'administrator to do this.'), 'danger')
    else:
        user = db.session.get(User, user_id)
        if user is None:
            abort(404)
        db.session.delete(user)
        db.session.commit()
        flash(_('Successfully deleted user %(name)s.', name=user.full_name()), 'success')
    return redirect(url_for('admin.registered_users'))


