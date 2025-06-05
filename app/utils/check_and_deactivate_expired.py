from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, db
from app.models import Subscription

app = create_app()

def check_and_deactivate_expired():
    with app.app_context():
        subs = Subscription.query.filter_by(is_active=True).all()
        for s in subs:
            if s.has_expired():
                s.is_active = False
        db.session.commit()
        print("[CRON] Verificação de assinaturas expiradas finalizada.")

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_deactivate_expired, trigger='cron', hour=0, minute=0)
scheduler.start()
