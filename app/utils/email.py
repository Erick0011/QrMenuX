from flask_mail import Message
from app import mail
from flask import current_app


def enviar_email(destinatario, assunto, corpo):
    try:
        msg = Message(assunto, recipients=[destinatario], body=corpo)
        mail.send(msg)
        current_app.logger.info(
            f"E-mail enviado para {destinatario} | Assunto: {assunto} | Corpo: {corpo}"
        )
    except Exception as e:
        current_app.logger.error(
            f"Erro ao enviar e-mail: {e} | Assunto: {assunto} | Corpo: {corpo}"
        )
