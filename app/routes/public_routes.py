from flask import Blueprint, render_template
from app.models import Restaurant, Category
from flask import abort

bp = Blueprint('public', __name__, url_prefix='/menu')

@bp.route('/<int:restaurant_id>')
def view_menu(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    categories = Category.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('public/menu.html', restaurant=restaurant, categories=categories)
