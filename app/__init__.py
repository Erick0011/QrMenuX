from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from app.security import CSP_POLICY
from dotenv import load_dotenv

import logging
from logging.handlers import RotatingFileHandler
import os

# Carrega variáveis do .env
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # Carrega config do .env
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")

    # Extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    Talisman(app, content_security_policy=CSP_POLICY)

    # Blueprints
    from .routes import auth_routes, dashboard_routes, public_routes, admin_routes

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(dashboard_routes.bp)
    app.register_blueprint(public_routes.bp)
    app.register_blueprint(admin_routes.bp)

    # Logging
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=3)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Aplicação iniciada!")

    return app
