# Implementation Plan — Bug Set 001

**Planner:** Bug Planner Agent
**Date:** 2026-06-22
**Input:** `context/bugs/001/research/verified-research.md`

---

## Change 1: Fix BUG-001 — ZeroDivisionError in average_spending

**File:** `src/calculator.py`
**Function:** `average_spending`

**Before:**
```python
def average_spending(transactions):
    """Calculate average transaction amount. BUG-001: division by zero."""
    total = sum(t[1] for t in transactions)
    return total / len(transactions)  # BUG-001: ZeroDivisionError when empty
```

**After:**
```python
def average_spending(transactions):
    """Calculate average transaction amount."""
    if not transactions:
        return 0.0
    total = sum(t[1] for t in transactions)
    return total / len(transactions)
```

**Test command after change:** `python3 -m pytest tests/ -v -k "test_average"`

---

## Change 2: Fix BUG-002 — Off-by-one in calculate_balance

**File:** `src/calculator.py`
**Function:** `calculate_balance`

**Before:**
```python
def calculate_balance(transactions):
    """Calculate total balance. BUG-002: skips first transaction."""
    total = 0.0
    for t in transactions[1:]:  # BUG-002: off-by-one, skips transactions[0]
        total += t[1]
    return total
```

**After:**
```python
def calculate_balance(transactions):
    """Calculate total balance."""
    total = 0.0
    for t in transactions:
        total += t[1]
    return total
```

**Test command after change:** `python3 -m pytest tests/ -v -k "test_balance"`

---

## Change 3: Fix SEC-001 — SQL Injection in search_transactions

**File:** `src/storage.py`
**Function:** `search_transactions`

**Before:**
```python
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
```

**After:**
```python
def search_transactions(keyword):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, amount, category, description, created_at "
        "FROM transactions WHERE description LIKE ?",
        (f"%{keyword}%",)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
```

**Test command after change:** `python3 -m pytest tests/ -v`

---

## Overall Test Command

```bash
python3 -m pytest tests/ -v
```

Expected: All tests pass.
