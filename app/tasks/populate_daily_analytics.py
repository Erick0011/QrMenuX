from app.models import db, Restaurant, PageVisit, ItemView, Reservation, DailyAnalytics
from app.utils.now_angola import now_angola
from datetime import timedelta
from sqlalchemy import func


def populate_daily_analytics():
    yesterday = now_angola().date() - timedelta(days=1)

    restaurants = Restaurant.query.all()
    for restaurant in restaurants:
        total_visits = PageVisit.query.filter(
            PageVisit.restaurant_id == restaurant.id,
            func.date(PageVisit.timestamp) == yesterday,
        ).count()

        total_item_views = ItemView.query.filter(
            ItemView.restaurant_id == restaurant.id,
            func.date(ItemView.timestamp) == yesterday,
        ).count()

        reservations = Reservation.query.filter(
            Reservation.restaurant_id == restaurant.id,
            func.date(Reservation.start_time) == yesterday,
        ).all()

        total_reservations = len(reservations)
        total_people = sum(r.people for r in reservations)

        analytics = DailyAnalytics.query.filter_by(
            restaurant_id=restaurant.id, date=yesterday
        ).first()

        if not analytics:
            analytics = DailyAnalytics(restaurant_id=restaurant.id, date=yesterday)
            db.session.add(analytics)

        analytics.total_visits = total_visits
        analytics.total_item_views = total_item_views
        analytics.total_reservations = total_reservations
        analytics.total_people = total_people

    db.session.commit()
    print("[✓] KPIs diários populados com sucesso.")
