import hmac
import os
from functools import wraps
from flask import jsonify, request

API_KEY = os.environ.get("SERVICEBOARD_API_KEY")

if not API_KEY:
    raise RuntimeError("SERVICEBOARD_API_KEY is not configured")

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        provided = request.headers.get("Authorization", "")
        expected = f"Bearer {API_KEY}"

        if not hmac.compare_digest(provided.encode(), expected.encode()):
            return jsonify({"error": "Unauthorized"}), 401, {
                "WWW-Authenticate": "Bearer"
            }

        return func(*args, **kwargs)

    return wrapper