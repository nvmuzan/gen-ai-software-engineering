# Bug Context — Budget Tracker CLI (Bug Set 001)

## App Under Test

`src/budget.py` — CLI budget tracker using SQLite. Commands: add, list, search, summary.

## Seeded Defects

### BUG-001: ZeroDivisionError in average_spending
- **File**: `src/calculator.py`
- **Function**: `average_spending(transactions)`
- **Line**: 12
- **Symptom**: `python3 src/budget.py summary` on empty database raises `ZeroDivisionError: division by zero`
- **Root cause**: No guard for empty list before `total / len(transactions)`

### BUG-002: Off-by-one in calculate_balance
- **File**: `src/calculator.py`
- **Function**: `calculate_balance(transactions)`
- **Line**: 4
- **Symptom**: Balance is always wrong; the first transaction is never counted
- **Root cause**: `for t in transactions[1:]` skips `transactions[0]`

## Seeded Security Issue

### SEC-001: SQL Injection in search_transactions
- **File**: `src/storage.py`
- **Function**: `search_transactions(keyword)`
- **Line**: 49
- **Symptom**: `python3 src/budget.py search "' OR '1'='1' --"` returns all rows regardless of keyword
- **Root cause**: f-string interpolation in SQL instead of parameterized query
