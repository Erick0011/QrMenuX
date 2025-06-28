from app.models import db, DailyAnalytics
from app.utils.now_angola import now_angola
from datetime import timedelta
import random


def populate_demo_analytics():
    restaurant_id = 1
    day = now_angola().date() - timedelta(days=1)
    print(
        f"[DEBUG] Populando demo analytics para o dia {day}, restaurante ID {restaurant_id}"
    )

    analytics = DailyAnalytics.query.filter_by(
        restaurant_id=restaurant_id, date=day
    ).first()

    if not analytics:
        analytics = DailyAnalytics(restaurant_id=restaurant_id, date=day)
        db.session.add(analytics)
        print("[DEBUG] Novo registro de analytics criado.")

    analytics.total_visits = random.randint(20, 200)
    analytics.total_item_views = random.randint(10, 100)
    analytics.total_reservations = random.randint(2, 15)
    analytics.total_people = analytics.total_reservations * random.randint(1, 5)

    print(f"[DEBUG] total_visits: {analytics.total_visits}")
    print(f"[DEBUG] total_item_views: {analytics.total_item_views}")
    print(f"[DEBUG] total_reservations: {analytics.total_reservations}")
    print(f"[DEBUG] total_people: {analytics.total_people}")

    db.session.commit()
    print("[✓] Demo analytics populados com sucesso.")
