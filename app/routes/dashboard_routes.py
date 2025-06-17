from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    send_file,
)
from flask_login import login_required, current_user
from PIL import Image, ImageDraw, ImageFont
import os
from werkzeug.utils import secure_filename
from app.models import (
    db,
    Category,
    MenuItem,
    OperatingHour,
    Table,
    Reservation,
    PageVisit,
    ItemView,
    DailyAnalytics,
)
from app.utils.gerar_slots_disponiveis import gerar_slots_disponiveis
from flask import current_app
import qrcode
from fpdf import FPDF
import io
from io import BytesIO
import base64
from datetime import time, datetime, timedelta
from sqlalchemy import delete
from sqlalchemy import func, extract
from app.utils.now_angola import now_angola

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/")
@login_required
def index():
    restaurant = current_user.restaurant

    # --- KPIs gerais ---
    total_reservations = Reservation.query.filter_by(
        restaurant_id=restaurant.id
    ).count()
    total_visits = PageVisit.query.filter_by(restaurant_id=restaurant.id).count()
    total_item_views = ItemView.query.filter_by(restaurant_id=restaurant.id).count()
    total_people = (
        db.session.query(func.sum(Reservation.people))
        .filter_by(restaurant_id=restaurant.id)
        .scalar()
        or 0
    )

    # --- Analytics dos últimos 7 dias ---
    last_7_days = now_angola().date() - timedelta(days=6)
    analytics = (
        DailyAnalytics.query.filter(
            DailyAnalytics.restaurant_id == restaurant.id,
            DailyAnalytics.date >= last_7_days,
        )
        .order_by(DailyAnalytics.date)
        .all()
    )

    # Heatmap: hora x dia da semana
    heatmap = {}
    for r in (
        Reservation.query.filter_by(restaurant_id=restaurant.id)
        .filter(Reservation.start_time != None)
        .all()
    ):
        dow = r.start_time.strftime("%A")
        hour = r.start_time.hour
        key = (dow, hour)
        heatmap[key] = heatmap.get(key, 0) + 1

    # Pratos mais visualizados
    top_items = (
        db.session.query(MenuItem.name, db.func.count(ItemView.id).label("views"))
        .join(ItemView, MenuItem.id == ItemView.item_id)
        .filter(ItemView.restaurant_id == restaurant.id)
        .group_by(MenuItem.id)
        .order_by(db.desc("views"))
        .limit(10)
        .all()
    )

    bar_labels = [name for name, _ in top_items]
    bar_values = [views for _, views in top_items]

    labels = [a.date.strftime("%d/%m") for a in analytics]
    visits = [a.total_visits for a in analytics]
    item_views = [a.total_item_views for a in analytics]
    reservations = [a.total_reservations for a in analytics]
    people = [a.total_people for a in analytics]

    return render_template(
        "dashboard/index.html",
        total_reservations=total_reservations,
        total_visits=total_visits,
        total_item_views=total_item_views,
        total_people=total_people,
        labels=labels,
        visits=visits,
        item_views=item_views,
        reservations=reservations,
        people=people,
        heatmap=heatmap,
        bar_labels=bar_labels,
        bar_values=bar_values,
        top_items=top_items,
    )


@bp.route("/")
@login_required
def indexa():
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

    # Gerar QR code básico
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Criar nova imagem com espaço para texto
    width, height = qr_img.size
    new_height = height + 80
    result_img = Image.new("RGB", (width, new_height), "white")
    result_img.paste(qr_img, (0, 0))

    # Escrever textos abaixo
    draw = ImageDraw.Draw(result_img)

    try:
        # Você pode substituir essa fonte por uma que tenha no seu sistema
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
    except IOError:
        font = ImageFont.load_default()

    text1 = f"{restaurant.name}"
    text2 = "Criado com ❤️ pela NextKode"

    # Centralizar textos
    bbox1 = draw.textbbox((0, 0), text1, font=font)
    text1_width = bbox1[2] - bbox1[0]

    bbox2 = draw.textbbox((0, 0), text2, font=font)
    text2_width = bbox2[2] - bbox2[0]

    draw.text(((width - text1_width) / 2, height + 5), text1, fill="black", font=font)
    draw.text(((width - text2_width) / 2, height + 30), text2, fill="gray", font=font)
    # Converter para base64
    buf = io.BytesIO()
    result_img.save(buf, format="PNG")
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


