from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Decorator para restringir acesso a usuários com um dos papéis especificados."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized
            if current_user.role not in roles:
                abort(403)  # Forbidden
            return f(*args, **kwargs)

        return decorated_function

    return decorator
