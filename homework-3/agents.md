# Virtual Card Service — Agent Guidelines

## Project Context

This is a PCI DSS– and GDPR-regulated virtual card lifecycle service. The domain is payment card management: issuance, state transitions (PENDING → ACTIVE → FROZEN → TERMINATED), spending controls, and transaction visibility.

All code generated for this project must treat **compliance, security, and auditability as first-class constraints** — not afterthoughts. When in doubt between a convenient shortcut and the compliant path, always take the compliant path and document why.

---

## Tech Stack Assumptions

- **Language:** Python 3.11+ or TypeScript (Node 20+); confirm with the existing codebase before choosing
- **Database:** PostgreSQL 15+; use parameterized queries or ORM exclusively — no string interpolation in SQL
- **Cache:** Redis for idempotency keys and auth-state propagation
- **Auth:** JWT validation middleware; MFA via TOTP for destructive operations (terminate, replace)
- **Money:** All monetary values as integers in minor units (e.g. cents); never `float` or `double`
- **IDs:** UUID v4 for all entity identifiers; card PAN is never used as an identifier in internal systems
- **Migrations:** Include a rollback section in every migration script

---

## Domain Rules (Never Violate)

1. **Never log PAN.** No 16-digit card number may appear in any log statement, error message, stack trace, or API response body. If you need to reference a card in a log, use `masked_pan` (format `****-****-****-XXXX`) or `card_id` only.

2. **Always prefer idempotent writes.** Every mutating function must process the `Idempotency-Key` before executing. Duplicate execution of a state transition is a compliance risk — it creates phantom audit events and inconsistent state.

3. **Audit every state transition.** Every function that changes `cards.status` must call the `audit_event_writer` module within the **same database transaction**. There is no exception to this rule. If the audit write fails, the entire operation must roll back.

4. **State transitions are server-side only.** The client sends an intent (e.g. `action: "freeze"`). The server validates current state and applies the transition. Never trust client-supplied target state. Never skip the state validation step for convenience.

5. **Optimistic locking on all card writes.** Every `UPDATE` on the `cards` table must include `WHERE version = :current_version`. A stale version must return HTTP 409 `CONCURRENT_MODIFICATION`, not silently overwrite.

6. **Money arithmetic uses integer types only.** Never introduce floating-point calculations for amounts. Use integer arithmetic or a `Decimal`-equivalent library where division is necessary. Round toward zero on splits.

7. **MFA required for destructive operations.** `TERMINATE_CARD` and `REPLACE_CARD` require a valid MFA token in the request header. Never generate code that bypasses this check in any mode, including test or debug modes.

---

## Code Style

- Functions that touch card state must have a **single responsibility**: one state transition per function
- Error returns must include `error_code` (machine-readable snake_case string), `user_message` (human-readable, safe to display), and `trace_id`
- No bare `except Exception` or `catch (e)` blocks that swallow errors silently
- All database queries: ORM or parameterized queries only; never `f"SELECT ... WHERE id={id}"` or template strings in SQL
- No global mutable state for card status; always read from DB with version check before writing
- Test data must use obviously-fake PANs (e.g. `4111111111111111`) and be labeled clearly as test data

---

## Testing and Verification Expectations

- Every new function touching card state must have:
  - A unit test for the happy path
  - At least two unit tests for failure modes (invalid state, concurrent modification, missing idempotency key)
- Integration tests must use a real database connection, not a mocked DB. Mocking the database masks transaction-atomicity bugs — exactly the class of bug that causes compliance incidents.
- After writing any code that produces log output involving card data, run: `grep -E '[0-9]{16}' <logfile>` and assert 0 matches.
- State transition tests must verify **all three** of: `status` field changed, `version` incremented, audit event written. Verifying only `status` is insufficient.

---

## Security Constraints