@bp.route("/reservations", methods=["GET", "POST"])
@login_required
def reservations():
    # Ações de POST (mudar status ou deletar)
    if request.method == "POST":
        action = request.form.get("action")
        res_id = request.form.get("reservation_id")
        reservation = Reservation.query.get_or_404(res_id)

        # Confere se pertence ao restaurante do user
        if reservation.restaurant_id != current_user.restaurant.id:
            flash("Ação não permitida", "danger")
            return redirect(url_for("dashboard.reservations"))

        if action == "delete":
            db.session.delete(reservation)
            db.session.commit()
            flash("Reserva removida com sucesso", "success")

        elif action == "set_status":
            new_status = request.form.get("new_status")
            reservation.status = new_status
            db.session.commit()
            flash("Status atualizado!", "success")

        return redirect(url_for("dashboard.reservations"))

    # Filtros GET
    status = request.args.get("status")
    date = request.args.get("date")
    keyword = request.args.get("keyword")

    query = Reservation.query.filter_by(restaurant_id=current_user.restaurant.id)

    if status:
        query = query.filter_by(status=status)

    if date:
        try:
            from datetime import datetime

            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(db.func.date(Reservation.start_time) == parsed_date)
        except ValueError:
            pass

    if keyword:
        termo = f"%{keyword}%"
        query = query.filter(
            db.or_(
                Reservation.customer_name.ilike(termo),
                Reservation.customer_phone.ilike(termo),
                Reservation.unique_code.ilike(termo),
            )
        )

    reservas = query.order_by(Reservation.start_time.desc()).all()
    mesas = Table.query.filter_by(restaurant_id=current_user.restaurant.id).all()

    return render_template(
        "dashboard/reservations.html", reservas=reservas, mesas=mesas
    )


class ReceiptPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, self.restaurant_name, ln=1, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 6, self.restaurant_address, ln=1, align="C")
        self.ln(5)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 148 - 10, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 10)

        self.set_text_color(0, 0, 0)
        footer_text_1 = "QrMenuX · Powered by Next"
        footer_text_2 = "Kode"

        # Calcular largura total do rodapé
        w1 = self.get_string_width(footer_text_1)
        w2 = self.get_string_width(footer_text_2)
        total_width = w1 + w2

        # Posição X para centralizar
        page_width = self.w - 20  # 10 de margem cada lado
        start_x = (page_width - total_width) / 2 + 10

        # Imprimir as duas partes com cores diferentes
        self.set_x(start_x)
        self.set_text_color(0, 0, 0)
        self.cell(w1, 6, footer_text_1, ln=0)

        self.set_text_color(230, 190, 60)  # amarelo
        self.cell(w2, 6, footer_text_2, ln=1)


@bp.route("/reservations/<int:id>/receipt", methods=["GET"])
@login_required
def reservation_receipt(id):
    reserva = Reservation.query.get_or_404(id)

    if reserva.restaurant_id != current_user.restaurant.id:
        flash("Acesso negado", "danger")
        return redirect(url_for("dashboard.reservations_dashboard"))

    restaurant = current_user.restaurant
    pdf = ReceiptPDF(format="A5")
    pdf.restaurant_name = restaurant.name
    pdf.restaurant_address = restaurant.address or "Endereço não cadastrado"
    pdf.add_page()

    # Seção: Detalhes da Reserva
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detalhes da Reserva", ln=1)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 138, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Arial", "", 11)
    pdf.cell(40, 8, "Nome:", 0, 0)
    pdf.cell(0, 8, reserva.customer_name, 0, 1)

    pdf.cell(40, 8, "Telefone:", 0, 0)
    pdf.cell(0, 8, reserva.customer_phone, 0, 1)

    pdf.cell(40, 8, "Data e Hora:", 0, 0)
    pdf.cell(0, 8, reserva.start_time.strftime("%d/%m/%Y %H:%M"), 0, 1)

    pdf.cell(40, 8, "Pessoas:", 0, 0)
    pdf.cell(0, 8, str(reserva.people), 0, 1)

    pdf.cell(40, 8, "Código:", 0, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, reserva.unique_code, 0, 1)

    # Separador
    pdf.ln(5)
    pdf.set_draw_color(160, 160, 160)
    pdf.line(10, pdf.get_y(), 138, pdf.get_y())
    pdf.ln(5)

    # Seção: QR Code
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, "Aponte a câmera para este QR Code:", ln=1)

    # Gerar QR Code da reserva
    qr = qrcode.make(f"{reserva.unique_code}")
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    img_path = "/tmp/temp_qr.png"
    with open(img_path, "wb") as f:
        f.write(qr_buffer.getvalue())

    pdf.image(img_path, x=(148 - 50) / 2, w=50)  # centralizar na A5

    # Gerar PDF em memória
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)

    return send_file(
        pdf_output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"reserva_{reserva.id}.pdf",
    )


@bp.route("/reservations/<int:id>/edit", methods=["POST"])
@login_required
def update_reservation(id):
    r = Reservation.query.get_or_404(id)

    r.customer_name = request.form["customer_name"]
    r.customer_phone = request.form["customer_phone"]
    r.start_time = datetime.strptime(request.form["start_time"], "%Y-%m-%dT%H:%M")
    r.end_time = datetime.strptime(request.form["end_time"], "%Y-%m-%dT%H:%M")
    r.people = int(request.form["people"])
    r.table_id = int(request.form["table_id"])
    r.observations = request.form["observations"]
    r.status = request.form["status"]

    db.session.commit()
    flash("Reserva atualizada com sucesso!", "success")
    return redirect(url_for("dashboard.reservations"))
