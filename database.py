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

