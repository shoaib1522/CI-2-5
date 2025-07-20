# app/database.py

import sqlite3
import os

DB_FILE = "production.db"

def get_db_connection():
    """Creates and returns a connection to the SQLite database."""
    # check_same_thread=False is needed for SQLite to work with FastAPI's async nature.
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db(conn: sqlite3.Connection):
    """Initializes the database table if it doesn't exist."""
    cursor = conn.cursor()
    # A simple users table to store credentials.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()

def clear_db():
    """A helper function to delete the database file for clean testing."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)