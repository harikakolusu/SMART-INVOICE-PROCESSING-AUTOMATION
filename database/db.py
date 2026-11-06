
import sqlite3
from pathlib import Path

# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Database file location
DB_PATH = BASE_DIR / "data" / "invoice_automation.db"

# SQL schema file location
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection():
    """Create a connection to SQLite database."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    # Enable foreign key validation
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """Create all database tables."""

    connection = get_connection()

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)

        print("Database created successfully!")

    finally:
        connection.close()


def check_tables():
    """Display all created database tables."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    tables = cursor.fetchall()

    print("\nDatabase Tables:")

    for table in tables:
        print("-", table[0])

    print("\nTotal tables created:", len(tables))

    connection.close()


if __name__ == "__main__":

    initialize_database()

    check_tables()
