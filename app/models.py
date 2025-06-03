from flask_login import UserMixin
from . import db
from . import login_manager
from app.utils import now_angola

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='restaurant')  # 'admin' ou 'restaurant'
    restaurant = db.relationship('Restaurant', backref='owner', lazy=True, uselest=False)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    subscription = db.relationship('Subscription', uselist=False, backref='restaurant', lazy=True)
    categories = db.relationship('Category', backref='restaurant', lazy=True)


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), unique=True)
    start_date = db.Column(db.DateTime, default=now_angola())
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    items = db.relationship('MenuItem', backref='category', lazy=True)


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(100))
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


