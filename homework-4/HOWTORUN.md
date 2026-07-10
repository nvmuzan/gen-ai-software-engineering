# ▶️ How to Run — Homework 4: 4-Agent Pipeline

## Prerequisites

- Python 3.10+
- pytest: `pip install pytest`
- Claude Code CLI (for pipeline): `npm install -g @anthropic-ai/claude-code`
- Anthropic API key (for pipeline): `export ANTHROPIC_API_KEY=your_key_here`

---

## Run the Tests

```bash
cd homework-4
python3 -m pytest tests/ -v
```

Expected output:
```
collected 8 items

tests/test_budget.py::test_average_spending_empty_list PASSED
tests/test_budget.py::test_average_spending_single_transaction PASSED
tests/test_budget.py::test_average_spending_multiple_transactions PASSED
tests/test_budget.py::test_calculate_balance_empty_list PASSED
tests/test_budget.py::test_calculate_balance_single_transaction PASSED
tests/test_budget.py::test_calculate_balance_counts_first_transaction PASSED
tests/test_budget.py::test_search_transactions_normal PASSED
tests/test_budget.py::test_search_transactions_sql_injection_blocked PASSED

8 passed in 0.02s
```

---

## Run the Budget Tracker App

```bash
cd homework-4

# Add transactions
python3 src/budget.py add 50.00 food "lunch at cafe"
python3 src/budget.py add 120.00 transport "metro pass"
python3 src/budget.py add -30.00 misc "refund"

# List all transactions
python3 src/budget.py list

# Search by keyword
python3 src/budget.py search "cafe"

# Summary (balance + average + by category)
python3 src/budget.py summary
```

---

## Run the Full 4-Agent Pipeline

```bash
cd homework-4
bash run-pipeline.sh
```

The pipeline invokes 4 agents sequentially via `claude -p`:

| Step | Agent | Model | Reads | Writes |
|------|-------|-------|-------|--------|
| 1 | Research Verifier | `claude-opus-4-8` | `codebase-research.md` + `src/` | `verified-research.md` |
| 2 | Bug Fixer | `claude-sonnet-4-6` | `implementation-plan.md` | fixed `src/` + `fix-summary.md` |
| 3 | Security Verifier | `claude-opus-4-8` | `fix-summary.md` + changed `src/` | `security-report.md` |
| 4 | Unit Test Generator | `claude-sonnet-4-6` | `fix-summary.md` + changed `src/` | `tests/test_budget.py` + `test-report.md` |

After all agents complete, the pipeline runs `python3 -m pytest tests/ -v` automatically.

---

## Review Pipeline Artifacts

After running the pipeline:

```bash
# Research verification result
cat context/bugs/001/research/verified-research.md

# What was fixed
cat context/bugs/001/fix-summary.md

# Security scan result
cat context/bugs/001/security-report.md

# Test report
cat context/bugs/001/test-report.md
```

---

## Clean Up

```bash
rm -f homework-4/budget.db
```
