from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app.models import Restaurant, User
from app import db
from flask import current_app as app

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    return "Entre em contacto para criar a sua conta"

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))  # rota do admin
            else:
                return redirect(url_for('dashboard.index'))  # dashboard do restaurante

        flash("Email ou senha inválidos", 'danger')

    return render_template('auth/login.html')



@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
