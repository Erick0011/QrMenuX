from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import db, Category, MenuItem
import os
from werkzeug.utils import secure_filename

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


UPLOAD_FOLDER = "app/static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bp.route("/")
@login_required
def index():
    # Página inicial do painel
    return render_template("dashboard/index.html")

@bp.route("/assinatura")
@login_required
def subscription():
    restaurant = current_user.restaurant
    subscription = restaurant.subscription if restaurant else None
    return render_template("dashboard/subscription.html", subscription=subscription)

@bp.route("/categorias")
@login_required
def categories():
    restaurant = current_user.restaurant
    categories = Category.query.filter_by(restaurant_id=restaurant.id).all() if restaurant else []
    return render_template("dashboard/categories.html", categories=categories)

@bp.route("/cardapio")
@login_required
def menu():
    # Exibir itens agrupados por categoria
    restaurant = current_user.restaurant
    categories = Category.query.filter_by(restaurant_id=restaurant.id).all() if restaurant else []
    return render_template("dashboard/menu.html", categories=categories)

@bp.route("/perfil")
@login_required
def profile():
    restaurant = current_user.restaurant
    return render_template("dashboard/profile.html", restaurant=restaurant)