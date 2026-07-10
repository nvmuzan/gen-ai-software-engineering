# Test Report — Bug Set 001

**Agent:** Unit Test Generator (claude-sonnet-4-6)
**Date:** 2026-06-22
**Skill applied:** `skills/unit-tests-FIRST.md`
**Input:** `context/bugs/001/fix-summary.md`

---

## Test Files Created

| File | Lines | Description |
|------|-------|-------------|
| `tests/test_budget.py` | 88 | pytest unit tests for 3 changed functions |

---

## FIRST Compliance

| Principle | Status | Evidence |
|-----------|--------|---------|
| **F**ast | ✓ | 8 tests completed in 0.02s total; in-memory SQLite, no I/O |
| **I**ndependent | ✓ | Each test using `db` fixture gets a fresh shared in-memory DB via `yield` + `conn.close()`; calculator tests use no shared state |
| **R**epeatable | ✓ | No random data, no real filesystem access, no env-specific paths; `file:testdb_hw4?mode=memory&cache=shared` is deterministic |
| **S**elf-validating | ✓ | All 8 tests contain explicit `assert` statements; pytest reports PASS/FAIL with no manual inspection |
| **T**imely | ✓ | Tests cover only 3 functions changed by Bug Fixer: `average_spending`, `calculate_balance`, `search_transactions` |

**Note on fixture design:** `storage.py` closes each connection after use (`conn.close()`). A simple `lambda: conn` fixture fails on the second call. Used SQLite shared-cache URI (`file:name?mode=memory&cache=shared&uri=true`) so `get_connection()` returns a fresh connection object each time while the DB persists as long as the fixture's `yield conn` is alive.

---

## Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.3, pluggy-1.6.0
collected 8 items

tests/test_budget.py::test_average_spending_empty_list PASSED            [ 12%]
tests/test_budget.py::test_average_spending_single_transaction PASSED    [ 25%]
tests/test_budget.py::test_average_spending_multiple_transactions PASSED [ 37%]
tests/test_budget.py::test_calculate_balance_empty_list PASSED           [ 50%]
tests/test_budget.py::test_calculate_balance_single_transaction PASSED   [ 62%]
tests/test_budget.py::test_calculate_balance_counts_first_transaction PASSED [ 75%]
tests/test_budget.py::test_search_transactions_normal PASSED             [ 87%]
tests/test_budget.py::test_search_transactions_sql_injection_blocked PASSED [100%]

============================== 8 passed in 0.02s ==============================
```

---

## Coverage

| Function Changed | Tests Written | Status |
|-----------------|---------------|--------|
| `calculator.average_spending` (BUG-001) | 3 | ✓ covered |
| `calculator.calculate_balance` (BUG-002) | 3 | ✓ covered |
| `storage.search_transactions` (SEC-001) | 2 | ✓ covered |
| **Total** | **8** | **100% of changed functions** |
