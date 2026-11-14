from flask import Flask, jsonify, request, redirect, render_template, session, url_for
from .auth import require_api_key, require_login, is_valid_api_key
from . import database
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from collections.abc import Mapping

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SERVICEBOARD_SECRET_KEY"]

app.config["ADMIN_PASSWORD_HASH"] = os.environ["SERVICEBOARD_ADMIN_PASSWORD_HASH"]

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SERVICEBOARD_ALLOW_INSECURE_COOKIES") != "1"

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

csrf = CSRFProtect(app)

database.initialize_database()

def public_service(service):
    return {
        "id": service["id"],
        "name": service["name"],
        "url": service["url"]
    }

def service_read_response(data):
    authorization = request.headers.get("Authorization")

    if authorization is None:
        if isinstance(data, list):
            data = [public_service(service) for service in data]
        else:
            data = public_service(data)
    elif not is_valid_api_key():
        return jsonify({"error": "Invalid API key"}), 401, {
            "WWW-Authenticate": "Bearer"
        }

    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"

    return response

def validate_service_fields(data):
    if not isinstance(data, Mapping):
        return None, "Invalid data format"

    name = data.get("name")
    url = data.get("url")

    if not isinstance(name, str) or not isinstance(url, str):
        return None, "Invalid data format"

    name = name.strip()
    url = url.strip()

    if not name or not url:
        return None, "Service name and url required"

    fields = {
        "name": name,
        "url": url
    }

    for field in ("host", "deployment_type", "runtime_name", "runtime_version"):
        value = data.get(field)

        if value is not None and not isinstance(value, str):
            return None, f"{field} must be a string or null"

        if isinstance(value, str):
            value = value.strip() or None

        fields[field] = value

    if fields["runtime_version"] and not fields["runtime_name"]:
        return None, "Runtime name required when runtime version is provided"

    return fields, None

@app.route('/')
def index():
    services = [
        {
            "name": service["name"],
            "url": service["url"]
        }
        for service in database.get_services()
    ]

    return render_template("index.html", services=services)

@app.route('/services')
def get_services():
    services = database.get_services()

    return service_read_response(services)

@app.route('/services/<int:service_id>')
def get_service(service_id):
    service = database.get_service(service_id)

    if service is None:
        return { "error": "Service not found" }, 404

    return service_read_response(service)

@app.route("/services", methods=["POST"])
@require_api_key
@csrf.exempt
def create_service():
    fields, error = validate_service_fields(request.get_json(silent=True))

    if error is not None:
        return {"error": error}, 400

    service = database.create_service(**fields)

    return jsonify(service), 201

@app.route("/services/<int:service_id>", methods=["PUT"])
@require_api_key
@csrf.exempt
def update_service(service_id):
    fields,error = validate_service_fields(request.get_json(silent=True))

    if error is not None:
        return { "error": error}, 400

    service = database.update_service(service_id, **fields)
    if service is None:
        return { "error": "Service not found"}

    return jsonify(service)


@app.route("/services/<int:service_id>", methods=["DELETE"])
@require_api_key
@csrf.exempt
def delete_service(service_id):
    deleted = database.delete_service(service_id)
    if deleted:
        return "", 204

    return {"error": "Service not found"}, 404

@app.route("/admin/services", methods=["POST"])
@require_login
def admin_create_service():
    fields, error = validate_service_fields(request.form)

    if error is not None:
        return render_template(
            "admin.html",
            serrvices=database.get_services(),
            error=error
        ), 400

    database.create_service(**fields)

    return redirect(url_for("admin"))

@app.route("/admin/services/<int:service_id>/edit", methods=["GET", "POST"])
@require_login
def admin_edit_service(service_id):
    service = database.get_service(service_id)

    if service is None:
        return "Service not found", 404

    if request.method == "POST":
        fields, error = validate_service_fields(request.form)

        if error is not None:
            return render_template(
                "edit_service.html",
                service=service,
                error=error
            ), 400

        database.update_service(service_id, **fields)

        return redirect(url_for("admin"))

    return render_template("edit_service.html", service=service)

@app.route("/admin/services/<int:service_id>/delete", methods=["GET", "POST"])
@require_login
def admin_delete_service(service_id):
    service = database.get_service(service_id)

    if service is None:
        return "Service not found", 404

    if request.method == "POST":
        deleted = database.delete_service(service_id)
        if not deleted:
            return "Service not found", 404

        return redirect(url_for("admin"))

    return render_template("delete_service.html", service=service)

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("admin"))

    error = None

    if request.method == "POST":
        password = request.form.get("password", "")

        if check_password_hash(app.config["ADMIN_PASSWORD_HASH"], password):
            session.clear()
            session.permanent = True
            session["authenticated"] = True

            return redirect(url_for("admin"))

        error = "Invalid password"

    return render_template("login.html", error=error), 401 if error else 200

@app.route("/admin")
@require_login
def admin():
    services = database.get_services()

    return render_template("admin.html", services=services)

@app.route("/logout", methods=["POST"])
@require_login
def logout():
    session.clear()

    return redirect(url_for("login"))