from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app.models import db, Category, MenuItem, OperatingHour, Table
from flask import current_app
import qrcode
import io
import base64
from flask import send_file
from datetime import time
from sqlalchemy import delete


bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/")
@login_required
def index():
    # Página inicial do painel
    return render_template("dashboard/index.html")


@bp.route("/subscription", methods=["GET"])
@login_required
def subscription():
    restaurant = current_user.restaurant
    sub = restaurant.subscription

    days_left = sub.days_remaining() if sub and sub.end_date else 0
    expired = not sub or sub.has_expired()

    return render_template(
        "dashboard/subscription.html",
        subscription=sub,
        days_left=days_left,
        expired=expired,
        active_page="subscription",
    )


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
        return redirect(url_for("dashboard.list_categories"))

    category.is_active = not category.is_active

    for item in category.items:
        item.is_active = category.is_active

    db.session.commit()
    flash("Estado da categoria e dos itens alterado.", "info")
    return redirect(url_for("dashboard.list_categories"))


@bp.route("/categories/<int:category_id>/delete")
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for("dashboard.list_categories"))

    for item in category.items:
        if item.image_filename:
            image_path = os.path.join(
                current_app.root_path, "static/uploads", item.image_filename
            )
            if os.path.exists(image_path):
                os.remove(image_path)
        db.session.delete(item)

    db.session.delete(category)
    db.session.commit()

    flash("Categoria e seus itens foram removidos com sucesso!", "warning")
    return redirect(url_for("dashboard.list_categories"))


@bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for("dashboard.list_categories"))

    name = request.form.get("name")
    if name:
        category.name = name.strip()
        db.session.commit()
        flash("Categoria atualizada!", "success")
    return redirect(url_for("dashboard.list_categories"))


@bp.route("/items", methods=["GET"])
@login_required
def list_items():
    restaurant = current_user.restaurant
    categories = Category.query.filter_by(restaurant=restaurant).all()
    category_id = request.args.get("category_id", type=int)
    selected_category = (
        Category.query.get(category_id)
        if category_id
        else categories[0] if categories else None
    )
    items = (
        MenuItem.query.filter_by(category=selected_category).all()
        if selected_category
        else []
    )
    return render_template(
        "dashboard/items.html",
        categories=categories,
        selected_category=selected_category,
        items=items,
    )


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
        return redirect(url_for("dashboard.list_items"))

    filename = None
    if image and name:
        ext = os.path.splitext(image.filename)[1]
        safe_image_name = secure_filename(name.lower().replace(" ", "_")) + ext

        restaurant_slug = current_user.restaurant.slug
        relative_path = os.path.join(restaurant_slug, safe_image_name).replace(
            "\\", "/"
        )
        absolute_folder = os.path.join(
            current_app.root_path, "static", "uploads", restaurant_slug
        )
        os.makedirs(absolute_folder, exist_ok=True)

        image.save(os.path.join(absolute_folder, safe_image_name))
        filename = relative_path

    new_item = MenuItem(
        name=name,
        description=description,
        price=price,
        image_filename=filename,
        category=category,
    )
    db.session.add(new_item)
    db.session.commit()

    flash("Prato criado com sucesso!", "success")
    return redirect(url_for("dashboard.list_items", category_id=category_id))


@bp.route("/items/edit/<int:item_id>", methods=["POST", "GET"])
@login_required
def edit_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    restaurant = current_user.restaurant

    if item.category.restaurant != restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for("dashboard.list_items"))

    name = request.form.get("name").strip()
    description = request.form.get("description")
    price = request.form.get("price", type=float)
    category_id = request.form.get("category_id", type=int)
    image = request.files.get("image")

    new_category = Category.query.get_or_404(category_id)
    if new_category.restaurant != restaurant:
        flash("Categoria inválida.", "danger")
        return redirect(url_for("dashboard.list_items"))

    item.name = name
    item.description = description
    item.price = price
    item.category = new_category

    if image and name:
        ext = os.path.splitext(image.filename)[1]
        safe_name = secure_filename(name.lower().replace(" ", "_")) + ext

        folder = os.path.join(
            current_app.root_path, "static", "uploads", restaurant.slug
        )
        os.makedirs(folder, exist_ok=True)

        filepath = os.path.join(folder, safe_name)
        image.save(filepath)

        item.image_filename = f"{restaurant.slug}/{safe_name}"

    db.session.commit()
    flash("Prato atualizado com sucesso!", "success")
    return redirect(url_for("dashboard.list_items", category_id=category_id))


