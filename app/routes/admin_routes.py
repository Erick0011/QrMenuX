from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import db, User, Restaurant, Subscription
from datetime import datetime
from slugify import slugify

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html", current_user=current_user)

@bp.route("/create_user", methods=['POST'])
@login_required
def create_user():
    try:
        # Coletar dados do formulário
        user_email = request.form['user_email']
        user_password = request.form['user_password']
        restaurant_name = request.form['restaurant_name']
        restaurant_email = request.form['restaurant_email']
        restaurant_phone = request.form.get('restaurant_phone')
        subscription_end_str = request.form['subscription_end_date']

        # Criar usuário
        user = User(
            email=user_email,
            password=generate_password_hash(user_password),
            role='restaurant'
        )
        db.session.add(user)
        db.session.flush()  # pega o ID do usuário antes de commit

        # Criar restaurante
        restaurant = Restaurant(
            owner_id=user.id,
            name=restaurant_name,
            slug=slugify(restaurant_name),
            email=restaurant_email,
            phone=restaurant_phone,
            is_active=True
        )
        db.session.add(restaurant)
        db.session.flush()

        # Criar assinatura
        subscription_end = datetime.strptime(subscription_end_str, "%Y-%m-%d")
        subscription = Subscription(
            restaurant_id=restaurant.id,
            end_date=subscription_end,
            is_active=True
        )
        db.session.add(subscription)

        db.session.commit()
        flash('Usuário, restaurante e assinatura criados com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar usuário: {e}', 'danger')

    return redirect(url_for('admin.users'))

@bp.route('/admin/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        # Atualizar e-mail
        user.email = request.form['user_email']

        # Atualizar senha se fornecida
        password = request.form.get('user_password')
        if password:
            user.password = generate_password_hash(password)

        # Atualizar dados do restaurante
        restaurant = user.restaurant
        restaurant.name = request.form['restaurant_name']
        restaurant.slug = slugify(restaurant.name)
        restaurant.email = request.form['restaurant_email']
        restaurant.phone = request.form['restaurant_phone']

        db.session.commit()
        flash('Dados do usuário atualizados com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar dados do usuário: {e}', 'danger')

    return redirect(url_for('admin.users'))


@bp.route('/admin/toggle_user_status/<int:user_id>')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)

    # Verifica se o usuário tem restaurante
    if user.restaurant:
        user.restaurant.is_active = not user.restaurant.is_active
        db.session.commit()

    return redirect(url_for('admin.users'))


@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    try:
        # Buscar usuário
        user = User.query.get_or_404(user_id)

        # Buscar restaurante associado
        restaurant = user.restaurant
        if restaurant:
            # Excluir assinatura se houver
            if restaurant.subscription:
                db.session.delete(restaurant.subscription)

            # Excluir itens de menu ligados às categorias
            for category in restaurant.categories:
                for item in category.items:
                    db.session.delete(item)
                db.session.delete(category)

            # Excluir restaurante
            db.session.delete(restaurant)

        # Excluir usuário
        db.session.delete(user)

        db.session.commit()
        flash("Usuário e dados relacionados foram excluídos com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir usuário: {e}", "danger")

    return redirect(url_for('admin.users'))


@bp.route("/users")
@login_required
def users():
    # filtro de busca
    search = request.args.get('search', '')

    # query base com join do restaurante
    query = User.query.join(Restaurant).filter(User.role == 'restaurant')

    if search:
        like_search = f"%{search}%"
        query = query.filter(
            db.or_(
                User.email.ilike(like_search),
                Restaurant.name.ilike(like_search),
            )
        )

    users = query.all()

    return render_template('admin/users.html', users=users, search=search)

@bp.route('/subscriptions')
@login_required
def subscriptions():
    restaurants = Restaurant.query.join(Subscription).order_by(Subscription.end_date.asc()).all()
    return render_template('admin/subscriptions.html', restaurants=restaurants)


@bp.route('/subscription/extend/<int:restaurant_id>')
@login_required
def extend_subscription(restaurant_id):
    days = int(request.args.get('days', 0))
    months = int(request.args.get('months', 0))

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if restaurant.subscription:
        restaurant.subscription.extend(days=days, months=months)
    return redirect(url_for('admin.subscriptions'))


@bp.route('/subscription/reminder/<int:restaurant_id>')
@login_required
def send_reminder(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    sub = restaurant.subscription
    if sub:
        dias = sub.days_remaining()
        print(f"[MOCK EMAIL] Restaurante {restaurant.name} - {dias} dias restantes.")
        print(f"[MOCK WHATSAPP] Número {restaurant.phone} - expira em {dias} dias.")
    return redirect(url_for('admin.subscriptions'))
