from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import db, User, Restaurant

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html", current_user=current_user)

@bp.route("/create_user")
@login_required
def create_user():
    return render_template("admin/create_restaurant.html", current_user=current_user)

@bp.route('/admin/user/<int:user_id>/edit')
def edit_user(user_id):
    return f"Edição temporária do usuário {user_id}"

@bp.route('/admin/toggle_user_status/<int:user_id>')
def toggle_user_status(user_id):
    return redirect(url_for('admin.users'))

@bp.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    return redirect(url_for('admin.users'))

@bp.route("/users")
@login_required
def users():
    # filtro de busca
    search = request.args.get('search', '')

    # query base com join do restaurante
    query = User.query.join(Restaurant).filter(User.role == 'restaurant')

    if search:
        like_search = f"%{search}%"
        query = query.filter(
            db.or_(
                User.email.ilike(like_search),
                Restaurant.name.ilike(like_search),
            )
        )

    users = query.all()

    return render_template('admin/users.html', users=users, search=search)