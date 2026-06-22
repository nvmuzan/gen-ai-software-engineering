import sqlite3
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import storage
import calculator


@pytest.fixture
def db(monkeypatch):
    """Shared in-memory SQLite DB — satisfies FIRST: Fast, Independent, Repeatable.

    Uses cache=shared URI so each get_connection() call returns a fresh connection
    object to the same underlying DB, surviving storage.py's conn.close() calls.
    The fixture holds one connection open to keep the DB alive for the test duration.
    """
    db_uri = "file:testdb_hw4?mode=memory&cache=shared&uri=true"
    conn = sqlite3.connect(db_uri, uri=True)
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    monkeypatch.setattr(storage, "get_connection",
                        lambda: sqlite3.connect(db_uri, uri=True))
    yield conn
    conn.close()


# --- calculator.average_spending (BUG-001 fix) ---

def test_average_spending_empty_list():
    """BUG-001 fix: empty list must return 0.0, not raise ZeroDivisionError."""
    assert calculator.average_spending([]) == 0.0


def test_average_spending_single_transaction():
    assert calculator.average_spending([(0, 50.0, 'food', 'lunch', '')]) == 50.0


def test_average_spending_multiple_transactions():
    txns = [(0, 10.0, 'a', 'b', ''), (0, 20.0, 'c', 'd', '')]
    assert calculator.average_spending(txns) == 15.0


# --- calculator.calculate_balance (BUG-002 fix) ---

def test_calculate_balance_empty_list():
    assert calculator.calculate_balance([]) == 0.0


def test_calculate_balance_single_transaction():
    """BUG-002 fix: single transaction must not be skipped."""
    assert calculator.calculate_balance([(0, 100.0, 'food', 'lunch', '')]) == 100.0


def test_calculate_balance_counts_first_transaction():
    """BUG-002 fix: first transaction must be included in total."""
    txns = [(0, 30.0, 'a', 'b', ''), (0, 70.0, 'c', 'd', '')]
    assert calculator.calculate_balance(txns) == 100.0


# --- storage.search_transactions (SEC-001 fix) ---

def test_search_transactions_normal(db):
    """Normal keyword search returns matching rows."""
    storage.add_transaction(50.0, 'food', 'lunch at cafe')
    storage.add_transaction(20.0, 'transport', 'metro pass')
    results = storage.search_transactions('cafe')
    assert len(results) == 1
    assert results[0][3] == 'lunch at cafe'


def test_search_transactions_sql_injection_blocked(db):
    """SEC-001 fix: SQL injection attempt must not return all rows."""
    storage.add_transaction(50.0, 'food', 'lunch at cafe')
    storage.add_transaction(20.0, 'transport', 'metro pass')
    # Before fix, this returned all rows; after fix, returns 0 (literal match)
    results = storage.search_transactions("' OR '1'='1")
    assert len(results) == 0
