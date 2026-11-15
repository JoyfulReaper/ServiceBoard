from flask import Flask, jsonify, request, redirect, render_template, session, url_for, flash
from .auth import require_api_key, require_login, is_valid_api_key
from . import database
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from collections.abc import Mapping
from urllib.parse import urlsplit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ipaddress import ip_address
from flask import current_app

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SERVICEBOARD_SECRET_KEY"]

app.config["ADMIN_PASSWORD_HASH"] = os.environ["SERVICEBOARD_ADMIN_PASSWORD_HASH"]

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SERVICEBOARD_ALLOW_INSECURE_COOKIES") != "1"

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

app.config["TRUST_CLOUDFLARE_IP"] = os.environ.get("SERVICEBOARD_TRUST_CLOUDFLARE_IP") == "1"

app.config["RATELIMIT_STORAGE_URI"] = os.environ.get(
    "SERVICEBOARD_RATE_LIMIT_STORAGE_URI",
    "memory://"
)

csrf = CSRFProtect(app)

database.initialize_database()

def get_client_ip():
    remote_ip = get_remote_address()

    if not current_app.config.get("TRUST_CLOUDFLARE_IP", False):
        return remote_ip

    # Only trust forwarded headers from a local proxy.
    if remote_ip not in ("127.0.0.1", "::1"):
        return remote_ip

    forwarded_ip = request.headers.get("CF-Connecting-IP")

    try:
        return str(ip_address(forwarded_ip))
    except (ValueError, TypeError):
        return remote_ip

limiter = Limiter(
    key_func=get_client_ip,
    app=app
)

def public_service(service):
    return {
        "id": service["id"],
        "name": service["name"],
        "description": service["description"],
        "url": service["url"],
        "project_url": service["project_url"],
    }

def service_read_response(data):
    authorization = request.headers.get("Authorization")

    if authorization is None:
        if isinstance(data, list):
            data = [
                public_service(service)
                for service in data
                if service["is_public"]
            ]
        else:
            if not data["is_public"]:
                return jsonify({"error": "Service not found"}), 404

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

    if not isinstance(name, str):
        return None, "Invalid data format"

    name = name.strip()

    if not name:
        return None, "Service name required"

    fields = {"name": name}

    optional_fields = (
        "url",
        "project_url",
        "host",
        "deployment_type",
        "description",
        "runtime_name",
        "runtime_version"
    )

    for field in optional_fields:
        value = data.get(field)

        if value is not None and not isinstance(value, str):
            return None, f"{field} must be a string or null"

        if isinstance(value, str):
            value = value.strip() or None

        fields[field] = value

    allowed_schemes = {
        "url": {"http", "https", "gemini", "gopher"},
        "project_url": {"http", "https"}
    }

    for field, schemes in allowed_schemes.items():
        value = fields[field]

        if value is None:
            continue

        try:
            parsed = urlsplit(value)

            valid = (
                parsed.scheme in schemes
                and bool(parsed.hostname)
                and not any(character.isspace() for character in value)
            )

        except ValueError:
            valid = False

        if not valid:
            return None, f"{field} must be a valid URL with an allowed scheme"

    if fields["runtime_version"] and not fields["runtime_name"]:
        return None, "Runtime name required when runtime version is provided"

    if "is_public" in data:
        is_public = data["is_public"]

        if not isinstance(is_public, bool):
            return None, "is_public must be a boolean"

        fields["is_public"] = is_public

    return fields, None

