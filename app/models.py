from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import hashlib

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)  # Login ID
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'faculty', 'student'
    face_embedding = db.Column(db.LargeBinary, nullable=True)  # Can be encrypted later
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        # Hash password using SHA256 (for demonstration, use bcrypt in production)
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False)  # 'TIME_IN' or 'TIME_OUT'
    location = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', backref=db.backref('attendance_logs', lazy=True))

    def __repr__(self):
        return f"<Log {self.user_id} - {self.status} @ {self.timestamp}>"
