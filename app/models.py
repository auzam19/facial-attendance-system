from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

# Flask-Login: load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)  # stored lowercase
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' | 'faculty' | 'student'
    face_embedding = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_logs = db.relationship(
        'AttendanceLog',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
        passive_deletes=True  # don't try to NULL the FK
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def _sha256_hex(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        ph = self.password_hash or ""
        try:
            if check_password_hash(ph, password):
                return True
        except Exception:
            pass
        if ph == self._sha256_hex(password):
            self.set_password(password)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            return True
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(10), nullable=False)  # 'TIME_IN' | 'TIME_OUT'
    location = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Log {self.user_id} - {self.status} @ {self.timestamp}>"
