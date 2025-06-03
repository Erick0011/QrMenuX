from app import create_app, db
from app.models import User, Restaurant
from werkzeug.security import generate_password_hash
from slugify import slugify

app = create_app()

with app.app_context():
    # Cria o usuário admin se não existir
    if not User.query.filter_by(email="admin@qrmenux.com").first():
        admin_user = User(
            email="admin@qrmenux.com",
            password=generate_password_hash("12345", method='pbkdf2:sha256'),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe.")

    # Verifica se já existem restaurantes para não duplicar
    if Restaurant.query.count() == 0:
        users_data = [
            {
                "email": "rest1@example.com",
                "password": "123456",

                "restaurant": {
                    "name": "Comida Rápida Luanda",
                    "email": "contato@comidaluanda.com",
                    "phone": "923000111",
                    "description": "Restaurante especializado em fast-food angolano.",
                }
            },
            {
                "email": "rest2@example.com",
                "password": "123456",

                "restaurant": {
                    "name": "Sabores da Ilha",
                    "email": "sabores@ilha.co.ao",
                    "phone": "923000222",
                    "description": "Restaurante com pratos típicos e frutos do mar.",
                }
            },
            {
                "email": "rest3@example.com",
                "password": "123456",

                "restaurant": {
                    "name": "Vegano na Banda",
                    "email": "vegan@banda.ao",
                    "phone": "923000333",
                    "description": "Opções 100% veganas e sustentáveis.",
                }
            },
        ]

        for data in users_data:
            hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
            user = User(email=data['email'], password=hashed_pw)
            db.session.add(user)
            db.session.flush()  # pega o ID do user antes do commit

            r_data = data['restaurant']
            restaurant = Restaurant(
                name=r_data['name'],
                slug=slugify(r_data['name']),
                email=r_data['email'],
                phone=r_data['phone'],
                description=r_data['description'],
                is_active=True,
                owner_id=user.id
            )
            db.session.add(restaurant)

        db.session.commit()
        print("Usuários e restaurantes criados com sucesso!")
    else:
        print("Restaurantes já existem no banco.")
