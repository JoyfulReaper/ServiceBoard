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
        try:
            connection.execute("""
               CREATE TABLE IF NOT EXISTS services
               (
                   id              INTEGER PRIMARY KEY,
                   name            TEXT NOT NULL,
                   url             TEXT,
                   project_url     TEXT,
                   description     TEXT,
                   host            TEXT,
                   deployment_type TEXT,
                   runtime_name    TEXT,
                   runtime_version TEXT,
                   is_public       INTEGER NOT NULL DEFAULT 1
               )
               """)

            existing_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(services)")
            }

            for column in ("description", "host", "deployment_type", "runtime_name", "runtime_version", "project_url"):
                if column not in existing_columns:
                    connection.execute(f"ALTER TABLE services ADD COLUMN {column} TEXT")

            if "is_public" not in existing_columns:
                connection.execute(
                    "ALTER TABLE services ADD COLUMN is_public INTEGER NOT NULL DEFAULT 1"
                )

            columns = {
                row[1]: row
                for row in connection.execute("PRAGMA table_info(services)")
            }

            if columns["url"][3] == 1:
                connection.execute("""
                                   CREATE TABLE services_new
                                   (
                                       id              INTEGER PRIMARY KEY,
                                       name            TEXT    NOT NULL,
                                       url             TEXT,
                                       project_url     TEXT,
                                       description     TEXT,
                                       host            TEXT,
                                       deployment_type TEXT,
                                       runtime_name    TEXT,
                                       runtime_version TEXT,
                                       is_public       INTEGER NOT NULL DEFAULT 0
                                   )
                                   """)

                connection.execute("""
                                   INSERT INTO services_new (id, name, url, project_url, description, host,
                                                             deployment_type, runtime_name, runtime_version, is_public)
                                   SELECT id,
                                          name,
                                          url,
                                          project_url,
                                          description,
                                          host,
                                          deployment_type,
                                          runtime_name,
                                          runtime_version,
                                          is_public
                                   FROM services
                                   """)

                connection.execute("DROP TABLE services")
                connection.execute("ALTER TABLE services_new RENAME TO services")
        except Exception:
            connection.rollback()
            raise

        connection.commit()

def get_services():
    with closing(sqlite3.connect(database_path())) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("""
            SELECT id, name, url, project_url, host, deployment_type, runtime_name, runtime_version, description, is_public
            FROM services
                                    """)
        rows = cursor.fetchall()

        services = [dict(row) for row in rows]

        for service in services:
            service["is_public"] = bool(service["is_public"])

        return services

def get_service(service_id):
    with closing(sqlite3.connect(database_path())) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("""
            SELECT id, name, url, project_url, host, deployment_type, runtime_name, runtime_version, description, is_public 
            FROM services WHERE id = ?
                                    """, (service_id,))
        row = cursor.fetchone()
        service = dict(row) if row else None

        if service is not None:
            service["is_public"] = bool(service["is_public"])

        return service

def create_service(
        name: str,
        url: str | None = None,
        host: str | None = None,
        runtime_name: str | None = None,
        runtime_version: str | None = None,
        deployment_type: str | None = None,
        description: str | None = None,
        is_public: bool = False,
        project_url: str | None = None,
):

    sql = """
          INSERT INTO services (name, url, project_url, host, deployment_type, runtime_name, runtime_version, description, is_public)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    with closing(sqlite3.connect(database_path())) as connection:
        cursor = connection.execute(sql, (name, url, project_url, host, deployment_type, runtime_name, runtime_version, description, is_public))
        service_id = cursor.lastrowid

        service = {
            'id': service_id,
            'name': name,
            'url': url,
            'project_url': project_url,
            'host': host,
            'deployment_type': deployment_type,
            'description': description,
            'runtime_name': runtime_name,
            'runtime_version': runtime_version,
            'is_public': is_public
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
                   url: str | None = None,
                   host: str | None = None,
                   runtime_name: str | None = None,
                   runtime_version: str | None = None,
                   deployment_type: str | None = None,
                   description: str | None = None,
                   is_public: bool | None = None,
                   project_url: str | None = None):

    sql = """
        UPDATE services SET name = ?, url = ?, project_url = ?, host = ?, deployment_type = ?, runtime_name = ?, runtime_version = ?, description = ?, is_public = COALESCE(?, is_public)
        WHERE id = ?
    """
    visibility = None if is_public is None else int(is_public)
    with closing(sqlite3.connect(database_path())) as connection:
        cursor = connection.execute(sql,
                                    (name, url, project_url, host, deployment_type, runtime_name, runtime_version, description, visibility, service_id))
        connection.commit()

        if cursor.rowcount == 0:
            return None

    return get_service(service_id)