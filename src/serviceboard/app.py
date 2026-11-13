from flask import Flask, jsonify, request, redirect, render_template, session, url_for
from .auth import require_api_key, require_login
from . import database
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SERVICEBOARD_SECRET_KEY"]

app.config["ADMIN_PASSWORD_HASH"] = os.environ["SERVICEBOARD_ADMIN_PASSWORD_HASH"]

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SERVICEBOARD_ALLOW_INSECURE_COOKIES") != "1"

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

csrf = CSRFProtect(app)

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
@csrf.exempt
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

    name = name.strip()
    url = url.strip()

    if not name or not url:
        return { "error": "Service name and url required" }, 400

    optional_fields = {}

    for field in ("host", "runtime_name", "runtime_version"):
        value = data.get(field)

        if value is not None and not isinstance(value, str):
            return { "error": f"{field} must be a string or null"}, 400

        if isinstance(value, str):
            value = value.strip() or None

        optional_fields[field] = value

    if optional_fields["runtime_version"] and not optional_fields["runtime_name"]:
        return { "error": "Runtime name required when runtime version is provided" }, 400

    service = database.create_service(name, url, **optional_fields)
    return jsonify(service), 201

@app.route("/services/<int:service_id>", methods=["PUT"])
@require_api_key
@csrf.exempt
def update_service(service_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return { "error": "Invalid data format" }, 400

    name = data.get("name")
    url = data.get("url")

    if not isinstance(name, str) or not isinstance(url, str):
        return { "error": "Invalid data format" }, 400

    name = name.strip()
    url = url.strip()

    if not name or not url:
        return { "error": "Service name and url required" }, 400

    optional_fields = {}
    for field in ("host", "runtime_name", "runtime_version"):
        value = data.get(field)

        if value is not None and not isinstance(value, str):
            return {"error": f"{field} must be a string or null"}, 400

        if isinstance(value, str):
            value = value.strip() or None

        optional_fields[field] = value

    if optional_fields["runtime_version"] and not optional_fields["runtime_name"]:
        return {"error": "Runtime name required when runtime version is provided"}, 400

    service = database.update_service(service_id, name, url, **optional_fields)

    if service is None:
        return {"error": "Service not found"}, 404

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
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()

    host = request.form.get("host", "").strip() or None
    runtime_name = request.form.get("runtime_name", "").strip() or None
    runtime_version = request.form.get("runtime_version", "").strip() or None

    if not name or not url:
        return render_template("admin.html",
                               services=database.get_services(),
                               error="Service name and URL are required"), 400

    if runtime_version and not runtime_name:
        return render_template("admin.html",
                               services=database.get_services(),
                               error="Runtime name is required when specifying a version"), 400

    database.create_service(
        name,
        url,
        host,
        runtime_name,
        runtime_version
    )

    return redirect(url_for("admin"))

@app.route("/admin/services/<int:service_id>/edit", methods=["GET", "POST"])
@require_login
def admin_edit_service(service_id):
    service = database.get_service(service_id)

    if service is None:
        return "Service not found", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()

        host = request.form.get("host", "").strip() or None
        runtime_name = request.form.get("runtime_name", "").strip() or None
        runtime_version = request.form.get("runtime_version", "").strip() or None

        if not name or not url:
            return render_template("edit_service.html",
                                   service=service,
                                   error="Service name and URL are required"), 400

        if runtime_version and not runtime_name:
            return render_template("edit_service.html",
                                   service=service,
                                   error="Runtime name is required when specifying a version"), 400

        database.update_service(
            service_id,
            name,
            url,
            host,
            runtime_name,
            runtime_version)

        return redirect(url_for("admin"))

    return render_template("edit_service.html", service=service)

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