---
name: unit-tests-FIRST
description: FIRST principles for unit tests. Used by Unit Test Generator to ensure all generated tests meet quality standards.
---

# Unit Tests — FIRST Principles

Apply every principle to every test. Reference this skill in `test-report.md` to confirm compliance.

## The FIRST Principles

| Principle | Requirement | Enforcement |
|-----------|-------------|-------------|
| **F**ast | Each test completes in < 100ms | Use in-memory SQLite (`:memory:`), no network I/O, no filesystem I/O |
| **I**ndependent | Tests do not share state; can run in any order | Use pytest fixtures to create a fresh DB per test |
| **R**epeatable | Same result on every run, in any environment | No random data, no time-dependent assertions, no env-specific paths |
| **S**elf-validating | Each test asserts a clear pass/fail | Every test has at least one `assert`; no print-only tests |
| **T**imely | Tests cover only code changed in the current fix | Do not add tests for functions not listed in `fix-summary.md` |

## In-Memory SQLite Fixture Pattern

For tests that exercise `storage.py`, monkeypatch `get_connection` to return an in-memory connection:

```python
import sqlite3
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import storage
import calculator


@pytest.fixture
def db(monkeypatch):
    conn = sqlite3.connect(":memory:")
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
    monkeypatch.setattr(storage, "get_connection", lambda: conn)
    return conn
```

## FIRST Self-Check Before Writing test-report.md

- [ ] No test takes > 100ms (Fast)
- [ ] Each test creates its own DB via fixture, no shared state (Independent)
- [ ] No test reads from real filesystem or real `budget.db` (Repeatable)
- [ ] Every test has at least one `assert` statement (Self-validating)
- [ ] Only `average_spending`, `calculate_balance`, `search_transactions` have new tests (Timely)
