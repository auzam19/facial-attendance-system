from flask import Blueprint, render_template, request, Response
from flask_login import login_required, current_user
from app.models import AttendanceLog
from datetime import datetime
import csv
import io

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

def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None

# Faculty-only: view all logs
@dashboard_bp.route('/faculty/logs')
@login_required
def faculty_logs():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    start = _parse_date(request.args.get("from"))
    end = _parse_date(request.args.get("to"))
    q = AttendanceLog.query
    if start:
        q = q.filter(AttendanceLog.timestamp >= start)
    if end:
        q = q.filter(AttendanceLog.timestamp < (end.replace(hour=23, minute=59, second=59, microsecond=999999)))
    logs = q.order_by(AttendanceLog.timestamp.desc()).all()
    return render_template('dashboard/faculty_logs.html', logs=logs, start=start, end=end)

@dashboard_bp.route('/faculty/logs/export')
@login_required
def faculty_logs_export():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    start = _parse_date(request.args.get("from"))
    end = _parse_date(request.args.get("to"))
    q = AttendanceLog.query
    if start:
        q = q.filter(AttendanceLog.timestamp >= start)
    if end:
        q = q.filter(AttendanceLog.timestamp < (end.replace(hour=23, minute=59, second=59, microsecond=999999)))
    logs = q.order_by(AttendanceLog.timestamp.desc()).all()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["user_id", "full_name", "username", "status", "timestamp"])
    for l in logs:
        w.writerow([l.user_id, l.user.full_name, l.user.username, l.status,
                    l.timestamp.isoformat(sep=' ', timespec='seconds')])

    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="attendance_faculty_view.csv"'})

# ---------- NEW: Faculty reports (Coming Soon placeholder) ----------
@dashboard_bp.route('/faculty/reports')
@login_required
def faculty_reports():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    # Simple placeholder page; keeps a link to existing CSV export as an interim.
    return render_template('dashboard/faculty_reports.html')
    
# Student-only: my logs
@dashboard_bp.route('/student/logs')
@login_required
def student_logs():
    if current_user.role != 'student':
        return "Unauthorized", 403
    logs = (AttendanceLog.query
            .filter_by(user_id=current_user.id)
            .order_by(AttendanceLog.timestamp.desc())
            .all())
    return render_template('dashboard/student_logs.html', logs=logs)

@dashboard_bp.route('/student/logs/export')
@login_required
def student_logs_export():
    if current_user.role != 'student':
        return "Unauthorized", 403
    logs = (AttendanceLog.query
            .filter_by(user_id=current_user.id)
            .order_by(AttendanceLog.timestamp.desc())
            .all())
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["status", "timestamp"])
    for l in logs:
        w.writerow([l.status, l.timestamp.isoformat(sep=' ', timespec='seconds')])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="my_attendance.csv"'})