def render_admin_page(**extra_context):
    sort_fields = {
        "name": "name",
        "host": "host",
        "deployment": "deployment_type",
        "runtime": "runtime_name",
    }

    sort_by = request.args.get("sort", "name")
    if sort_by not in sort_fields:
        sort_by = "name"

    sort_field = sort_fields[sort_by]

    visibility = request.args.get("visibility", "all")

    if visibility not in ("all", "public", "private"):
        visibility = "all"

    services = database.get_services()
    has_any_services = bool(services)

    hosts = sorted(
        {service["host"] for service in services if service["host"]},
        key=str.casefold
    )

    deployment_types = sorted(
        {service["deployment_type"] for service in services if service["deployment_type"]},
        key=str.casefold
    )

    runtimes = sorted(
        {service["runtime_name"] for service in services if service["runtime_name"]},
        key=str.casefold
    )

    selected_runtime = request.args.get("runtime", "")

    if selected_runtime not in runtimes:
        selected_runtime = ""

    selected_host = request.args.get("host", "")

    if selected_host not in hosts:
        selected_host = ""

    if selected_host:
        services = [
            service for service in services
            if service["host"] == selected_host
        ]

    selected_deployment = request.args.get("deployment", "")

    if selected_deployment not in deployment_types:
        selected_deployment = ""

    if visibility == "public":
        services = [service for service in services if service["is_public"]]
    elif visibility == "private":
        services = [service for service in services if not service["is_public"]]

    if selected_deployment:
        services = [
            service for service in services
            if service["deployment_type"] == selected_deployment
        ]

    if selected_runtime:
        services = [
            service for service in services
            if service["runtime_name"] == selected_runtime
        ]

    services = sorted(
        services,
        key=lambda service: (
            service[sort_field] is None,
            (service[sort_field] or "").casefold(),
            service["name"].casefold()
        )
    )

    return render_template(
        "admin.html",
        services=services,
        hosts=hosts,
        selected_host=selected_host,
        selected_sort=sort_by,
        selected_visibility=visibility,
        deployment_types=deployment_types,
        runtimes=runtimes,
        selected_runtime=selected_runtime,
        selected_deployment=selected_deployment,
        has_any_services=has_any_services,
        **extra_context
    )

@app.route('/')
def index():
    services = [
        {
            "name": service["name"],
            "url": service["url"],
            "project_url": service["project_url"],
            "description": service["description"]
        }
        for service in database.get_services()
        if service["is_public"]
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
        return { "error": "Service not found"}, 404

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
    form_data = request.form.to_dict()
    form_data["is_public"] = "is_public" in request.form

    fields, error = validate_service_fields(form_data)

    if error is not None:
        return render_admin_page(
            error=error,
            form_is_public=form_data["is_public"]
        ), 400

    database.create_service(**fields)

    return redirect(url_for("admin"))

@app.route("/admin/services/<int:service_id>/edit", methods=["GET", "POST"])
@require_login
def admin_edit_service(service_id):
    service = database.get_service(service_id)

    if service is None:
        return "Service not found", 404

    # Determine Previous/Next services by ID.
    service_ids = sorted(item["id"] for item in database.get_services())

    current_index = service_ids.index(service_id)

    previous_id = service_ids[current_index - 1] if current_index > 0 else None
    next_id = service_ids[current_index + 1] if current_index < len(service_ids) - 1 else None

    if request.method == "POST":
        form_data = request.form.to_dict()
        form_data["is_public"] = "is_public" in request.form

        fields, error = validate_service_fields(form_data)

        if error is not None:
            return render_template(
                "edit_service.html",
                service=service,
                form_is_public=form_data["is_public"],
                error=error,
                previous_id=previous_id,
                next_id=next_id
            ), 400

        database.update_service(service_id, **fields)

        flash("Changes saved successfully.", "success")

        return redirect(url_for("admin_edit_service", service_id=service_id))

    return render_template(
        "edit_service.html",
        service=service,
        previous_id=previous_id,
        next_id=next_id
    )

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
@limiter.limit(
    "5 per 15 minutes",
    methods=["POST"],
    deduct_when=lambda response: response.status_code == 401
)
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
    return render_admin_page()

@app.route("/logout", methods=["POST"])
@require_login
def logout():
    session.clear()

    return redirect(url_for("login"))