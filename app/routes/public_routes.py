from flask import Blueprint, redirect, render_template, request, jsonify, url_for, flash
from app.models import (
    Restaurant,
    Category,
    OperatingHour,
    Reservation,
    Table,
    ItemView,
    PageVisit,
)
from datetime import datetime, timedelta, date
from app.utils.gerar_slots_disponiveis import gerar_slots_disponiveis
from app.utils.now_angola import now_angola
import phonenumbers
from app import csrf
from app import db


bp = Blueprint("public", __name__, url_prefix="/")


@bp.route("/")
def index():

    return redirect(url_for("auth.login"))


@bp.route("/<slug>")
def menu(slug):
    restaurant = Restaurant.query.filter_by(slug=slug, is_active=True).first_or_404()
    categories = Category.query.filter_by(
        restaurant_id=restaurant.id, is_active=True
    ).all()
    hours = OperatingHour.query.filter_by(restaurant_id=restaurant.id).all()

    return render_template(
        "public/menu.html",
        restaurant=restaurant,
        categories=categories,
        hours=hours,
        theme_color=restaurant.theme_color,
    )


@csrf.exempt
@bp.route("/track-item-view", methods=["POST"])
def track_item_view():
    data = request.get_json()
    item_id = data.get("item_id")
    slug = data.get("slug")
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    restaurant = Restaurant.query.filter_by(slug=slug).first()
    if restaurant:
        view = ItemView(
            item_id=item_id,
            slug=slug,
            ip_address=ip,
            restaurant_id=restaurant.id,
            user_agent=user_agent,
        )
        db.session.add(view)
        db.session.commit()

    return jsonify({"status": "ok"})


@csrf.exempt
@bp.route("/api/visita/<slug>", methods=["POST"])
def registrar_visita(slug):
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    now = now_angola()

    restaurant = Restaurant.query.filter_by(slug=slug).first()
    if not restaurant:
        return jsonify({"status": "not_found"}), 404

    # Verifica a última visita do mesmo IP a esse restaurante
    ultima = (
        PageVisit.query.filter_by(slug=slug, ip_address=ip)
        .order_by(PageVisit.timestamp.desc())
        .first()
    )

    if not ultima or (now - ultima.timestamp > timedelta(minutes=30)):
        visita = PageVisit(
            slug=slug,
            ip_address=ip,
            restaurant_id=restaurant.id,
            timestamp=now,
            user_agent=user_agent,
        )
        db.session.add(visita)
        db.session.commit()
        return jsonify({"status": "registrado"})

    return jsonify({"status": "ignorado"})


