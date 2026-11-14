import pytest
import sqlite3
from contextlib import closing
from src.serviceboard import database

@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    database.initialize_database()

def test_create_service(isolated_database):
    created = database.create_service(
        "Test service",
        "https://example.com",
        "FrontDesk",
        "Microsoft.AspNetCore.App",
        "10.0.15"
    )

    assert created["id"] > 0
    retrieved = database.get_service(created["id"])
    assert retrieved == created

def test_update_service(isolated_database):
    created = database.create_service(
        "Test Service",
        "https://example.com"
    )

    updated = database.update_service(
        created["id"],
        "Updated Service",
        "https://updated.example.com",
        "DeepDish",
        "Microsoft.AspNetCore.App",
        "10.0.15"
    )

    assert updated["id"] == created["id"]
    assert updated["name"] == "Updated Service"
    assert updated["url"] == "https://updated.example.com"
    assert updated["host"] == "DeepDish"
    assert updated["runtime_name"] == "Microsoft.AspNetCore.App"
    assert updated["runtime_version"] == "10.0.15"

    retrieved = database.get_service(created["id"])

    assert retrieved == updated

def test_delete_service(isolated_database):
    created = database.create_service(
        "Delete Test",
        "https://example.com"
    )

    service_id = created["id"]

    deleted = database.delete_service(service_id)

    assert deleted is True
    assert database.get_service(service_id) is None
    assert database.get_services() == []

def test_nonexistent_service(isolated_database):
    service_id = 99999

    assert database.get_service(service_id) is None

    updated = database.update_service(
        service_id,
        "Does Not Exist",
        "https://example.com"
    )

    assert updated is None

    deleted = database.delete_service(service_id)

    assert deleted is False

def test_database_migration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with closing(sqlite3.connect("data.db")) as connection:
        connection.execute("""
            CREATE TABLE services (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL
            )
        """)

        connection.execute(
            "INSERT INTO services (name, url) VALUES (?, ?)",
            ("Old Service", "https://example.com")
        )

        connection.commit()

    database.initialize_database()

    services = database.get_services()

    assert len(services) == 1

    service = services[0]

    assert service["name"] == "Old Service"
    assert service["url"] == "https://example.com"
    assert service["host"] is None
    assert service["runtime_name"] is None
    assert service["runtime_version"] is None

def test_database_initialization_preserves_data(isolated_database):
    created = database.create_service(
        "Persistent Service",
        "https://example.com",
        "Clanker",
        "Microsoft.AspNetCore.App",
        "10.0.15"
    )

    database.initialize_database()

    retrieved = database.get_service(created["id"])

    assert retrieved == created

def test_configured_database_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    custom_database = tmp_path / "custom.db"
    custom_database.touch()

    monkeypatch.setenv(
        "SERVICEBOARD_DATABASE_PATH",
        str(custom_database)
    )

    database.initialize_database()

    created = database.create_service(
        "Configured Service",
        "https://example.com"
    )

    assert database.get_service(created["id"]) == created
    assert custom_database.is_file()
    assert not (tmp_path / "data.db").exists()

def test_configured_database_path_must_exist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    missing_database = tmp_path / "missing.db"

    monkeypatch.setenv(
        "SERVICEBOARD_DATABASE_PATH",
        str(missing_database)
    )

    with pytest.raises(FileNotFoundError):
        database.initialize_database()

    assert not missing_database.exists()
    assert not (tmp_path / "data.db").exists()

def test_deployment_type_create_and_update(isolated_database):
    created = database.create_service(
        "Deployment Test",
        "https://example.com",
        deployment_type="docker"
    )

    assert created["deployment_type"] == "docker"

    retrieved = database.get_service(created["id"])

    assert retrieved["deployment_type"] == "docker"

    updated = database.update_service(
        created["id"],
        "Deployment Test",
        "https://example.com",
        deployment_type="systemd"
    )

    assert updated["deployment_type"] == "systemd"

    retrieved = database.get_service(created["id"])

    assert retrieved["deployment_type"] == "systemd"

def test_service_description(isolated_database):
    created = database.create_service(
        "SmolSearch",
        "https://example.com",
        description="A search engine for the small web"
    )

    assert created["description"] == "A search engine for the small web"

    retrieved = database.get_service(created["id"])

    assert retrieved["description"] == "A search engine for the small web"

    database.update_service(
        created["id"],
        "SmolSearch",
        "https://example.com",
        description="Searches Gemini and Gopher content"
    )

    updated = database.get_service(created["id"])

    assert updated["description"] == "Searches Gemini and Gopher content"