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
            "deployment_type": "docker",
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
    assert service["deployment_type"] == "docker"

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
            "deployment_type": "systemd",
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
    assert updated["deployment_type"] == "systemd"

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

def test_admin_create_and_edit_description(client):
    admin_page = login_as_admin(client)

    response = client.post(
        "/admin/services",
        data={
            "csrf_token": extract_csrf_token(admin_page),
            "name": "SmolSearch",
            "url": "https://example.com",
            "description": "Searches the small web"
        }
    )

    assert response.status_code == 302

    created = database.get_services()[0]

    assert created["description"] == "Searches the small web"

    edit_url = f"/admin/services/{created['id']}/edit"

    edit_page = client.get(edit_url)

    assert edit_page.status_code == 200
    assert b"Searches the small web" in edit_page.data

    response = client.post(
        edit_url,
        data={
            "csrf_token": extract_csrf_token(edit_page),
            "name": "SmolSearch",
            "url": "https://example.com",
            "description": "Searches Gemini and Gopher"
        }
    )

    assert response.status_code == 302

    updated = database.get_service(created["id"])

    assert updated["description"] == "Searches Gemini and Gopher"

def test_admin_can_change_service_visibility(client):
    admin_page = login_as_admin(client)

    assert b'name="is_public"' in admin_page.data

    # An unchecked checkbox is omitted from the submitted form.
    response = client.post(
        "/admin/services",
        data={
            "csrf_token": extract_csrf_token(admin_page),
            "name": "Internal Service",
            "url": "https://internal.example.com"
        }
    )

    assert response.status_code == 302

    created = database.get_services()[0]
    assert created["is_public"] is False

    # Edit the service and make it public.
    edit_url = f"/admin/services/{created['id']}/edit"
    edit_page = client.get(edit_url)

    assert edit_page.status_code == 200

    response = client.post(
        edit_url,
        data={
            "csrf_token": extract_csrf_token(edit_page),
            "name": "Internal Service",
            "url": "https://internal.example.com",
            "is_public": "on"
        }
    )

    assert response.status_code == 302

    updated = database.get_service(created["id"])
    assert updated["is_public"] is True

def test_admin_displays_visibility_badges(client):
    database.create_service(
        "Service One",
        "https://example.com",
        is_public=True
    )

    database.create_service(
        "Service Two",
        "https://internal.example.com",
        is_public=False
    )

    login_as_admin(client)

    response = client.get("/admin")

    assert response.status_code == 200
    assert b"visibility-public" in response.data
    assert b"visibility-private" in response.data

def test_edit_page_uses_shared_layout(client):
    created = database.create_service(
        "Test Service",
        "https://example.com",
        is_public=False
    )

    login_as_admin(client)

    response = client.get(
        f"/admin/services/{created['id']}/edit"
    )

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "site-header" in html
    assert "style.css" in html
    assert "Edit Test Service" in html
    assert 'class="service-form"' in html
    assert 'name="csrf_token"' in html
    assert 'name="is_public"' in html

def test_delete_page_uses_shared_layout(client):
    created = database.create_service(
        "Test Service",
        "https://example.com"
    )

    login_as_admin(client)

    response = client.get(
        f"/admin/services/{created['id']}/delete"
    )

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "site-header" in html
    assert "style.css" in html
    assert "Delete Service" in html
    assert "Test Service" in html
    assert 'name="csrf_token"' in html
    assert 'class="danger-button"' in html
    assert "Cancel" in html

def test_admin_filters_by_visibility(client):
    database.create_service(
        "Alpha Service",
        "https://alpha.example.com",
        is_public=True
    )

    database.create_service(
        "Beta Service",
        "https://beta.example.com",
        is_public=False
    )

    login_as_admin(client)

    # Show private services.
    response = client.get("/admin?visibility=private")

    assert response.status_code == 200
    assert b"Beta Service" in response.data
    assert b"Alpha Service" not in response.data

    # Show public services.
    response = client.get("/admin?visibility=public")

    assert response.status_code == 200
    assert b"Alpha Service" in response.data
    assert b"Beta Service" not in response.data

    # Show everything.
    response = client.get("/admin?visibility=all")

    assert response.status_code == 200
    assert b"Alpha Service" in response.data
    assert b"Beta Service" in response.data

