import hmac
import os
from functools import wraps
from flask import jsonify, request, session, redirect, url_for

API_KEY = os.environ.get("SERVICEBOARD_API_KEY")

if not API_KEY:
    raise RuntimeError("SERVICEBOARD_API_KEY is not configured")

def is_valid_api_key():
    provided = request.headers.get("Authorization", "")
    expected = f"Bearer {API_KEY}"

    return hmac.compare_digest(provided.encode(), expected.encode())

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_valid_api_key():
            return jsonify({"error": "Invalid API Key"}), 401, {
                "WWW-Authenticate": "Bearer"
            }

        return func(*args, **kwargs)

    return wrapper

def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper