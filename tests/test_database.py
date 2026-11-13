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