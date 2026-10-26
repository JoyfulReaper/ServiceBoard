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

