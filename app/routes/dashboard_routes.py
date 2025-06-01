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
    categories = Category.query.filter_by(restaurant_id=current_user.id).all()
    return render_template("dashboard/index.html", categories=categories)

@bp.route("/category/new", methods=["GET", "POST"])
@login_required
def new_category():
    if request.method == "POST":
        name = request.form["name"]
        category = Category(name=name, restaurant_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        flash("Categoria criada com sucesso!", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("dashboard/new_category.html")

@bp.route("/item/new", methods=["GET", "POST"])
@login_required
def new_item():
    categories = Category.query.filter_by(restaurant_id=current_user.id).all()
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        category_id = request.form["category_id"]
        image_filename = request.files["image"]
        filename = None
        if image_filename:
            filename = secure_filename(image_filename.filename)
            image_filename.save(os.path.join(UPLOAD_FOLDER, filename))
        item = MenuItem(name=name, price=price, image_filename=filename, category_id=category_id)
        db.session.add(item)
        db.session.commit()
        flash("Prato adicionado com sucesso!", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("dashboard/new_item.html", categories=categories)
