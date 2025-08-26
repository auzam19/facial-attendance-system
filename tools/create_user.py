# tools/create_user.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import User

USAGE = "Usage: python tools/create_user.py <role: admin|faculty|student> <username> <password>"

def main():
    if len(sys.argv) != 4:
        print(USAGE)
        raise SystemExit(1)

    role, username, password = sys.argv[1:4]
    role = role.strip().lower()
    username = username.strip().lower()

    if role not in {"admin", "faculty", "student"}:
        print("Role must be one of: admin, faculty, student")
        raise SystemExit(1)

    app = create_app()
    with app.app_context():
        print("DB:", app.config['SQLALCHEMY_DATABASE_URI'])
        u = User.query.filter_by(username=username).first()
        if u:
            print(f"User '{username}' already exists (role={u.role}).")
            return
        u = User(username=username, full_name=username, role=role)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print(f"Created {role} '{username}'")

if __name__ == "__main__":
    main()
