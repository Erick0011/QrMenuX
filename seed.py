from app import create_app, db
from app.models import User, Restaurant, Subscription
from werkzeug.security import generate_password_hash
from slugify import slugify
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from app.utils import now_angola  # ou ajuste conforme o local do now_angola()

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

    # Verifica se já existem restaurantes
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
                },
                "extend": {"months": 1}
            },
            {
                "email": "rest2@example.com",
                "password": "123456",
                "restaurant": {
                    "name": "Sabores da Ilha",
                    "email": "sabores@ilha.co.ao",
                    "phone": "923000222",
                    "description": "Restaurante com pratos típicos e frutos do mar.",
                },
                "extend": {"days": 7}
            },
            {
                "email": "rest3@example.com",
                "password": "123456",
                "restaurant": {
                    "name": "Vegano na Banda",
                    "email": "vegan@banda.ao",
                    "phone": "923000333",
                    "description": "Opções 100% veganas e sustentáveis.",
                },
                "extend": {"months": -1}  # expirado
            },
        ]

        for data in users_data:
            hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
            user = User(email=data['email'], password=hashed_pw)
            db.session.add(user)
            db.session.flush()

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
            db.session.flush()

            # Cria uma assinatura e aplica extensão conforme seed
            now = now_angola()
            start_date = now
            end_date = now + timedelta(days=data['extend'].get('days', 0)) + relativedelta(months=data['extend'].get('months', 0))
            is_active = end_date > now

            subscription = Subscription(
                restaurant_id=restaurant.id,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active
            )
            db.session.add(subscription)

        db.session.commit()
        print("Usuários, restaurantes e assinaturas criados com sucesso!")
    else:
        print("Restaurantes já existem no banco.")