@bp.route("/<slug>/reservation", methods=["GET", "POST"])
def reservation(slug):
    restaurant = Restaurant.query.filter_by(slug=slug, is_active=True).first_or_404()
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()
    hours = OperatingHour.query.filter_by(restaurant_id=restaurant.id).all()

    data_str = request.args.get("date")
    mesa_id_str = request.args.get("table_id")
    data_reserva = None
    mesa_escolhida = None
    slots_disponiveis = []

    if data_str and mesa_id_str:
        try:
            data_reserva = datetime.strptime(data_str, "%Y-%m-%d").date()
            mesa_escolhida = Table.query.filter_by(
                id=int(mesa_id_str), restaurant_id=restaurant.id
            ).first()

            if mesa_escolhida:
                # Verifica se o restaurante está aberto nesse dia
                day_name = data_reserva.strftime("%A")
                operating_hour = OperatingHour.query.filter_by(
                    restaurant_id=restaurant.id, day_of_week=day_name
                ).first()

                if data_reserva < date.today():
                    flash(
                        "Não é possível fazer reservas para datas no passado.", "danger"
                    )
                    return redirect(url_for("public.reservation", slug=slug))

                if (
                    not operating_hour
                    or operating_hour.open_time == operating_hour.close_time
                ):
                    flash("O restaurante está fechado nesse dia.", "danger")
                    return redirect(url_for("public.reservation", slug=slug))

                slots_disponiveis = gerar_slots_disponiveis(
                    restaurant_id=restaurant.id,
                    mesa_id=mesa_escolhida.id,
                    data=data_reserva,
                )
        except ValueError:
            flash("Erro ao carregar horários.", "danger")

    if request.method == "POST":
        table_id = int(request.form["table_id"])
        name = request.form["customer_name"].strip()
        raw_phone = request.form["full_phone"]
        start = datetime.fromisoformat(request.form["start_time"])
        end = datetime.fromisoformat(request.form["end_time"])
        people = int(request.form["people"])
        obs = request.form.get("observations") or ""

        table = Table.query.filter_by(id=table_id, restaurant_id=restaurant.id).first()
        if not table:
            flash("Mesa inválida.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        if start.date() < date.today():
            flash("Não é possível fazer reservas para datas no passado.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        if people > table.capacity:
            if people <= table.capacity + 2:
                flash(
                    f"A mesa suporta até {table.capacity} pessoas. "
                    "Cadeiras extras foram solicitadas nas observações!",
                    "warning",
                )
                if "Solicito cadeiras extras" not in obs:
                    obs += (
                        " Solicito cadeiras extras para acomodar todos os convidados."
                    )
            else:
                flash(f"A mesa suporta até {table.capacity} pessoas.", "danger")
                return redirect(url_for("public.reservation", slug=slug))

        day_name = start.strftime("%A")
        operating_hour = OperatingHour.query.filter_by(
            restaurant_id=restaurant.id, day_of_week=day_name
        ).first()

        try:
            phone_obj = phonenumbers.parse(raw_phone, None)

            if not phonenumbers.is_valid_number(phone_obj):
                flash("Número de telefone inválido.", "danger")
                return redirect(url_for("public.reservation", slug=slug))

            phone = phonenumbers.format_number(
                phone_obj, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )

        except phonenumbers.NumberParseException:
            flash("Número de telefone mal formatado.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        if not operating_hour or operating_hour.open_time == operating_hour.close_time:
            flash("Restaurante fechado neste dia.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        if start.date() != end.date():
            flash("A reserva deve começar e terminar no mesmo dia.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        if end - start > timedelta(hours=3):
            flash("A duração máxima da reserva é de 3 horas.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        start_clock = start.time()
        end_clock = end.time()
        if not (
            operating_hour.open_time <= start_clock < operating_hour.close_time
            and operating_hour.open_time < end_clock <= operating_hour.close_time
        ):
            flash("Horário fora do funcionamento do restaurante.", "danger")
            return redirect(url_for("public.reservation", slug=slug))

        conflict = Reservation.query.filter(
            Reservation.table_id == table_id,
            Reservation.start_time < end,
            Reservation.end_time > start,
        ).first()

        if conflict:
            flash("Horário indisponível para essa mesa!", "danger")
            return redirect(url_for("public.reservation", slug=slug))
        else:
            res = Reservation(
                customer_name=name,
                customer_phone=phone,
                start_time=start,
                end_time=end,
                people=people,
                observations=obs,
                table_id=table_id,
                status="pendente",
                restaurant_id=restaurant.id,
            )
            db.session.add(res)
            db.session.commit()
            flash("Reserva criada com sucesso!", "success")

        import urllib.parse

        whatsapp_number = restaurant.phone.replace(" ", "").replace("+", "")
        mensagem = f"Olá, fiz uma reserva no nome de {name} para {people} pessoas no dia {start.strftime('%d/%m/%Y')} às {start.strftime('%H:%M')}."
        mensagem_encoded = urllib.parse.quote(mensagem)
        whatsapp_link = f"https://wa.me/{whatsapp_number}?text={mensagem_encoded}"

        return render_template(
            "public/reservation_redirect.html",
            whatsapp_link=whatsapp_link,
            nome=name,
            data=start.strftime("%d/%m/%Y"),
            hora=start.strftime("%H:%M"),
            restaurant=restaurant,
        )

    reservations = (
        Reservation.query.join(Table)
        .filter(Table.restaurant_id == restaurant.id)
        .order_by(Reservation.start_time)
        .all()
    )

    return render_template(
        "public/reservation.html",
        tables=tables,
        hours=hours,
        slug=slug,
        reservations=reservations,
        data_reserva=data_reserva,
        restaurant=restaurant,
        mesa_escolhida=mesa_escolhida,
        slots_disponiveis=slots_disponiveis,
        theme_color=restaurant.theme_color,
    )
