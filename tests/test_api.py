from src.serviceboard import database


def test_public_services_hide_private_fields(client):
    created = database.create_service(
        "Test Service",
        "https://example.com",
        "FrontDesk",
        "Microsoft.AspNetCore.App",
        "10.0.15"
    )

    response = client.get("/services")

    assert response.status_code == 200

    services = response.get_json()

    assert services == [
        {
            "id": created["id"],
            "name": "Test Service",
            "url": "https://example.com"
        }
    ]

def test_valid_bearer_token_shows_private_fields(client):
    created = database.create_service(
        "Test Service",
        "https://example.com",
        "FrontDesk",
        "Microsoft.AspNetCore.App",
        "10.0.15"
    )

    response = client.get(
        "/services",
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 200
    assert response.get_json() == [created]
    assert response.headers["Cache-Control"] == "no-store"

def test_invalid_bearer_token_is_rejected(client):
    response = client.get(
        "/services",
        headers={"Authorization": "Bearer incorrect-key"}
    )

    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"

def test_create_service_requires_api_key(client):
    response = client.post(
        "/services",
        json={
            "name": "Unauthorized Service",
            "url": "https://example.com"
        }
    )

    assert response.status_code == 401
    assert database.get_services() == []

def test_create_service_with_valid_api_key(client):
    payload = {
        "name": "Packet Garden",
        "url": "https://garden.kgivler.com",
        "host": "FrontDesk",
        "runtime_name": "Microsoft.AspNetCore.App",
        "runtime_version": "10.0.15"
    }

    response = client.post(
        "/services",
        json=payload,
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 201

    created = response.get_json()

    assert created["id"] > 0
    assert created["name"] == payload["name"]
    assert created["host"] == payload["host"]
    assert created["runtime_version"] == payload["runtime_version"]

    assert database.get_service(created["id"]) == created

def test_update_service_requires_api_key(client):
    original = database.create_service(
        "Original Service",
        "https://example.com"
    )

    response = client.put(
        f"/services/{original['id']}",
        json={
            "name": "Modified Service",
            "url": "https://modified.example.com"
        }
    )

    assert response.status_code == 401
    assert database.get_service(original["id"]) == original