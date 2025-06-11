from flask import Blueprint, render_template
from app.models import Restaurant, Category
from flask import abort
import datetime

bp = Blueprint('public', __name__, url_prefix='/')

@bp.route('/<slug>')
def menu(slug):
    restaurant = Restaurant.query.filter_by(slug=slug, is_active=True).first_or_404()
    categories = Category.query.filter_by(restaurant_id=restaurant.id, is_active=True).all()
    theme = "#e67e22"  # suposição de novo campo no model
    return render_template('public/menu.html',
                           restaurant=restaurant,
                           categories=categories,
                           theme_color=theme,
                           now=datetime.utcnow())