def test_admin_filters_by_host(client):
    database.create_service(
        "Search Service",
        "https://search.example.com",
        host="Clanker",
        is_public=True
    )

    database.create_service(
        "Matrix Service",
        "https://matrix.example.com",
        host="Molasses",
        is_public=True
    )

    database.create_service(
        "Backup Service",
        "https://backup.example.com",
        host="Clanker",
        is_public=False
    )

    login_as_admin(client)

    # Filter by Clanker.
    response = client.get("/admin?host=Clanker")

    assert response.status_code == 200
    assert b"Search Service" in response.data
    assert b"Backup Service" in response.data
    assert b"Matrix Service" not in response.data

    # Combine host and visibility filters.
    response = client.get("/admin?host=Clanker&visibility=private")

    assert response.status_code == 200
    assert b"Backup Service" in response.data
    assert b"Search Service" not in response.data

    # All hosts.
    response = client.get("/admin")

    assert response.status_code == 200
    assert b"Search Service" in response.data
    assert b"Matrix Service" in response.data
    assert b"Backup Service" in response.data

def test_admin_filters_by_deployment_type(client):
    database.create_service(
        "Docker Service",
        "https://docker.example.com",
        host="Clanker",
        deployment_type="docker"
    )

    database.create_service(
        "Systemd Service",
        "https://systemd.example.com",
        host="Clanker",
        deployment_type="systemd"
    )

    database.create_service(
        "Other Docker Service",
        "https://other.example.com",
        host="Molasses",
        deployment_type="docker"
    )

    login_as_admin(client)

    # Only systemd services.
    response = client.get("/admin?deployment=systemd")

    assert response.status_code == 200
    assert b"Systemd Service" in response.data
    assert b"Docker Service" not in response.data
    assert b"Other Docker Service" not in response.data

    # Combine deployment and host filters.
    response = client.get("/admin?deployment=docker&host=Clanker")

    assert response.status_code == 200
    assert b"Docker Service" in response.data
    assert b"Systemd Service" not in response.data
    assert b"Other Docker Service" not in response.data

def test_admin_filters_by_runtime(client):
    database.create_service(
        "ASP.NET Service",
        "https://dotnet.example.com",
        host="Clanker",
        runtime_name="Microsoft.AspNetCore.App",
        runtime_version="10.0.15",
        deployment_type="docker"
    )

    database.create_service(
        "Flask Service",
        "https://flask.example.com",
        host="Clanker",
        runtime_name="Python",
        runtime_version="3.14.6",
        deployment_type="systemd"
    )

    database.create_service(
        "Another Python Service",
        "https://python.example.com",
        host="Molasses",
        runtime_name="Python",
        runtime_version="3.14.6",
        deployment_type="docker"
    )

    login_as_admin(client)

    # Filter by Python.
    response = client.get("/admin?runtime=Python")

    assert response.status_code == 200
    assert b"Flask Service" in response.data
    assert b"Another Python Service" in response.data
    assert b"ASP.NET Service" not in response.data

    # Combine runtime and deployment filters.
    response = client.get("/admin?runtime=Python&deployment=docker")

    assert response.status_code == 200
    assert b"Another Python Service" in response.data
    assert b"Flask Service" not in response.data
    assert b"ASP.NET Service" not in response.data

def test_admin_empty_state_messages(client):
    login_as_admin(client)

    # No services exist.
    response = client.get("/admin")

    assert response.status_code == 200
    assert b"No services have been added yet." in response.data

    # Add one public service.
    database.create_service(
        "Test Service",
        "https://example.com",
        is_public=True
    )

    # Filter for private services, producing zero matches.
    response = client.get("/admin?visibility=private")

    assert response.status_code == 200
    assert b"No services match the selected filters." in response.data
    assert b"No services have been added yet." not in response.data

def test_admin_validation_error_preserves_filter_options(client):
    database.create_service(
        "Existing Service",
        "https://example.com",
        host="Clanker",
        deployment_type="docker",
        runtime_name="Python"
    )

    admin_page = login_as_admin(client)

    response = client.post(
        "/admin/services",
        data={
            "csrf_token": extract_csrf_token(admin_page),
            "name": "Invalid Service",
            "url": "https://invalid.example.com",
            "runtime_version": "3.14"
        }
    )

    assert response.status_code == 400

    html = response.get_data(as_text=True)

    assert "Runtime name required" in html
    assert 'value="Clanker"' in html
    assert 'value="docker"' in html
    assert 'value="Python"' in html