- Never generate code that stores raw PAN beyond the scope of the tokenization call
- Never generate code that logs request bodies containing card fields without first scrubbing PAN
- Never add a `DEBUG`, `DEV`, or `BYPASS_AUTH` mode that disables JWT validation, MFA checks, or the idempotency middleware
- All new API endpoints must be covered by the authentication middleware. There are no unprotected routes in this service.
- Never expose `pan_token` in API responses. Only `masked_pan` is safe to return.

---

## How the Agent Should Treat Edge Cases

- **Unexpected card state:** Return `INVALID_STATE_TRANSITION` with the current and attempted states in the error body. Never silently coerce, ignore, or log-and-continue.
- **Tokenizer unavailable:** Fail the entire `CREATE_CARD` operation. Never create a card record without a `pan_token`. The partial-state scenario is a compliance failure.
- **Audit write failure:** Roll back the parent transaction. A committed state change without an audit event is a PCI DSS violation. Log the audit failure at ERROR level and alert.
- **GDPR erasure with legal hold:** Log the block with `reason` and `card_id`. Notify the user via the notification service. Never silently skip the request or mark it as completed.
- **Concurrent modification:** Surface HTTP 409 to the caller with `CONCURRENT_MODIFICATION`. Do not retry silently on the server side. The caller is responsible for re-reading state and retrying with a new version.
- **Missing idempotency key:** Return HTTP 400 `MISSING_IDEMPOTENCY_KEY` immediately, before any handler logic executes.

---

## Sensitive Data Classification

| Field | Classification | Handling |
|-------|---------------|---------|
| `pan_token` | Confidential — PCI | Store in DB; never log; never return in API response |
| `masked_pan` | Safe for display | Log-safe; return in API responses |
| `cvv` | Confidential — PCI | Never persist; discard after issuance response |
| `source_ip` | PII — GDPR | Store in audit log; nullify on GDPR erasure |
| `actor_id` | Audit field | Retain 7 years; not subject to GDPR erasure (legal obligation) |
| `amount_minor_units` | Financial | Retain 7 years; not subject to erasure |
| `user_id` reference | PII — GDPR | Nullify on GDPR erasure; `card_id` is retained |

---

## Error Code Reference

All error codes the agent may generate must come from this list or follow the same naming convention. New codes must be added here when introduced.

| Error Code | HTTP Status | Meaning |
|------------|-------------|---------|
| `INVALID_STATE_TRANSITION` | 422 | Attempted transition not in the valid state machine |
| `CONCURRENT_MODIFICATION` | 409 | Optimistic lock failed; version mismatch |
| `ALREADY_FROZEN` | 409 | Freeze attempted on already-FROZEN card |
| `CARD_FROZEN` | 422 | Operation rejected because card is FROZEN |
| `CARD_TERMINATED` | 422 | Operation rejected because card is TERMINATED |
| `CARD_NOT_ACTIVE` | 422 | Operation requires ACTIVE card |
| `MAX_CARDS_REACHED` | 422 | Account already has maximum allowed cards (5) |
| `LIMIT_EXCEEDED` | 422 | Transaction exceeds configured spending limit |
| `LIMIT_OUT_OF_RANGE` | 422 | Limit value outside allowed range |
| `INVALID_LIMIT_VALUE` | 422 | Limit value is invalid (e.g. zero) |
| `MCC_BLOCKED` | 422 | Merchant category code is blocked for this card |
| `INVALID_MCC` | 422 | MCC code format is invalid |
| `MISSING_IDEMPOTENCY_KEY` | 400 | Required `Idempotency-Key` header is absent |
| `IDEMPOTENCY_KEY_CONFLICT` | 422 | Same key reused with a different request payload |
| `MFA_REQUIRED` | 403 | Destructive operation requires MFA confirmation |
| `FORBIDDEN` | 403 | Actor does not have permission to access this resource |
| `ERASURE_BLOCKED_LEGAL_HOLD` | 422 | GDPR erasure blocked by active legal hold |
