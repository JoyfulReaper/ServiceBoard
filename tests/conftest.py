import importlib
import pytest
from werkzeug.security import generate_password_hash
from src.serviceboard import database

@pytest.fixture(autouse=True)
def isolate_database_path_environment(monkeypatch):
    monkeypatch.delenv("SERVICEBOARD_DATABASE_PATH", raising=False)

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv("SERVICEBOARD_API_KEY", "test-api-key")
    monkeypatch.setenv("SERVICEBOARD_SECRET_KEY", "test-session-secret-key")
    monkeypatch.setenv(
        "SERVICEBOARD_ADMIN_PASSWORD_HASH",
        generate_password_hash("test-password")
    )

    app_module = importlib.import_module("src.serviceboard.app")

    database.initialize_database()

    app_module.app.config.update(
        TESTING=True,
        SESSION_COOKIE_SECURE=False
    )

    with app_module.app.test_client() as test_client:
        yield test_client