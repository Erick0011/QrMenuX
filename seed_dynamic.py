from app import create_app, db
from app.models import User, Restaurant, Subscription
from werkzeug.security import generate_password_hash
from slugify import slugify
from faker import Faker
from random import randint, choice
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from app.utils import now_angola  # ou substitua por datetime.utcnow se preferir

fake = Faker('pt_PT')  # Gera dados mais adaptados a Angola/Portugal
app = create_app()


def create_restaurant_with_subscription(index: int):
    now = now_angola()

    # Usuário
    email = f"{fake.user_name()}{index}@example.com"
    password = generate_password_hash("123456", method='pbkdf2:sha256')
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.flush()

    # Restaurante
    rest_name = fake.company()
    restaurant = Restaurant(
        name=rest_name,
        slug=slugify(rest_name),
        email=f"{slugify(rest_name)}@restaurant.com",
        phone=fake.phone_number(),
        description=fake.catch_phrase(),
        is_active=True,
        owner_id=user.id
    )
    db.session.add(restaurant)
    db.session.flush()

    # Assinatura (válida ou expirada)
    option = choice(['7_days', '1_month', '3_months', 'expired'])
    start_date = now
    if option == '7_days':
        end_date = now + timedelta(days=7)
    elif option == '1_month':
        end_date = now + relativedelta(months=1)
    elif option == '3_months':
        end_date = now + relativedelta(months=3)
    elif option == 'expired':
        end_date = now - timedelta(days=randint(1, 30))  # entre 1 e 30 dias atrás

    is_active = end_date > now

    subscription = Subscription(
        restaurant_id=restaurant.id,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active
    )
    db.session.add(subscription)


def seed(n=10):
    with app.app_context():
        print(f"🔁 Inserindo {n} restaurantes...")
        for i in range(n):
            create_restaurant_with_subscription(i)
        db.session.commit()
        print(f"✅ {n} usuários/restaurantes criados com sucesso!")


if __name__ == "__main__":
    seed(10)  # Altere aqui
