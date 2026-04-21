from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role != required_role:
                return jsonify({"message": "Access forbidden"}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper