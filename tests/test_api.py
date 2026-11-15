from src.serviceboard import database


def test_public_services_hide_private_fields(client):
    created = database.create_service(
        "Test Service",
        "https://example.com",
        "FrontDesk",
        "Microsoft.AspNetCore.App",
        "10.0.15",
        deployment_type="docker",
        description="A test service"
    )

    response = client.get("/services")

    assert response.status_code == 200

    services = response.get_json()

    assert services == [
        {
            "id": created["id"],
            "name": "Test Service",
            "url": "https://example.com",
            "description": "A test service"
        }
    ]

def test_valid_bearer_token_shows_private_fields(client):
    created = database.create_service(
        "Test Service",
        "https://example.com",
        "FrontDesk",
        "Microsoft.AspNetCore.App",
        "10.0.15",
        deployment_type="docker"
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

def test_update_service_with_valid_api_key(client):
    original = database.create_service(
        "Original Service",
        "https://old.example.com",
        "Clanker"
    )

    payload = {
        "name": "Updated Service",
        "url": "https://new.example.com",
        "host": "FrontDesk",
        "runtime_name": "Microsoft.AspNetCore.App",
        "runtime_version": "10.0.15"
    }

    response = client.put(
        f"/services/{original['id']}",
        json=payload,
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 200

    updated = response.get_json()

    assert updated["id"] == original["id"]

    for field, value in payload.items():
        assert updated[field] == value

    assert database.get_service(original["id"]) == updated

def test_delete_service_requires_api_key(client):
    created = database.create_service(
        "Protected Service",
        "https://example.com"
    )

    response = client.delete(
        f"/services/{created['id']}"
    )

    assert response.status_code == 401
    assert database.get_service(created["id"]) == created

def test_delete_service_with_valid_api_key(client):
    created = database.create_service(
        "Service To Delete",
        "https://example.com"
    )

    response = client.delete(
        f"/services/{created['id']}",
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 204
    assert response.data == b""
    assert database.get_service(created["id"]) is None

def test_create_rejects_runtime_version_without_name(client):
    response = client.post(
        "/services",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "runtime_version": "10.0.15"
        },
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 400

    assert response.get_json()["error"] == (
        "Runtime name required when runtime version is provided"
    )

    assert database.get_services() == []

def test_api_create_and_update_deployment_type(client):
    headers = {"Authorization": "Bearer test-api-key"}

    response = client.post(
        "/services",
        json={
            "name": "Deployment Test",
            "url": "https://example.com",
            "deployment_type": "docker"
        },
        headers=headers
    )

    assert response.status_code == 201

    created = response.get_json()

    assert created["deployment_type"] == "docker"

    response = client.put(
        f"/services/{created['id']}",
        json={
            "name": "Deployment Test",
            "url": "https://example.com",
            "deployment_type": "systemd"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.get_json()["deployment_type"] == "systemd"

    retrieved = database.get_service(created["id"])

    assert retrieved["deployment_type"] == "systemd"

def test_api_create_and_update_description(client):
    headers = {"Authorization": "Bearer test-api-key"}

    response = client.post(
        "/services",
        json={
            "name": "SmolSearch",
            "url": "https://example.com",
            "description": "A search engine for the small web"
        },
        headers=headers
    )

    assert response.status_code == 201

    created = response.get_json()

    assert created["description"] == "A search engine for the small web"
    assert database.get_service(created["id"])["description"] == "A search engine for the small web"

    response = client.put(
        f"/services/{created['id']}",
        json={
            "name": "SmolSearch",
            "url": "https://example.com",
            "description": "Searches Gemini and Gopher content"
        },
        headers=headers
    )

    assert response.status_code == 200

    updated = response.get_json()

    assert updated["description"] == "Searches Gemini and Gopher content"
    assert database.get_service(created["id"])["description"] == "Searches Gemini and Gopher content"

def test_public_homepage_shows_description_without_private_fields(client):
    database.create_service(
        "SmolSearch",
        "https://example.com",
        host="PrivateHost123",
        description="Searches Gemini and Gopher content"
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"SmolSearch" in response.data
    assert b"Searches Gemini and Gopher content" in response.data
    assert b"PrivateHost123" not in response.data

def test_private_services_hidden_from_public(client):
    public = database.create_service(
        "Public Service",
        "https://public.example.com"
    )

    private = database.create_service(
        "Private Service",
        "https://private.example.com",
        is_public=False
    )

    # Public homepage
    response = client.get("/")

    assert response.status_code == 200
    assert b"Public Service" in response.data
    assert b"Private Service" not in response.data

    # Public JSON listing
    response = client.get("/services")

    assert response.status_code == 200

    services = response.get_json()
    assert len(services) == 1
    assert services[0]["id"] == public["id"]

    # Direct access without authentication
    response = client.get(f"/services/{private['id']}")

    assert response.status_code == 404

    # Authenticated access
    response = client.get(
        f"/services/{private['id']}",
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 200
    assert response.get_json() == private

    # Authenticated listing includes both services
    response = client.get(
        "/services",
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 200
    assert len(response.get_json()) == 2

def test_api_service_visibility(client):
    headers = {"Authorization": "Bearer test-api-key"}

    # Create a private service.
    response = client.post(
        "/services",
        json={
            "name": "Private Service",
            "url": "https://example.com",
            "is_public": False
        },
        headers=headers
    )

    assert response.status_code == 201

    created = response.get_json()
    assert created["is_public"] is False

    service_id = created["id"]

    # Updating without visibility should preserve it.
    response = client.put(
        f"/services/{service_id}",
        json={
            "name": "Updated Private Service",
            "url": "https://example.com"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.get_json()["is_public"] is False

    # Explicitly make the service public.
    response = client.put(
        f"/services/{service_id}",
        json={
            "name": "Updated Private Service",
            "url": "https://example.com",
            "is_public": True
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.get_json()["is_public"] is True

def test_api_rejects_invalid_visibility(client):
    response = client.post(
        "/services",
        json={
            "name": "Invalid Service",
            "url": "https://example.com",
            "is_public": "false"
        },
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "is_public must be a boolean"

    assert database.get_services() == []

def test_update_nonexistent_service_returns_404(client):
    response = client.put(
        "/services/999999",
        json={
            "name": "Missing Service",
            "url": "https://example.com"
        },
        headers={"Authorization": "Bearer test-api-key"}
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Service not found"