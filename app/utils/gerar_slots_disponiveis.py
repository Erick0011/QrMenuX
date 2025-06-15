from datetime import datetime, timedelta
from app.models import Restaurant, OperatingHour, Reservation


def gerar_slots_disponiveis(restaurant_id, mesa_id, data):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return []

    duracao = timedelta(minutes=restaurant.slot_duration_minutes or 90)
    buffer = timedelta(minutes=restaurant.slot_buffer_minutes or 5)

    dia_semana = data.strftime("%A")
    oh = OperatingHour.query.filter_by(
        restaurant_id=restaurant_id, day_of_week=dia_semana
    ).first()
    if not oh or oh.open_time == oh.close_time:
        return []

    abertura = datetime.combine(data, oh.open_time)
    fechamento = datetime.combine(data, oh.close_time)

    # Se o restaurante permite ultrapassar o horário de fechamento
    if restaurant.allow_pass_closing_time:
        fechamento += duracao

    # Pegando reservas da mesa naquele dia
    reservas = Reservation.query.filter(
        Reservation.table_id == mesa_id,
        Reservation.start_time >= abertura - buffer,
        Reservation.end_time <= fechamento + buffer,
    ).all()

    slots = []
    hora = abertura

    while hora + duracao <= fechamento:
        slot_inicio = hora
        slot_fim = hora + duracao

        conflito = False
        for r in reservas:
            if not (
                slot_fim <= r.start_time - buffer or slot_inicio >= r.end_time + buffer
            ):
                conflito = True
                break

        if not conflito:
            slots.append(
                (
                    slot_inicio.time().strftime("%H:%M"),
                    slot_fim.time().strftime("%H:%M"),
                )
            )

        # Avança o relógio para o próximo slot fixo
        hora += duracao + buffer

    return slots