@bp.route("/items/<int:item_id>/toggle")
@login_required
def toggle_item(item_id):
    item = MenuItem.query.get_or_404(item_id)

    if item.category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for("dashboard.list_items"))

    if not item.is_active and not item.category.is_active:
        flash(
            "Não é possível ativar este prato porque a categoria está desativada.",
            "warning",
        )
        return redirect(url_for("dashboard.list_items", category_id=item.category.id))

    item.is_active = not item.is_active
    db.session.commit()
    flash("Estado do prato alterado.", "info")
    return redirect(url_for("dashboard.list_items", category_id=item.category.id))


@bp.route("/items/<int:item_id>/delete")
@login_required
def delete_item(item_id):
    item = MenuItem.query.get_or_404(item_id)

    if item.category.restaurant != current_user.restaurant:
        flash("Acesso negado.", "danger")
        return redirect(url_for("dashboard.list_items"))

    if item.image_filename:
        image_path = os.path.join(
            current_app.root_path, "static/uploads", item.image_filename
        )
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(item)
    db.session.commit()
    flash("Prato excluído com sucesso!", "warning")
    return redirect(url_for("dashboard.list_items", category_id=item.category.id))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user
    restaurant = user.restaurant

    if request.method == "POST":
        user.email = request.form.get("user_email").strip()
        new_password = request.form.get("user_password").strip()
        if new_password:
            from werkzeug.security import generate_password_hash

            user.password = generate_password_hash(new_password)

        restaurant.email = request.form.get("restaurant_email").strip()
        restaurant.phone = request.form.get("restaurant_phone").strip()
        restaurant.description = request.form.get("restaurant_description").strip()
        restaurant.address = request.form["restaurant_address"].strip()
        restaurant.theme_color = request.form["theme_color"].strip()

        db.session.commit()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("dashboard.profile"))

    return render_template(
        "dashboard/profile.html",
        user=user,
        restaurant=restaurant,
        active_page="profile",
    )


@bp.route("/qrcode")
@login_required
def qrcode_page():
    restaurant = current_user.restaurant
    link = url_for("public.menu", slug=restaurant.slug, _external=True)

    # Gerar QR Code em memória
    qr_img = qrcode.make(link)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render_template(
        "dashboard/qrcode.html", link=link, qr_data=qr_data, active_page="qrcode"
    )


@bp.route("/operating_hours", methods=["GET", "POST"])
@login_required
def operating_hours():
    restaurant = current_user.restaurant

    if request.method == "POST":
        # Remove todos os horários anteriores
        OperatingHour.query.filter_by(restaurant_id=restaurant.id).delete()

        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            open_time_str = request.form.get(f"open_time_{day}")
            close_time_str = request.form.get(f"close_time_{day}")

            if open_time_str and close_time_str:
                open_time = time.fromisoformat(open_time_str)
                close_time = time.fromisoformat(close_time_str)

                new_hour = OperatingHour(
                    restaurant_id=restaurant.id,
                    day_of_week=day,
                    open_time=open_time,
                    close_time=close_time,
                )
                db.session.add(new_hour)
        db.session.commit()
        flash("Horários de funcionamento atualizados com sucesso!", "success")
        return redirect(url_for("dashboard.operating_hours"))

    hours = OperatingHour.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template(
        "dashboard/operating_hours.html", hours=hours, active_page="operating_hours"
    )


@bp.route("/tables", methods=["GET", "POST"])
@login_required
def list_tables():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        capacity = request.form.get("capacity", "").strip()

        if not name or not capacity.isdigit():
            flash("Invalid table name or capacity.", "danger")
            return redirect(url_for("dashboard.list_tables"))

        new_table = Table(
            name=name,
            capacity=int(capacity),
            restaurant_id=current_user.restaurant.id,  # ou outro ID se for estático
        )
        db.session.add(new_table)
        db.session.commit()
        flash("Table created successfully.", "success")
        return redirect(url_for("dashboard.list_tables"))

    tables = Table.query.filter_by(restaurant_id=current_user.restaurant.id).all()
    return render_template("dashboard/tables.html", tables=tables)


@bp.route("/table/<int:table_id>/edit", methods=["POST"])
@login_required
def edit_table(table_id):
    table = Table.query.get_or_404(table_id)

    if table.restaurant_id != current_user.restaurant.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard.list_tables"))

    name = request.form.get("name", "").strip()
    capacity = request.form.get("capacity", "").strip()

    if not name or not capacity.isdigit():
        flash("Invalid data.", "danger")
        return redirect(url_for("dashboard.list_tables"))

    table.name = name
    table.capacity = int(capacity)
    db.session.commit()
    flash("Table updated successfully.", "success")
    return redirect(url_for("dashboard.list_tables"))


@bp.route("/table/<int:table_id>/delete")
@login_required
def delete_table(table_id):
    table = Table.query.get_or_404(table_id)

    if table.restaurant_id != current_user.restaurant.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("dashboard.list_tables"))

    db.session.delete(table)
    db.session.commit()
    flash("Table deleted successfully.", "success")
    return redirect(url_for("dashboard.list_tables"))
