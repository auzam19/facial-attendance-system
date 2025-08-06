from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, AttendanceLog

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin():
    return current_user.is_authenticated and current_user.role == 'admin'

@admin_bp.route('/users', methods=['GET'])
@login_required
def view_users():
    if not is_admin():
        return "Unauthorized", 403
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if not is_admin():
        return "Unauthorized", 403

    username = request.form.get('username')
    full_name = request.form.get('full_name')
    password = request.form.get('password')
    role = request.form.get('role')

    existing = User.query.filter_by(username=username).first()
    if existing:
        flash('Username already exists.', 'warning')
        return redirect(url_for('admin.view_users'))

    new_user = User(username=username, full_name=full_name, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash(f'{role.title()} user "{full_name}" added successfully.', 'success')
    return redirect(url_for('admin.view_users'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not is_admin():
        return "Unauthorized", 403

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.full_name} deleted.', 'info')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin.view_users'))

@admin_bp.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if not is_admin():
        return "Unauthorized", 403

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin.view_users'))

    new_role = request.form.get('role')
    new_password = request.form.get('password')

    if new_role:
        user.role = new_role
    if new_password:
        user.set_password(new_password)

    db.session.commit()
    flash(f"User {user.full_name} updated.", "success")
    return redirect(url_for('admin.view_users'))

@admin_bp.route('/logs/<int:user_id>', methods=['GET'])
@login_required
def view_user_logs(user_id):
    if not is_admin():
        return "Unauthorized", 403

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    logs = AttendanceLog.query.filter_by(user_id=user_id).order_by(AttendanceLog.timestamp.desc()).all()
    return render_template('admin/user_logs.html', user=user, logs=logs)
