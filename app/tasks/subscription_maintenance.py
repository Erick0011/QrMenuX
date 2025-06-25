from app.models import Subscription
from app.utils.now_angola import now_angola
from app.utils.email import enviar_email
from app import db


def desativar_ou_notificar_subscricoes():
    hoje = now_angola()
    subs_ativas = Subscription.query.filter(Subscription.is_active == True).all()

    desativados = 0
    notificados = 0

    for sub in subs_ativas:
        restaurante = sub.restaurant

        if not restaurante:
            continue  # Segurança

        # Caso esteja expirada
        if sub.has_expired():
            sub.is_active = False
            restaurante.is_active = False
            desativados += 1

            enviar_email(
                destinatario=restaurante.email,
                assunto="Sua assinatura expirou",
                corpo=f"""Olá {restaurante.name},

Sua assinatura foi desativada automaticamente por expiração no dia {sub._end_date_with_tz().strftime('%d/%m/%Y')}.

Para reativar seus serviços, acesse o painel e renove sua assinatura.

Equipe QrMenuX @ NextKode.""",
            )

        # Caso esteja perto de expirar (≤ 3 dias)
        elif sub.days_remaining() <= 3:
            notificados += 1
            enviar_email(
                destinatario=restaurante.email,
                assunto="Sua assinatura está prestes a expirar",
                corpo=f"""Olá {restaurante.name},

Sua assinatura irá expirar em {sub.days_remaining()} dia(s), no dia {sub._end_date_with_tz().strftime('%d/%m/%Y')}.

Evite interrupções renovando agora mesmo pelo painel de administração.

Equipe QrMenuX @ NextKode.""",
            )

    db.session.commit()

    print(f"{desativados} restaurantes desativados.")
    print(f"{notificados} lembretes enviados.")
