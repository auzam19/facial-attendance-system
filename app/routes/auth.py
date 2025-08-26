from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from sqlalchemy import func
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        # case-insensitive lookup
        user = User.query.filter(func.lower(User.username) == username.lower()).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard.dashboard_home'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        username  = (request.form.get('username') or '').strip().lower()   # store lowercase
        password  = request.form.get('password') or ''

        if not username or not full_name or not password:
            flash('All fields are required.', 'warning')
            return redirect(url_for('auth.register'))

        # ensure uniqueness in lowercase space
        existing_user = User.query.filter(func.lower(User.username) == username).first()
        if existing_user:
            flash('Username already taken.', 'warning')
            return redirect(url_for('auth.register'))

        user = User(username=username, full_name=full_name, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
