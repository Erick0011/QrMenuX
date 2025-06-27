from app.models import db, DailyAnalytics
from app.utils.now_angola import now_angola
from datetime import timedelta
import random


def populate_demo_analytics():
    restaurant_id = 1
    day = now_angola().date() - timedelta(days=1)

    analytics = DailyAnalytics.query.filter_by(
        restaurant_id=restaurant_id, date=day
    ).first()

    if not analytics:
        analytics = DailyAnalytics(restaurant_id=restaurant_id, date=day)
        db.session.add(analytics)

    analytics.total_visits = random.randint(20, 200)
    analytics.total_item_views = random.randint(10, 100)
    analytics.total_reservations = random.randint(2, 15)
    analytics.total_people = analytics.total_reservations * random.randint(1, 5)

    db.session.commit()
