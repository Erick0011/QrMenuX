from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Category, MenuItem
import os
from werkzeug.utils import secure_filename
from uuid import uuid4
from flask import current_app as app

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def dashboard():
    categories = Category.query.filter_by(restaurant_id=current_user.id).all()
    return render_template('dashboard/index.html', categories=categories)

@bp.route('/add-category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        category = Category(name=name, restaurant_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('dashboard.dashboard'))
    return render_template('dashboard/add_category.html')

@bp.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    categories = Category.query.filter_by(restaurant_id=current_user.id).all()
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        category_id = int(request.form['category_id'])
        image = request.files['image']
        filename = f"{uuid4().hex}_{secure_filename(image.filename)}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        item = MenuItem(name=name, price=price, image_filename=filename, category_id=category_id)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('dashboard.dashboard'))
    return render_template('dashboard/add_item.html', categories=categories)
