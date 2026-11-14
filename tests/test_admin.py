import re
from src.serviceboard import database

def extract_csrf_token(response):
    match = re.search(
        r'name="csrf_token" value="([^"]+)"',
        response.get_data(as_text=True)
    )

    assert match is not None, "CSRF token missing from response"

    return match.group(1)

def login_as_admin(client):
    login_page = client.get("/login")

    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": extract_csrf_token(login_page)
        }
    )

    assert response.status_code == 302

    admin_page = client.get("/admin")
    assert admin_page.status_code == 200

    return admin_page

def test_admin_requires_login(client):
    response = client.get("/admin")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_login_requires_csrf_token(client):
    login_url = client.get("/admin").headers["Location"]

    response = client.post(
        login_url,
        data={"password": "test-password"}
    )

    assert response.status_code == 400
    assert client.get("/admin").status_code == 302

def test_login_with_valid_password(client):
    login_page = client.get("/login")

    assert login_page.status_code == 200

    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": extract_csrf_token(login_page)
        }
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")

    assert client.get("/admin").status_code == 200

def test_login_rejects_incorrect_password(client):
    login_page = client.get("/login")

    response = client.post(
        "/login",
        data={
            "password": "incorrect-password",
            "csrf_token": extract_csrf_token(login_page)
        }
    )

    assert response.status_code == 401
    assert b"Invalid password" in response.data
    assert client.get("/admin").status_code == 302

def test_logout_clears_session(client):
    admin_page = login_as_admin(client)

    logout_response = client.post(
        "/logout",
        data={"csrf_token": extract_csrf_token(admin_page)}
    )

    assert logout_response.status_code == 302
    assert client.get("/admin").status_code == 302

def test_admin_create_requires_csrf_token(client):
    login_as_admin(client)

    response = client.post(
        "/admin/services",
        data={
            "name": "Unauthorized Service",
            "url": "https://example.com"
        }
    )

    assert response.status_code == 400
    assert database.get_services() == []

def test_admin_can_create_service(client):
    admin_page = login_as_admin(client)

    response = client.post(
        "/admin/services",
        data={
            "csrf_token": extract_csrf_token(admin_page),
            "name": "Packet Garden",
            "url": "https://garden.kgivler.com",
            "host": "FrontDesk",
            "runtime_name": "Microsoft.AspNetCore.App",
            "runtime_version": "10.0.15"
        }
    )

    assert response.status_code == 302

    services = database.get_services()

    assert len(services) == 1

    service = services[0]

    assert service["name"] == "Packet Garden"
    assert service["url"] == "https://garden.kgivler.com"
    assert service["host"] == "FrontDesk"
    assert service["runtime_name"] == "Microsoft.AspNetCore.App"
    assert service["runtime_version"] == "10.0.15"

def test_admin_can_edit_service(client):
    created = database.create_service(
        "Original Service",
        "https://old.example.com",
        "Clanker"
    )

    login_as_admin(client)

    edit_url = f"/admin/services/{created['id']}/edit"

    edit_page = client.get(edit_url)
    assert edit_page.status_code == 200

    response = client.post(
        edit_url,
        data={
            "csrf_token": extract_csrf_token(edit_page),
            "name": "Updated Service",
            "url": "https://new.example.com",
            "host": "FrontDesk",
            "runtime_name": "Microsoft.AspNetCore.App",
            "runtime_version": "10.0.15"
        }
    )

    assert response.status_code == 302

    updated = database.get_service(created["id"])

    assert updated is not None
    assert updated["id"] == created["id"]
    assert updated["name"] == "Updated Service"
    assert updated["url"] == "https://new.example.com"
    assert updated["host"] == "FrontDesk"
    assert updated["runtime_name"] == "Microsoft.AspNetCore.App"
    assert updated["runtime_version"] == "10.0.15"

def test_admin_can_delete_service(client):
    created = database.create_service(
        "Service To Delete",
        "https://example.com"
    )

    login_as_admin(client)

    delete_url = f"/admin/services/{created['id']}/delete"

    confirmation_page = client.get(delete_url)

    assert confirmation_page.status_code == 200
    assert b"Service To Delete" in confirmation_page.data

    assert database.get_service(created["id"]) == created

    response = client.post(
        delete_url,
        data={
            "csrf_token": extract_csrf_token(confirmation_page)
        }
    )

    assert response.status_code == 302
    assert database.get_service(created["id"]) is None

def test_admin_create_rejects_invalid_runtime(client):
    admin_page = login_as_admin(client)

    response = client.post(
        "/admin/services",
        data={
            "csrf_token": extract_csrf_token(admin_page),
            "name": "Invalid Runtime",
            "url": "https://example.com",
            "runtime_version": "10.0.15"
        }
    )

    assert response.status_code == 400

    assert b"Runtime name required when runtime version is provided" in response.data

    assert database.get_services() == []

def test_admin_edit_rejects_invalid_runtime(client):
    original = database.create_service(
        "Original Service",
        "https://old.example.com",
        "Clanker",
        "Microsoft.AspNetCore.App",
        "10.0.15"
    )

    login_as_admin(client)

    edit_url = f"/admin/services/{original['id']}/edit"

    edit_page = client.get(edit_url)
    assert edit_page.status_code == 200

    response = client.post(
        edit_url,
        data={
            "csrf_token": extract_csrf_token(edit_page),
            "name": "Modified Service",
            "url": "https://new.example.com",
            "host": "DeepDish",
            "runtime_name": "",
            "runtime_version": "10.0.20"
        }
    )

    assert response.status_code == 400

    assert b"Runtime name required when runtime version is provided" in response.data

    assert database.get_service(original["id"]) == original