def test_admin_creates_private_job_without_endpoint(client):
    admin_page = login_as_admin(client)

    html = admin_page.get_data(as_text=True)

    # Project URL field must exist.
    assert 'name="project_url"' in html

    # Service URL must be optional.
    url_input = re.search(r'<input\b[^>]*id="url"[^>]*>', html)

    assert url_input is not None
    assert "required" not in url_input.group(0)

    # New services must default to private.
    visibility_input = re.search(
        r'<input\b[^>]*id="is_public"[^>]*>',
        html
    )

    assert visibility_input is not None
    assert "checked" not in visibility_input.group(0)

    response = client.post(
        "/admin/services",
        data={
            "csrf_token": extract_csrf_token(admin_page),
            "name": "VPS Backup",
            "url": "",
            "project_url": "https://github.com/JoyfulReaper/InfraOps",
            "host": "ScopeCreep",
            "deployment_type": "systemd"
        }
    )

    assert response.status_code == 302

    services = database.get_services()

    assert len(services) == 1

    service = services[0]

    assert service["name"] == "VPS Backup"
    assert service["url"] is None
    assert service["project_url"] == "https://github.com/JoyfulReaper/InfraOps"
    assert service["host"] == "ScopeCreep"
    assert service["deployment_type"] == "systemd"
    assert service["is_public"] is False

def test_admin_edit_project_url_without_endpoint(client):
    created = database.create_service(
        "VPS Backup",
        host="ScopeCreep",
        deployment_type="systemd",
        project_url="https://github.com/JoyfulReaper/InfraOps",
        is_public=False
    )

    login_as_admin(client)

    edit_url = f"/admin/services/{created['id']}/edit"
    edit_page = client.get(edit_url)

    assert edit_page.status_code == 200

    html = edit_page.get_data(as_text=True)

    # Existing project URL should be populated.
    assert 'name="project_url"' in html
    assert 'value="https://github.com/JoyfulReaper/InfraOps"' in html

    # Missing service URLs should display as empty fields.
    url_input = re.search(r'<input\b[^>]*id="url"[^>]*>', html)

    assert url_input is not None
    assert "required" not in url_input.group(0)
    assert 'value="None"' not in url_input.group(0)

    # Update the project URL.
    response = client.post(
        edit_url,
        data={
            "csrf_token": extract_csrf_token(edit_page),
            "name": "VPS Backup",
            "url": "",
            "project_url": "https://github.com/JoyfulReaper/InfraOps/tree/main/VPS",
            "host": "ScopeCreep",
            "deployment_type": "systemd"
        }
    )

    assert response.status_code == 302

    updated = database.get_service(created["id"])

    assert updated["url"] is None
    assert updated["project_url"] == "https://github.com/JoyfulReaper/InfraOps/tree/main/VPS"
    assert updated["host"] == "ScopeCreep"
    assert updated["is_public"] is False

def test_login_rate_limited_after_five_failures(client):
    login_page = client.get("/login")
    csrf_token = extract_csrf_token(login_page)

    # Five incorrect passwords should be rejected normally.
    for attempt in range(5):
        response = client.post(
            "/login",
            data={
                "password": "incorrect-password",
                "csrf_token": csrf_token
            }
        )

        assert response.status_code == 401, f"Attempt {attempt + 1}"

    # Even the correct password must be blocked during the cooldown.
    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": csrf_token
        }
    )

    assert response.status_code == 429

    # The login page itself should remain accessible.
    assert client.get("/login").status_code == 200

def test_login_rate_limit_is_per_ip(client):
    login_page = client.get("/login")
    csrf_token = extract_csrf_token(login_page)

    # First IP exhausts its allowance.
    for _ in range(5):
        response = client.post(
            "/login",
            data={
                "password": "incorrect-password",
                "csrf_token": csrf_token
            },
            environ_overrides={"REMOTE_ADDR": "192.0.2.10"}
        )

        assert response.status_code == 401

    # The first IP is now blocked, even with the correct password.
    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": csrf_token
        },
        environ_overrides={"REMOTE_ADDR": "192.0.2.10"}
    )

    assert response.status_code == 429

    # A different IP can still authenticate.
    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": csrf_token
        },
        environ_overrides={"REMOTE_ADDR": "192.0.2.11"}
    )

    assert response.status_code == 302

def test_successful_logins_do_not_count_toward_rate_limit(client):
    for _ in range(6):
        login_page = client.get("/login")

        response = client.post(
            "/login",
            data={
                "password": "test-password",
                "csrf_token": extract_csrf_token(login_page)
            }
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/admin")

        # Log out so the next iteration performs another real login.
        admin_page = client.get("/admin")

        response = client.post(
            "/logout",
            data={
                "csrf_token": extract_csrf_token(admin_page)
            }
        )

        assert response.status_code == 302

def test_cloudflare_tunnel_rate_limits_by_visitor_ip(client, monkeypatch):
    monkeypatch.setitem(client.application.config, "TRUST_CLOUDFLARE_IP", True)

    login_page = client.get("/login")
    csrf_token = extract_csrf_token(login_page)

    # Visitor A sends five incorrect passwords through the local tunnel.
    for _ in range(5):
        response = client.post(
            "/login",
            data={
                "password": "incorrect-password",
                "csrf_token": csrf_token
            },
            headers={"CF-Connecting-IP": "198.51.100.10"},
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"}
        )

        assert response.status_code == 401

    # Visitor B uses the same tunnel but has a different public IP.
    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": csrf_token
        },
        headers={"CF-Connecting-IP": "198.51.100.11"},
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"}
    )

    assert response.status_code == 302

