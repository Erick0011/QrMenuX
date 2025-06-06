from flask_login import UserMixin
from . import db, login_manager
from app.utils.now_angola import now_angola
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pytz

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default='restaurant')  # 'admin' ou 'restaurant'
    restaurant = db.relationship('Restaurant', backref='owner', lazy=True, uselist=False)


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
    start_date = db.Column(db.DateTime, default=lambda: now_angola())
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def extend(self, days=0, months=0):
        now = now_angola()

        # Converter end_date para timezone-aware se necessário
        if self.end_date and self.end_date.tzinfo is None:
            self.end_date = pytz.timezone("Africa/Luanda").localize(self.end_date)

        base_date = self.end_date if self.end_date and self.end_date > now else now

        new_end_date = base_date + timedelta(days=days) + relativedelta(months=months)

        self.start_date = self.start_date or now
        self.end_date = new_end_date
        self.is_active = True
        db.session.commit()

    def has_expired(self):
        if self.end_date is None:
            return True

        return self._end_date_with_tz() < now_angola()

    def days_remaining(self):
        if self.end_date is None:
            return 0

        return (self._end_date_with_tz() - now_angola()).days

    def _end_date_with_tz(self):
        """Converte end_date para timezone de Angola, se necessário"""
        if self.end_date.tzinfo is None or self.end_date.tzinfo.utcoffset(self.end_date) is None:
            return self.end_date.replace(tzinfo=pytz.timezone("Africa/Luanda"))
        return self.end_date



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


