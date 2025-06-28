from app.models import db, Restaurant, PageVisit, ItemView, Reservation, DailyAnalytics
from app.utils.now_angola import now_angola
from datetime import timedelta, datetime


def populate_daily_analytics():
    yesterday = now_angola().date() - timedelta(days=1)
    print(f"[DEBUG] Data de referência: {yesterday}")

    start_of_day = datetime.combine(yesterday, datetime.min.time())
    end_of_day = datetime.combine(yesterday, datetime.max.time())

    restaurants = Restaurant.query.all()
    print(f"[DEBUG] Restaurantes encontrados: {len(restaurants)}")

    for restaurant in restaurants:
        print(f"[DEBUG] Processando restaurante ID {restaurant.id}")

        total_visits = PageVisit.query.filter(
            PageVisit.restaurant_id == restaurant.id,
            PageVisit.timestamp >= start_of_day,
            PageVisit.timestamp <= end_of_day,
        ).count()
        print(f"[DEBUG] Total de visitas: {total_visits}")

        total_item_views = ItemView.query.filter(
            ItemView.restaurant_id == restaurant.id,
            ItemView.timestamp >= start_of_day,
            ItemView.timestamp <= end_of_day,
        ).count()
        print(f"[DEBUG] Total de visualizações de itens: {total_item_views}")

        reservations = Reservation.query.filter(
            Reservation.restaurant_id == restaurant.id,
            Reservation.start_time >= start_of_day,
            Reservation.start_time <= end_of_day,
        ).all()
        print(f"[DEBUG] Total de reservas encontradas: {len(reservations)}")

        total_reservations = len(reservations)
        total_people = sum(r.people for r in reservations)
        print(f"[DEBUG] Total de pessoas em reservas: {total_people}")

        analytics = DailyAnalytics.query.filter_by(
            restaurant_id=restaurant.id, date=yesterday
        ).first()

        if not analytics:
            analytics = DailyAnalytics(restaurant_id=restaurant.id, date=yesterday)
            db.session.add(analytics)
            print("[DEBUG] Criado novo registro de analytics.")

        analytics.total_visits = total_visits
        analytics.total_item_views = total_item_views
        analytics.total_reservations = total_reservations
        analytics.total_people = total_people

    db.session.commit()
    print("[✓] KPIs diários populados com sucesso.")
