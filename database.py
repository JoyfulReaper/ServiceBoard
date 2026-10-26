import sqlite3
from contextlib import closing

def initialize_database():
    print("Initializing database...")
    with closing(sqlite3.connect('data.db')) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL)""")

def get_services():
    with closing(sqlite3.connect('data.db')) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("""
            SELECT id, name, url FROM services""")
        rows = cursor.fetchall()

        services = [dict(row) for row in rows]
        return services

def get_service(service_id):
    with closing(sqlite3.connect('data.db')) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("""SELECT id, name, url FROM services WHERE id = ?""", (service_id,))
        row = cursor.fetchone()
        service = dict(row) if row else None
        return service

def create_service(name: str, url: str):
    sql = """INSERT INTO services (name, url) VALUES (?, ?)"""
    with closing(sqlite3.connect('data.db')) as connection:
        cursor = connection.execute(sql, (name, url))
        service_id = cursor.lastrowid

        service = {
            'id': service_id,
            'name': name,
            'url': url
        }

        connection.commit()
        return service