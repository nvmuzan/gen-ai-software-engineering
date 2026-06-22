import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "budget.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_transaction(amount, category, description):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (amount, category, description) VALUES (?, ?, ?)",
        (amount, category, description)
    )
    conn.commit()
    conn.close()


def get_all_transactions():
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, amount, category, description, created_at FROM transactions"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_transactions(keyword):
    """SEC-001: SQL injection — keyword interpolated directly into query."""
    conn = get_connection()
    query = (
        f"SELECT id, amount, category, description, created_at "
        f"FROM transactions WHERE description LIKE '%{keyword}%'"
    )
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows
