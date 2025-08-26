# tools/reset_password.py
import sys
from pathlib import Path

# --- make sibling 'app/' importable even when running from tools/ ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import func
from app import create_app, db
from app.models import User

def main():
    if len(sys.argv) != 3:
        print("Usage: python tools/reset_password.py <username> <new_password>")
        raise SystemExit(1)

    uname, new_pwd = sys.argv[1], sys.argv[2]

    app = create_app()
    with app.app_context():
        u = User.query.filter(func.lower(User.username) == uname.lower()).first()
        if not u:
            print("User not found:", uname)
            raise SystemExit(1)
        u.set_password(new_pwd)
        db.session.commit()
        print("Password reset OK for:", u.username)
        print("DB:", app.config['SQLALCHEMY_DATABASE_URI'])

if __name__ == "__main__":
    main()
