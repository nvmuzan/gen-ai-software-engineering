# Codebase Research — Budget Tracker CLI (Bug Set 001)

**Researcher:** Bug Researcher Agent
**Date:** 2026-06-22
**App:** `src/budget.py` (entry), `src/storage.py` (data), `src/calculator.py` (logic)

---

## BUG-001: ZeroDivisionError in average_spending

**File:** `src/calculator.py:9`
**Function:** `average_spending`

**Snippet:**
```python
def average_spending(transactions):
    """Calculate average transaction amount. BUG-001: division by zero."""
    total = sum(t[1] for t in transactions)
    return total / len(transactions)  # BUG-001: ZeroDivisionError when empty
```

**Analysis:** When `transactions` is empty, `sum([])` returns 0 but `len([])` returns 0,
causing `ZeroDivisionError`. No guard before division.

**Impact:** `summary` command crashes on fresh install with no transaction data.

---

## BUG-002: Off-by-one in calculate_balance

**File:** `src/calculator.py:4`
**Function:** `calculate_balance`

**Snippet:**
```python
def calculate_balance(transactions):
    """Calculate total balance. BUG-002: skips first transaction."""
    total = 0.0
    for t in transactions[1:]:  # BUG-002: off-by-one, skips transactions[0]
        total += t[1]
    return total
```

**Analysis:** The slice `transactions[1:]` unconditionally skips the first element.
For N transactions, only N-1 are counted.

**Impact:** Balance is always understated by the first transaction's amount.

---

## SEC-001: SQL Injection in search_transactions

**File:** `src/storage.py:32`
**Function:** `search_transactions`

**Snippet:**
```python
def search_transactions(keyword):
    """SEC-001: SQL injection — keyword interpolated directly into query."""
    conn = get_connection()
    query = (
        f"SELECT id, amount, category, description, created_at "
        f"FROM transactions WHERE description LIKE '%{keyword}%'"
    )
    cursor = conn.execute(query)
```

**Analysis:** The `keyword` argument is interpolated directly into the SQL string via
f-string. An attacker can inject: `' OR '1'='1` returns all rows.

**Recommendation:** Use parameterized query: `conn.execute("... LIKE ?", (f"%{keyword}%",))`

---

## Entry Point

**File:** `src/budget.py:1`

App initializes DB on start, routes commands via dict. No known bugs in routing logic.
