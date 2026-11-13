from flask import Flask, jsonify, request
from .auth import require_api_key
from . import database
import os
from datetime import timedelta

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SERVICEBOARD_SECRET_KEY"]

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SERVICEBOARD_ALLOW_INSECURE_COOKIES") != "1"

app.config["PERMANET_SESSION_LIFETIME"] = timedelta(hours=8)

database.initialize_database()

@app.route('/')
def index():
    return "ServiceBoard says Hello World"

@app.route('/services')
def get_services():
    return jsonify(database.get_services())

@app.route('/services/<int:service_id>')
def get_service(service_id):
    service = database.get_service(service_id)

    if service is None:
        return { "error": "Service not found" }, 404

    return jsonify(service)

@app.route("/services", methods=["POST"])
@require_api_key
def create_service():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return { "error": "Invalid data format" }, 400

    name = data.get("name")
    if not isinstance(name, str):
        return { "error": "Invalid data format" }, 400

    url = data.get("url")
    if not isinstance(url, str):
        return { "error": "Invalid data format" }, 400

    if not name or not url:
        return { "error": "Service name and url required" }, 400

    name = name.strip()
    url = url.strip()

    service = database.create_service(name, url)
    return jsonify(service), 201

@app.route("/services/<int:service_id>", methods=["DELETE"])
@require_api_key
def delete_service(service_id):
    deleted = database.delete_service(service_id)
    if deleted:
        return "", 204

    return {"error": "Service not found"}, 404