def test_cloudflare_header_ignored_for_untrusted_connections(client, monkeypatch):
    monkeypatch.setitem(client.application.config, "TRUST_CLOUDFLARE_IP", True)

    login_page = client.get("/login")
    csrf_token = extract_csrf_token(login_page)

    # Attacker sends five incorrect passwords from one connection IP.
    # Each request claims a different Cloudflare visitor IP.
    for attempt in range(5):
        response = client.post(
            "/login",
            data={
                "password": "incorrect-password",
                "csrf_token": csrf_token
            },
            headers={"CF-Connecting-IP": f"198.51.100.{attempt + 10}"},
            environ_overrides={"REMOTE_ADDR": "203.0.113.50"}
        )

        assert response.status_code == 401

    # Another forged header must not bypass the exhausted allowance.
    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": csrf_token
        },
        headers={"CF-Connecting-IP": "198.51.100.99"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.50"}
    )

    assert response.status_code == 429

def test_invalid_cloudflare_ips_fall_back_to_connection_ip(client, monkeypatch):
    monkeypatch.setitem(client.application.config, "TRUST_CLOUDFLARE_IP", True)

    login_page = client.get("/login")
    csrf_token = extract_csrf_token(login_page)

    invalid_ips = [
        "not-an-ip",
        "999.999.999.999",
        "198.51.100.10, 203.0.113.20",
        "",
        "invalid-address"
    ]

    for invalid_ip in invalid_ips:
        response = client.post(
            "/login",
            data={
                "password": "incorrect-password",
                "csrf_token": csrf_token
            },
            headers={"CF-Connecting-IP": invalid_ip},
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"}
        )

        assert response.status_code == 401

    # All five attempts should have used the same fallback IP.
    response = client.post(
        "/login",
        data={
            "password": "test-password",
            "csrf_token": csrf_token
        },
        headers={"CF-Connecting-IP": "still-invalid"},
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"}
    )

    assert response.status_code == 429

def test_admin_edit_save_stays_on_edit_page(client):
    created = database.create_service("Original Service")

    login_as_admin(client)

    edit_url = f"/admin/services/{created['id']}/edit"
    edit_page = client.get(edit_url)

    response = client.post(
        edit_url,
        data={
            "csrf_token": extract_csrf_token(edit_page),
            "name": "Updated Service"
        }
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(edit_url)

    saved_page = client.get(edit_url)

    assert saved_page.status_code == 200
    assert b"Changes saved successfully." in saved_page.data
    assert database.get_service(created["id"])["name"] == "Updated Service"

    # Flash messages should only appear once.
    second_visit = client.get(edit_url)

    assert b"Changes saved successfully." not in second_visit.data

def test_admin_edit_previous_next_navigation(client):
    first = database.create_service("First Service")
    removed = database.create_service("Removed Service")
    middle = database.create_service("Middle Service")
    last = database.create_service("Last Service")

    database.delete_service(removed["id"])

    login_as_admin(client)

    middle_page = client.get(
        f"/admin/services/{middle['id']}/edit"
    ).get_data(as_text=True)

    assert f'/admin/services/{first["id"]}/edit' in middle_page
    assert f'/admin/services/{last["id"]}/edit' in middle_page

    # Deleted IDs must be skipped.
    assert f'/admin/services/{removed["id"]}/edit' not in middle_page

    first_page = client.get(
        f"/admin/services/{first['id']}/edit"
    ).get_data(as_text=True)

    assert "Previous" not in first_page

    last_page = client.get(
        f"/admin/services/{last['id']}/edit"
    ).get_data(as_text=True)

    assert "Next" not in last_page

def test_admin_displays_project_url(client):
    database.create_service(
        "ServiceBoard",
        project_url="https://github.com/JoyfulReaper/ServiceBoard",
        is_public=False
    )

    login_as_admin(client)

    response = client.get("/admin")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'href="https://github.com/JoyfulReaper/ServiceBoard"' in html
    assert 'rel="noopener noreferrer"' in html


def test_login_page_uses_shared_layout(client):
    response = client.get("/login")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "style.css" in html
    assert 'class="login-panel"' in html
    assert 'name="password"' in html
    assert 'name="csrf_token"' in html