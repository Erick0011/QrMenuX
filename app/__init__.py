from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///QrMenuX.db'
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'

    db.init_app(app)
    login_manager.init_app(app)

    from .routes import auth_routes, dashboard_routes, public_routes, admin_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(dashboard_routes.bp)
    app.register_blueprint(public_routes.bp)
    app.register_blueprint(admin_routes.bp)

    return app

