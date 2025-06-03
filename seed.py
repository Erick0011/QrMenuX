from app import create_app, db
from app.models import User  # ajuste o import do modelo conforme o nome real
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Verifica se o admin já existe
    if not User.query.filter_by(email="admin@meusistema.com").first():
        admin_user = User(
            email="admin@meusistema.com",
            password=generate_password_hash("senha-super-segura", method='pbkdf2:sha256'),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe.")
