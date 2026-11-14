import sqlite3
import os
from pathlib import Path
from contextlib import closing

def database_path():
    configured = os.environ.get("SERVICEBOARD_DATABASE_PATH")

    if not configured:
        return Path("data.db")

    path = Path(configured)

    if not path.is_absolute():
        raise ValueError("SERVICEBOARD_DATABASE_PATH must be an absolute path")

    if not path.is_file():
        raise FileNotFoundError(f"Configured database does not exist: {path}")

    return path

def initialize_database():
    print("Initializing database...")

    with closing(sqlite3.connect(database_path())) as connection:
        connection.execute("""
           CREATE TABLE IF NOT EXISTS services
           (
               id              INTEGER PRIMARY KEY,
               name            TEXT NOT NULL,
               url             TEXT NOT NULL,
               host            TEXT,
               deployment_type TEXT,
               runtime_name    TEXT,
               runtime_version TEXT
           )
           """)

        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(services)")
        }

        for column in ("host", "deployment_type", "runtime_name", "runtime_version"):
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE services ADD COLUMN {column} TEXT")

        connection.commit()

def get_services():
    with closing(sqlite3.connect(database_path())) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("""
            SELECT id, name, url, host, deployment_type, runtime_name, runtime_version
            FROM services
                                    """)
        rows = cursor.fetchall()

        services = [dict(row) for row in rows]
        return services

def get_service(service_id):
    with closing(sqlite3.connect(database_path())) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("""
            SELECT id, name, url, host, deployment_type, runtime_name, runtime_version 
            FROM services WHERE id = ?
                                    """, (service_id,))
        row = cursor.fetchone()
        service = dict(row) if row else None
        return service

def create_service(
        name: str,
        url: str,
        host: str | None = None,
        runtime_name: str | None = None,
        runtime_version: str | None = None,
        deployment_type: str | None = None,
):

    sql = """
          INSERT INTO services (name, url, host, deployment_type, runtime_name, runtime_version)
          VALUES (?, ?, ?, ?, ?, ?)"""
    with closing(sqlite3.connect(database_path())) as connection:
        cursor = connection.execute(sql, (name, url, host, deployment_type, runtime_name, runtime_version))
        service_id = cursor.lastrowid

        service = {
            'id': service_id,
            'name': name,
            'url': url,
            'host': host,
            'deployment_type': deployment_type,
            'runtime_name': runtime_name,
            'runtime_version': runtime_version
        }

        connection.commit()
        return service

def delete_service(service_id):
    deleted = False
    with closing(sqlite3.connect(database_path())) as connection:
        cursor = connection.execute("""DELETE FROM services WHERE id = ?""", (service_id,))
        connection.commit()
        if cursor.rowcount == 1:
            deleted = True
        elif cursor.rowcount > 1:
            # Note: It should not be possible for the delete to affect multiple rows
            # for this Query
            raise ValueError("Affected multiple rows!")

    return deleted

def update_service(service_id: int,
                   name: str,
                   url: str,
                   host: str | None = None,
                   runtime_name: str | None = None,
                   runtime_version: str | None = None,
                   deployment_type: str | None = None):

    sql = """
        UPDATE services SET name = ?, url = ?, host = ?, deployment_type = ?, runtime_name = ?, runtime_version = ?
        WHERE id = ?
    """

    with closing(sqlite3.connect(database_path())) as connection:
        cursor = connection.execute(sql,
                                    (name, url, host, deployment_type, runtime_name, runtime_version, service_id))
        connection.commit()

        if cursor.rowcount == 0:
            return None

    return get_service(service_id)