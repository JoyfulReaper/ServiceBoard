from flask import Flask, jsonify, request

app = Flask(__name__)

services = [
    {
        "id": 1,
        "name": "Packet Garden",
        "url": "https://garden.kgivler.com"
    },
    {
        "id": 2,
        "name": "Random Steam Game",
        "url": "https://randomsteam.kgivler.com"
    }
]

@app.route('/')
def index():
    return "ServiceBoard says Hello World"

@app.route('/services')
def get_services():
    return jsonify(services)

@app.route('/services/<int:service_id>')
def get_service(service_id):
    service = next(
        (service for service in services if service["id"] == service_id),
        None
    )

    if service is None:
        return { "error": "Service not found" }, 404

    return jsonify(service)

@app.route("/services", methods=["POST"])
def create_service():
    data = request.get_json()

    service = {
        "id": max((service["id"] for service in services), default = 0) + 1,
        "name": data["name"],
        "url": data["url"]
    }

    services.append(service)

    return jsonify(service), 201