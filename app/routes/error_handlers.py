import traceback
from flask import render_template, request, current_app
from app import db
from app.errors.exceptions import RestauranteInativoError


def register_error_handlers(app):

    def log_error(code, error):
        current_app.logger.error(f"Erro {code} - {request.path} - {str(error)}")
        current_app.logger.error(traceback.format_exc())

    @app.errorhandler(401)
    def unauthorized_error(error):
        log_error(401, error)
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        log_error(403, error)
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        log_error(404, error)
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        log_error(500, error)
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(RestauranteInativoError)
    def restaurante_inativo_error(e):
        current_app.logger.warning(
            f"Restaurante inativo tentou acessar: {request.path}"
        )
        return render_template("errors/restaurante_inativo.html"), 451
