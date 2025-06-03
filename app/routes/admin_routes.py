from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import db, Category, MenuItem

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html", current_user=current_user)

@bp.route("/create_restaurant")
@login_required
def create_restaurant():
    return render_template("admin/create_restaurant.html", current_user=current_user)
