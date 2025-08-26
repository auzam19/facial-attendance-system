import os
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Create database and login manager instances
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirects to login page if not logged in

# Ensure SQLite enforces foreign keys (handy for future DB-level cascades)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
    except Exception:
        # Non-SQLite engines or any errors – ignore silently
        pass

def create_app():
    app = Flask(__name__)

    # Secret key for sessions and encryption
    app.config['SECRET_KEY'] = 'thisshouldbesecretandlong'

    # SQLite database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models so Flask-Migrate or shell can see them
    from app import models  # noqa: F401

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.recognition import recognition_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(recognition_bp)
    app.register_blueprint(admin_bp)

    # Create the database if it doesn't exist
    with app.app_context():
        db.create_all()

    return app
