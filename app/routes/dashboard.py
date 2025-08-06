from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import User, AttendanceLog

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard_home():
    if current_user.role == 'admin':
        return render_template('dashboard/admin_dashboard.html', user=current_user)
    elif current_user.role == 'faculty':
        return render_template('dashboard/faculty_dashboard.html', user=current_user)
    elif current_user.role == 'student':
        return render_template('dashboard/student_dashboard.html', user=current_user)
    else:
        return "Unauthorized role", 403

# Faculty-only route: View all attendance logs
@dashboard_bp.route('/faculty/logs')
@login_required
def faculty_logs():
    if current_user.role != 'faculty':
        return "Unauthorized", 403

    logs = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc()).all()
    return render_template('dashboard/faculty_logs.html', logs=logs)
