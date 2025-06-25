from app import create_app
from app.tasks.subscription_maintenance import desativar_ou_notificar_subscricoes

app = create_app()

with app.app_context():
    desativar_ou_notificar_subscricoes()
