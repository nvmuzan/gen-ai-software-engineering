# Security Report — Bug Set 001 (Post-Fix)

**Agent:** Security Verifier (claude-opus-4-8)
**Date:** 2026-06-22
**Input:** `context/bugs/001/fix-summary.md`
**Changed files scanned:** `src/calculator.py`, `src/storage.py`
**Unchanged files reviewed:** `src/budget.py`

---

## Executive Summary

After the Bug Fixer applied all 3 changes, the critical SQL injection vulnerability (SEC-001) has been **fully remediated**. All SQL operations in `src/storage.py` now use parameterized queries. Two low-severity findings remain in unchanged code paths: missing numeric range validation on the `amount` field and unhandled `ValueError` on non-numeric CLI input. No hardcoded secrets, no command injection, and no path traversal were found. Overall security posture: **1 CRITICAL resolved, 2 LOW remain**.

Findings by severity: CRITICAL 0 (was 1, resolved), HIGH 0, MEDIUM 0, LOW 2, INFO 1.

---

## Findings

**[RESOLVED] SEC-001: SQL Injection in search_transactions**
- File: `src/storage.py:46-55`
- Status: **FIXED** — f-string interpolation replaced with parameterized query `conn.execute("... LIKE ?", (f"%{keyword}%",))`
- Verification: `search("' OR '1'='1")` now performs literal LIKE match, returns no results

---

**[LOW] FINDING-1: No amount validation — negative values accepted**
- File: `src/storage.py:26-33` (`add_transaction`), `src/budget.py:14`
- Description: `add_transaction` accepts any `float` including negatives and values like `float('inf')`. At the CLI layer, `float(args[0])` converts the input but applies no range check.
- Exploitability: A user can insert `add -999999999 food x` corrupting balance calculations. Not remotely exploitable for a CLI tool but could matter if `add_transaction` is used as a library.
- Remediation: Add validation in `add_transaction`: `if not isinstance(amount, (int, float)) or amount == float('inf'): raise ValueError(...)`. Or validate at CLI: `if not -1e9 < amount < 1e9: raise ValueError("Amount out of range")`.

---

**[LOW] FINDING-2: Unhandled ValueError on non-numeric amount input**
- File: `src/budget.py:14`
- Description: `amount = float(args[0])` raises `ValueError` with a Python traceback if user provides a non-numeric string (e.g., `add abc food lunch`). The stack trace reveals internal file paths.
- Exploitability: Information disclosure — internal paths visible to CLI user. Not remotely exploitable.
- Remediation:
  ```python
  try:
      amount = float(args[0])
  except ValueError:
      print(f"Error: '{args[0]}' is not a valid amount")
      sys.exit(1)
  ```

---

**[INFO] FINDING-3: SQLite DB at predictable relative path**
- File: `src/storage.py:4`
- Description: `DB_PATH` resolves to `homework-4/budget.db` — adjacent to source. In a deployed context this could be accidentally web-served if behind a file server.
- Exploitability: For a local CLI tool, no risk. Would be MEDIUM if deployed behind a web server.
- Remediation: For production use, store DB in `~/.budget/budget.db` or respect `$XDG_DATA_HOME`.

---

## Unchanged Risk Areas

`src/budget.py` was not modified by the Bug Fixer and is out of scope for this report. FINDING-2 references `budget.py:14` as it interacts with the patched `add_transaction`, but the vulnerability is in the calling code, not the fixed function.

`src/calculator.py` — pure functions with no I/O. No security concerns.

---

## Conclusion

**NEEDS REMEDIATION**

The critical SQL injection (SEC-001) is resolved. The two remaining LOW findings (missing amount validation, unhandled ValueError exposing paths) should be addressed before library or production use. For a homework CLI demo they are acceptable. No blocking issues remain from the perspective of the bug-fix scope.
