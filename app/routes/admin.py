from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app import db
from app.models import User, AttendanceLog
from datetime import datetime
import csv
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin():
    return current_user.is_authenticated and current_user.role == 'admin'

def _parse_date(s: str | None):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None

@admin_bp.route('/users', methods=['GET'])
@login_required
def view_users():
    if not is_admin():
        return "Unauthorized", 403
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if not is_admin():
        return "Unauthorized", 403

    username = (request.form.get('username') or '').strip().lower()
    full_name = (request.form.get('full_name') or '').strip()
    password = request.form.get('password') or ''
    role = (request.form.get('role') or '').strip() or 'student'

    if not username or not full_name or not password:
        flash('All fields are required.', 'warning')
        return redirect(url_for('admin.view_users'))

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
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.view_users'))

    try:
        db.session.delete(user)  # cascades to attendance_logs via model relationship
        db.session.commit()
        flash(f'User {user.full_name} deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete user: {e}', 'danger')

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

    new_role = (request.form.get('role') or '').strip()
    new_password = request.form.get('password') or ''

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

    logs = (AttendanceLog.query
            .filter_by(user_id=user_id)
            .order_by(AttendanceLog.timestamp.desc())
            .all())
    return render_template('admin/user_logs.html', user=user, logs=logs)

# ---------- NEW: All logs (admin-wide) + CSV export ----------
@admin_bp.route('/all_logs', methods=['GET'])
@login_required
def view_all_logs():
    if not is_admin():
        return "Unauthorized", 403

    start = _parse_date(request.args.get("from"))
    end = _parse_date(request.args.get("to"))

    q = AttendanceLog.query
    if start:
        q = q.filter(AttendanceLog.timestamp >= start)
    if end:
        q = q.filter(AttendanceLog.timestamp < end.replace(hour=23, minute=59, second=59, microsecond=999999))

    logs = q.order_by(AttendanceLog.timestamp.desc()).all()
    return render_template('admin/all_logs.html', logs=logs, start=start, end=end)

@admin_bp.route('/all_logs/export', methods=['GET'])
@login_required
def export_all_logs():
    if not is_admin():
        return "Unauthorized", 403

    start = _parse_date(request.args.get("from"))
    end = _parse_date(request.args.get("to"))

    q = AttendanceLog.query
    if start:
        q = q.filter(AttendanceLog.timestamp >= start)
    if end:
        q = q.filter(AttendanceLog.timestamp < end.replace(hour=23, minute=59, second=59, microsecond=999999))

    logs = q.order_by(AttendanceLog.timestamp.desc()).all()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["user_id", "full_name", "username", "role", "status", "timestamp"])
    for l in logs:
        w.writerow([l.user_id, l.user.full_name, l.user.username, l.user.role,
                    l.status, l.timestamp.isoformat(sep=' ', timespec='seconds')])

    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="attendance_all.csv"'})

# ---------- NEW: System Settings (Coming Soon placeholder) ----------
@admin_bp.route('/settings', methods=['GET'])
@login_required
def system_settings():
    if not is_admin():
        return "Unauthorized", 403
    return render_template('admin/settings.html')
