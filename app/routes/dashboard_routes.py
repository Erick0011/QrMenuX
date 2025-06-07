from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app.models import db, Category, MenuItem
from flask import current_app



bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


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

@bp.route("/categories", methods=["GET", "POST"])
@login_required
def list_categories():
    restaurant = current_user.restaurant
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            new_category = Category(name=name.strip(), restaurant=restaurant)
            db.session.add(new_category)
            db.session.commit()
            flash("Categoria criada com sucesso!", "success")
    categories = Category.query.filter_by(restaurant=restaurant).all()
    return render_template("dashboard/categories.html", categories=categories)

@bp.route("/categories/<int:category_id>/toggle")
@login_required
def toggle_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_categories'))

    category.is_active = not category.is_active

    for item in category.items:
        item.is_active = category.is_active

    db.session.commit()
    flash("Estado da categoria e dos itens alterado.", "info")
    return redirect(url_for('dashboard.list_categories'))

@bp.route("/categories/<int:category_id>/delete")
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_categories'))

    for item in category.items:
        db.session.delete(item)

    db.session.delete(category)
    db.session.commit()

    flash("Categoria e seus itens foram removidos com sucesso!", "warning")
    return redirect(url_for('dashboard.list_categories'))


@bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_categories'))

    name = request.form.get("name")
    if name:
        category.name = name.strip()
        db.session.commit()
        flash("Categoria atualizada!", "success")
    return redirect(url_for('dashboard.list_categories'))

@bp.route("/items", methods=["GET"])
@login_required
def list_items():
    restaurant = current_user.restaurant
    categories = Category.query.filter_by(restaurant=restaurant).all()
    category_id = request.args.get("category_id", type=int)
    selected_category = Category.query.get(category_id) if category_id else categories[0] if categories else None
    items = MenuItem.query.filter_by(category=selected_category).all() if selected_category else []
    return render_template("dashboard/items.html", categories=categories, selected_category=selected_category, items=items)

@bp.route("/items/create", methods=["POST"])
@login_required
def create_item():
    name = request.form.get("name")
    description = request.form.get("description")
    price = request.form.get("price", type=float)
    category_id = request.form.get("category_id", type=int)
    image = request.files.get("image")

    category = Category.query.get_or_404(category_id)
    if category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_items'))

    filename = None
    if image and name:
        # Criar nome seguro para a imagem
        ext = os.path.splitext(image.filename)[1]
        safe_image_name = secure_filename(name.lower().replace(" ", "_")) + ext

        # Pasta do restaurante dentro de /static/uploads/
        restaurant_slug = current_user.restaurant.slug
        relative_folder = os.path.join("uploads", restaurant_slug)
        absolute_folder = os.path.join(current_app.root_path, "static", relative_folder)
        os.makedirs(absolute_folder, exist_ok=True)

        # Caminho final absoluto + salvar
        image_path = os.path.join(absolute_folder, safe_image_name)
        image.save(image_path)

        # Caminho relativo para salvar no banco
        filename = os.path.join(relative_folder, safe_image_name).replace("\\", "/")

    new_item = MenuItem(
        name=name,
        description=description,
        price=price,
        image_filename=filename,
        category=category
    )
    db.session.add(new_item)
    db.session.commit()

    flash("Prato criado com sucesso!", "success")
    return redirect(url_for('dashboard.list_items', category_id=category_id))

@bp.route("/items/edit/<int:item_id>", methods=["POST", "GET"])
@login_required
def edit_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    restaurant = current_user.restaurant

    if item.category.restaurant != restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_items'))

    name = request.form.get("name").strip()
    description = request.form.get("description")
    price = request.form.get("price", type=float)
    category_id = request.form.get("category_id", type=int)
    image = request.files.get("image")

    new_category = Category.query.get_or_404(category_id)
    if new_category.restaurant != restaurant:
        flash("Categoria inválida.", "danger")
        return redirect(url_for('dashboard.list_items'))

    item.name = name
    item.description = description
    item.price = price
    item.category = new_category

    if image and name:
        ext = os.path.splitext(image.filename)[1]  # ex: .jpg, .png
        safe_name = secure_filename(name.lower().replace(" ", "_")) + ext

        folder = os.path.join("static", "uploads", restaurant.slug)
        os.makedirs(folder, exist_ok=True)

        filepath = os.path.join(folder, safe_name)
        image.save(filepath)

        item.image_filename = f"{restaurant.slug}/{safe_name}"

    db.session.commit()
    flash("Prato atualizado com sucesso!", "success")
    return redirect(url_for('dashboard.list_items', category_id=category_id))
 

@bp.route("/items/<int:item_id>/toggle")
@login_required
def toggle_item(item_id):
    item = MenuItem.query.get_or_404(item_id)

    if item.category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_items'))

    if not item.is_active and not item.category.is_active:
        flash("Não é possível ativar este prato porque a categoria está desativada.", "warning")
        return redirect(url_for('dashboard.list_items', category_id=item.category.id))

    item.is_active = not item.is_active
    db.session.commit()
    flash("Estado do prato alterado.", "info")
    return redirect(url_for('dashboard.list_items', category_id=item.category.id))


@bp.route("/items/<int:item_id>/delete")
@login_required
def delete_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for('dashboard.list_items'))

    db.session.delete(item)
    db.session.commit()
    flash("Prato excluído com sucesso!", "warning")
    return redirect(url_for('dashboard.list_items', category_id=item.category.id))


@bp.route("/perfil")
@login_required
def profile():
    restaurant = current_user.restaurant
    return render_template("dashboard/profile.html", restaurant=restaurant)