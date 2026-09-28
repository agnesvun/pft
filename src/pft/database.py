import sqlite3


def get_connection():
    conn = sqlite3.connect("pft.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount_in_cents INTEGER NOT NULL,
                category TEXT
            );
        """)
