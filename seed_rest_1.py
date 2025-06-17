from app import create_app, db
from app.models import (
    Restaurant,
    Category,
    MenuItem,
    Table,
    OperatingHour,
    PageVisit,
    ItemView,
    Reservation,
    DailyAnalytics,
)
from app.utils.now_angola import now_angola
from datetime import datetime, timedelta, time, date
import random

app = create_app()
app.app_context().push()

restaurant_id = 1

# Limpar dados existentes (opcional)
models = [
    Category,
    Table,
    OperatingHour,
    PageVisit,
    ItemView,
    Reservation,
    DailyAnalytics,
]
for model in models:
    db.session.query(model).filter_by(restaurant_id=restaurant_id).delete()

MenuItem.query.filter(
    MenuItem.category_id.in_(
        db.session.query(Category.id).filter_by(restaurant_id=restaurant_id)
    )
).delete(synchronize_session=False)


# Categorias e Itens
categories = [
    Category(name="Entradas", restaurant_id=restaurant_id),
    Category(name="Pratos Principais", restaurant_id=restaurant_id),
    Category(name="Sobremesas", restaurant_id=restaurant_id),
]
db.session.add_all(categories)
db.session.flush()

items = [
    MenuItem(name="Sopa de legumes", price=1500, category_id=categories[0].id),
    MenuItem(name="Bruschetta", price=2000, category_id=categories[0].id),
    MenuItem(name="Frango grelhado", price=5500, category_id=categories[1].id),
    MenuItem(name="Bife de vaca", price=6500, category_id=categories[1].id),
    MenuItem(name="Lasanha", price=6000, category_id=categories[1].id),
    MenuItem(name="Mousse de chocolate", price=1800, category_id=categories[2].id),
    MenuItem(name="Pudim de leite", price=1600, category_id=categories[2].id),
]
db.session.add_all(items)
db.session.flush()

# Mesas
tables = [
    Table(
        name=f"Mesa {i}", capacity=random.choice([2, 4, 6]), restaurant_id=restaurant_id
    )
    for i in range(1, 6)
]
db.session.add_all(tables)
db.session.flush()

# Horário de funcionamento
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
for day in days:
    db.session.add(
        OperatingHour(
            restaurant_id=restaurant_id,
            day_of_week=day,
            open_time=time(10, 0),
            close_time=time(22, 0),
        )
    )

# Visitas à página e visualizações de item (últimos 7 dias)
today = now_angola().date()
for i in range(7):
    visit_date = today - timedelta(days=i)
    for _ in range(random.randint(5, 15)):
        db.session.add(
            PageVisit(
                slug="cardapio",
                ip_address=f"192.168.1.{random.randint(1, 100)}",
                user_agent="Mozilla/5.0",
                timestamp=datetime.combine(
                    visit_date, time(hour=random.randint(10, 21))
                ),
                restaurant_id=restaurant_id,
            )
        )
    for item in items:
        for _ in range(random.randint(0, 5)):
            db.session.add(
                ItemView(
                    slug=item.name.lower().replace(" ", "-"),
                    item_id=item.id,
                    ip_address=f"192.168.1.{random.randint(1, 100)}",
                    user_agent="Mozilla/5.0",
                    timestamp=datetime.combine(
                        visit_date, time(hour=random.randint(10, 21))
                    ),
                    restaurant_id=restaurant_id,
                )
            )

# Reservas
statuses = ["pendente", "aprovado", "cancelado"]
for i in range(20):
    start_dt = now_angola() - timedelta(
        days=random.randint(0, 6), hours=random.randint(0, 12)
    )
    end_dt = start_dt + timedelta(minutes=90)
    db.session.add(
        Reservation(
            unique_code=f"RSV{i:04}",
            customer_name=f"Cliente {i+1}",
            customer_phone=f"923{random.randint(100000, 999999)}",
            start_time=start_dt,
            end_time=end_dt,
            people=random.choice([2, 4, 6]),
            observations="",
            table_id=random.choice(tables).id,
            status=random.choice(statuses),
            created_at=start_dt - timedelta(hours=2),
            restaurant_id=restaurant_id,
        )
    )

# Analytics por dia
for i in range(7):
    d = today - timedelta(days=i)
    db.session.add(
        DailyAnalytics(
            restaurant_id=restaurant_id,
            date=d,
            total_visits=random.randint(20, 50),
            total_item_views=random.randint(10, 30),
            total_reservations=random.randint(1, 5),
            total_people=random.randint(5, 25),
        )
    )

db.session.commit()
print("Seed finalizado com sucesso.")
