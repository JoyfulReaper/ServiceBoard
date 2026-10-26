from flask import Flask, jsonify, request
import database
app = Flask(__name__)

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