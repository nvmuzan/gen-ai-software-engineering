# Virtual Card Lifecycle Specification

> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.

---

## High-Level Objective

Enable cardholders to create, manage, and terminate virtual payment cards through a secure, auditable lifecycle — reducing fraud exposure while meeting PCI DSS and GDPR obligations for a regulated environment.

**Scope boundary:** This specification covers the virtual card management service only — card issuance, state transitions, spending controls, and transaction visibility. Payment authorization, clearing, and settlement are out of scope (consumed as external services).

---

## Mid-Level Objectives

**MO-1 — Card Issuance:** A cardholder can create a virtual card and receive tokenized PAN and masked display details within 3 seconds; the raw PAN is never persisted or logged.

**MO-2 — State Control:** A cardholder or ops agent can freeze/unfreeze a card; the state change takes effect for all subsequent authorization requests within 500 ms; concurrent modifications are detected and rejected with a structured error.

**MO-3 — Spending Limits:** A cardholder can configure spending limits (daily, per-transaction, MCC-based); limits are enforced synchronously before authorization reaches the payment network.

**MO-4 — Transaction Visibility & Auditability:** A cardholder and ops agent can view paginated transaction history with full audit fields; every state transition is recorded in an immutable audit trail attributable to a specific actor.

**MO-5 — Termination and Replacement:** A card can be permanently terminated or replaced; the terminated card's state is immutable; replacement creates a new card linked to the original via a traceable reference.

---

## Card State Machine

```
                    ┌─────────┐
             ┌─────►│ PENDING │
             │      └────┬────┘
             │           │ activate
             │           ▼
        create      ┌─────────┐
             │      │ ACTIVE  │◄─────────┐
             │      └────┬────┘          │
             │     freeze│          unfreeze
             │           ▼               │
             │      ┌─────────┐          │
             │      │ FROZEN  │──────────┘
             │      └────┬────┘
             │  terminate│  terminate
             │           │   │
             └───────────▼───▼
                    ┌──────────┐
                    │TERMINATED│  (immutable — no outbound transitions)
                    └──────────┘
```

Valid transitions only. Any other transition attempt returns HTTP 422 `INVALID_STATE_TRANSITION`.

---

## Non-Functional & Policy Requirements

### Performance (Assumed Targets)

All values below are labeled as **assumed targets** derived from FinTech UX and regulatory practice — not measured benchmarks.

| Operation | p95 Latency Target | Rationale |
|-----------|-------------------|-----------|
| Card create | < 3 000 ms | Tokenization + DB write in single sync call; industry UX threshold for synchronous issuance |
| Freeze / Unfreeze | < 500 ms | Auth network polls card state; stale window beyond 500 ms is measurable fraud exposure |
| Limit update | < 1 000 ms | Synchronous enforcement; user expects immediate effect |
| Transaction list (one page) | < 500 ms | Standard list UX; max page size 50 records |
| Audit log write | ≤ 200 ms added latency | Must not degrade primary operation; async-durable write acceptable if guaranteed delivery |
| GDPR erasure job completion | < 30 days end-to-end | Regulatory SLA — GDPR Art. 17 |

**Rate limits (assumed):**
- Card create: 3 per user per day
- Freeze/unfreeze: 10 per card per hour
- Limit updates: 20 per card per hour
- All limits enforced at API gateway before reaching service

### Security

- PAN stored only as a PCI DSS–compliant token (HSM-backed tokenizer); raw PAN never written to disk, cache, or logs
- CVV never persisted after card issuance response is delivered
- All card-mutating operations require active session JWT; terminate and replace additionally require MFA confirmation
- mTLS between internal services; all external endpoints TLS 1.2 minimum
- Card details endpoint returns masked PAN (last-4 only) in all contexts
- CI/CD pipeline includes a regex scan for 16-digit sequences in log output; build fails on match (PCI DSS Req. 3.3)

### Privacy (GDPR)

- Right to erasure: PII fields (`user_id` reference, `source_ip`) nullified within 30 days of verified erasure request
- Audit records retained 7 years for regulatory compliance — GDPR Art. 17(3)(e) exception; this conflict is explicitly documented in Task 15
- Data minimization: transaction records store only fields required for dispute resolution and audit; no behavioral profiling fields
- Consent to card issuance and data processing logged at card creation with timestamp and consent version string

### Audit & Compliance

- Every state transition writes an immutable audit event **atomically within the same DB transaction** as the state change:
  `{ event_id, card_id, actor_id, actor_role, from_state, to_state, timestamp_utc, reason, source_ip }`
- Audit log is append-only; no UPDATE or DELETE path exists at the data model or application layer
- Retention minimum: 7 years (PCI DSS Req. 10.7)
- Ops-only audit trail endpoint; end-user sees own card state history only, not internal actor fields

### Reliability

- All mutating endpoints accept a client-supplied `Idempotency-Key` (UUID v4 format); required, not optional
- Duplicate requests within 24 h return cached response without re-execution
- Optimistic locking via `version` integer on card entity; stale-version write returns HTTP 409 `CONCURRENT_MODIFICATION`
- No silent failures: every failed state transition returns `{ error_code, user_message, trace_id }`
- Tokenizer unavailable → card create fails atomically; no partial card record written

---

## Implementation Notes

**Money:** All monetary values in minor units as integers (e.g. `amount_minor_units: 1050` = $10.50). Never `float` or `double` in any arithmetic path.

**IDs:** All entity identifiers are UUID v4. Card PAN is never used as an identifier in any internal system.

**Idempotency:** Every mutating endpoint requires `Idempotency-Key` header (UUID v4). Duplicate requests within 24 h return cached response; re-execution does not happen. Reuse of a key with a different payload returns HTTP 422 `IDEMPOTENCY_KEY_CONFLICT`.

**Error semantics:** 4xx = client error (do not retry); 5xx = server error (retry with exponential backoff). Every error body: `{ error_code, user_message, trace_id }`.

**State transitions:** Enforced server-side only. Client sends intent (e.g. `action: "freeze"`). Server validates current state and applies transition. Client never sends target state directly.

**Concurrent writes:** Optimistic locking via `version` integer on the `cards` table. UPDATE must include `WHERE version = :current_version`. Stale version → HTTP 409 `CONCURRENT_MODIFICATION`.

**PAN handling:** Tokenization is the first operation on card create. Raw PAN exists in memory < 100 ms, never touches disk, cache, or log output.

**Audit writes:** Synchronous within the same DB transaction as the state change. If the audit write fails, the entire operation rolls back. There is no code path that commits a state change without a corresponding audit event.

**Auth network propagation:** After freeze/unfreeze, card state must be reflected in the auth service cache within 500 ms. Mechanism: event published to internal message queue; auth service consumes and updates local cache.

---

## Context

### Beginning Context

- Hypothetical card-service repository with an empty `src/` directory
- PostgreSQL 15+ database with pre-existing `users` and `accounts` tables
- PAN tokenization service available at internal endpoint (external dependency; assumed healthy at service start)
- Authentication service providing JWT validation and MFA confirmation (external dependency)
- Append-only audit database initialized (separate schema from transactional DB)
- Redis cache available for idempotency key storage and auth-state propagation

### Ending Context

After all low-level tasks are complete, the following artifacts exist:

**Database tables:**

```
cards
  id                UUID PK
  account_id        UUID FK → accounts.id
  status            ENUM('PENDING','ACTIVE','FROZEN','TERMINATED')
  pan_token         VARCHAR(64)   -- opaque tokenizer reference; never a real PAN
  masked_pan        VARCHAR(19)   -- format: ****-****-****-XXXX
  version           INTEGER       -- optimistic lock counter
  replaced_by       UUID nullable FK → cards.id
  created_at        TIMESTAMPTZ
  updated_at        TIMESTAMPTZ

card_limits
  id                UUID PK
  card_id           UUID FK → cards.id
  limit_type        ENUM('DAILY','PER_TRANSACTION','MCC')
  amount_minor_units BIGINT nullable  -- null when limit_type = MCC
  currency          CHAR(3)
  mcc_code          VARCHAR(4) nullable
  mcc_action        ENUM('BLOCK','ALLOW') nullable
  updated_by        UUID
  updated_at        TIMESTAMPTZ

card_audit_log
  event_id          UUID PK
  card_id           UUID           -- retained after GDPR erasure
  actor_id          UUID           -- retained after GDPR erasure
  actor_role        ENUM('USER','OPS','SYSTEM')
  from_state        VARCHAR(20) nullable
  to_state          VARCHAR(20)
  timestamp_utc     TIMESTAMPTZ
  reason            TEXT nullable
  source_ip         INET nullable  -- nullified on GDPR erasure

card_transactions
  id                UUID PK
  card_id           UUID FK → cards.id
  amount_minor_units BIGINT
  currency          CHAR(3)
  merchant_name     VARCHAR(100)
  mcc               VARCHAR(4)
  status            ENUM('APPROVED','DECLINED')
  decline_reason    VARCHAR(50) nullable
  created_at        TIMESTAMPTZ

idempotency_cache   (Redis or DB, expires 24 h)
  key               UUID PK
  response_body     JSONB
  created_at        TIMESTAMPTZ
```

**Services / modules:**
- REST API exposing all lifecycle operations documented in Low-Level Tasks
- PAN tokenization wrapper module (zero-PAN-logging guarantee)
- Audit event writer (shared internal module, called by all mutating operations)
- GDPR erasure scheduled job

---

## Edge Cases and Failure Modes

| Scenario | Expected Behaviour | Compliance Implication |
|----------|-------------------|----------------------|
| Freeze while already FROZEN | HTTP 409 `ALREADY_FROZEN`; no audit event written; idempotent if same `Idempotency-Key` | — |
| Concurrent freeze from user + ops (race) | Optimistic lock: first writer wins; second → HTTP 409 `CONCURRENT_MODIFICATION` | Audit trail shows which actor won; unambiguous |
| Transaction attempted on FROZEN card | Auth rejected before reaching payment network; `CARD_FROZEN` error code; rejection event logged | Rejection logged with timestamp |
| Transaction attempted on TERMINATED card | Auth rejected; `CARD_TERMINATED`; cannot be reversed | Permanent; logged |
| Daily limit set to 0 | HTTP 422 `INVALID_LIMIT_VALUE` — zero not valid for daily limit; use freeze for spending suspension | Status remains ACTIVE; no confusion between limit=0 and FROZEN |
| Per-transaction limit set to 0 | HTTP 422 `INVALID_LIMIT_VALUE` | Same as above |
| Limit amount > reasonable max (99_999_99 minor units) | HTTP 422 `LIMIT_OUT_OF_RANGE` | — |
| Limit set on FROZEN card | HTTP 422 `CARD_NOT_ACTIVE` | — |
| GDPR erasure for card with active legal hold | HTTP 422 `ERASURE_BLOCKED_LEGAL_HOLD`; user notified with reason; block request logged | GDPR Art. 17(3)(e) exception; retention obligation takes precedence |
| Max cards per account exceeded (limit: 5) | HTTP 422 `MAX_CARDS_REACHED`; no card created | — |
| Tokenizer service unavailable at card create | HTTP 503; no card row written; safe to retry with same `Idempotency-Key` | PAN never in DB in partial state |
| Stale auth-network read after freeze | Card state cached max 500 ms in auth service; gap documented as assumed SLO | Within regulatory tolerance for payment fraud window |
| PAN regex match found in CI log scan | Build fails; alert raised; log source investigated before next deployment | PCI DSS Req. 3.3 enforcement |
| Unfreeze on TERMINATED card | HTTP 422 `INVALID_STATE_TRANSITION` | — |
| Idempotency key reused with different payload | HTTP 422 `IDEMPOTENCY_KEY_CONFLICT` | — |
| Replacement card — tokenizer fails after original terminated | Original card remains TERMINATED; new card not created; HTTP 503; caller must initiate new replacement | No rollback of termination; audit records both events |
| GET card details for terminated card | HTTP 200 with status=TERMINATED; read-only; all fields present except pan_token | Historical access preserved |

---

## Verification

### How Each Mid-Level Objective Is Verified

| MO | Verification Approach | Acceptance Signal |
|----|----------------------|-------------------|
| MO-1 (card create + tokenize) | Integration test: create card → assert no raw PAN in DB → assert `masked_pan` format `****-****-****-XXXX` → assert audit event `to_state=PENDING` written atomically | All 3 assertions pass; CI PAN regex scan returns 0 matches |
| MO-2 (freeze/unfreeze < 500 ms) | Load test: 100 concurrent freeze requests; measure p95 latency; assert 0 duplicate state transitions in DB | p95 < 500 ms; conflict errors = expected count; no silent duplicates |
| MO-3 (limits enforced) | Unit test per limit type: mock auth call → assert rejection when over limit; assert acceptance when under limit | Test matrix covers DAILY, PER_TRANSACTION, MCC; no false positives or negatives |
| MO-4 (audit trail complete) | E2E test: run full lifecycle PENDING → ACTIVE → FROZEN → ACTIVE → TERMINATED → assert audit table has 5 events in correct order → assert no gaps in `from_state/to_state` chain | Complete chain present; `event_id` order matches `timestamp_utc` order |
| MO-5 (termination immutable) | Test: terminate card → attempt unfreeze → assert HTTP 422; attempt limit update → assert HTTP 422 | `INVALID_STATE_TRANSITION` returned; no state change in DB |

### Test Categories (as Documentation)

- **Unit:** limit enforcement logic, state transition validator function, PAN masking function, audit event serializer, idempotency key validator
- **Integration:** card create with real tokenizer mock; audit write atomicity (simulate audit DB failure → assert card row also absent); idempotency cache hit/miss behavior
- **E2E:** full card lifecycle; GDPR erasure flow (request → job run → assert PII nullified → assert audit structurally intact)
- **Compliance review (manual):** audit log completeness checklist; PAN-in-logs scan report; GDPR erasure confirmation report; PCI DSS Req. 10 audit trail review

---

## Low-Level Tasks

### Task 1: CREATE_CARD
**Serves:** MO-1

Create a new virtual card in PENDING state for a given account.

**Steps:**
1. Validate `account_id` exists and account is active; assert card count for account < 5
2. Call tokenization service with raw PAN; receive `pan_token` and `masked_pan`; raw PAN discarded from memory within 100 ms
3. Open DB transaction: write `cards` row `{ id=UUID, account_id, status=PENDING, pan_token, masked_pan, version=1 }` and audit event `{ from_state=null, to_state=PENDING }` atomically
4. Write consent record with timestamp and consent version string
5. Return `{ card_id, masked_pan, status: "PENDING" }`

**Acceptance Criteria:**
- [ ] Card row exists with `status=PENDING` and non-null `pan_token`; raw PAN absent from DB and logs
- [ ] `masked_pan` matches pattern `****-****-****-XXXX`
- [ ] Audit event with `to_state=PENDING` written in same transaction as card row
- [ ] Tokenizer unavailable → HTTP 503; no card row in DB (transaction rolled back)
- [ ] 6th card for same account → HTTP 422 `MAX_CARDS_REACHED`; no card row created
- [ ] Duplicate request with same `Idempotency-Key` → same response; only one card row in DB

---

### Task 2: ACTIVATE_CARD
**Serves:** MO-1

Transition card from PENDING to ACTIVE.

**Steps:**
1. Load card; assert `status=PENDING`; assert requesting actor is the card owner or a SYSTEM actor
2. Apply optimistic lock: `UPDATE cards SET status='ACTIVE', version=version+1 WHERE id=:id AND version=:current_version`
3. Write audit event `{ from_state=PENDING, to_state=ACTIVE }`

**Acceptance Criteria:**
- [ ] Card transitions to ACTIVE; `version` incremented by 1
- [ ] Audit event written with correct `from_state` and `to_state`
- [ ] Activation of non-PENDING card → HTTP 422 `INVALID_STATE_TRANSITION`
- [ ] Concurrent activation (two requests simultaneously) → second request gets HTTP 409 `CONCURRENT_MODIFICATION`

---

### Task 3: FREEZE_CARD
**Serves:** MO-2

Transition card from ACTIVE to FROZEN.

**Steps:**
1. Load card; assert `status=ACTIVE`
2. Apply optimistic lock: `UPDATE cards SET status='FROZEN', version=version+1 WHERE id=:id AND version=:current_version`
3. Write audit event `{ from_state=ACTIVE, to_state=FROZEN, actor_id, actor_role, reason }`
4. Publish state-change event to auth cache propagation queue (target: auth service cache updated within 500 ms)

**Acceptance Criteria:**
- [ ] Card transitions to FROZEN; p95 latency < 500 ms under 100 concurrent requests
- [ ] Audit event includes `actor_role` field (USER or OPS)
- [ ] Freeze of already-FROZEN card → HTTP 409 `ALREADY_FROZEN`; no audit event written
- [ ] Concurrent freeze race between user and ops → losing request gets HTTP 409 `CONCURRENT_MODIFICATION`; winning actor's event is in audit log

---

### Task 4: UNFREEZE_CARD
**Serves:** MO-2

Transition card from FROZEN to ACTIVE.

**Steps:**
1. Load card; assert `status=FROZEN`
2. Apply optimistic lock: `UPDATE cards SET status='ACTIVE', version=version+1 WHERE id=:id AND version=:current_version`
3. Write audit event `{ from_state=FROZEN, to_state=ACTIVE }`
4. Publish state-change event to auth cache propagation queue

**Acceptance Criteria:**
- [ ] Card returns to ACTIVE; previous FROZEN event preserved and immutable in audit log
- [ ] Unfreeze of TERMINATED card → HTTP 422 `INVALID_STATE_TRANSITION`
- [ ] Optimistic lock conflict → HTTP 409 `CONCURRENT_MODIFICATION`
- [ ] Auth cache reflects ACTIVE state within 500 ms of response

---

### Task 5: TERMINATE_CARD
**Serves:** MO-5

Permanently terminate a card from any non-TERMINATED state.

**Steps:**
1. Validate MFA confirmation token in request header (`X-MFA-Token`); reject with HTTP 403 `MFA_REQUIRED` if absent or invalid
2. Load card; assert `status != TERMINATED`
3. Apply optimistic lock: `UPDATE cards SET status='TERMINATED', version=version+1 WHERE id=:id AND version=:current_version`
4. Write audit event `{ from_state=<current>, to_state=TERMINATED, reason }`
5. Publish termination event; auth service marks card as permanently rejected

**Acceptance Criteria:**
- [ ] Card status = TERMINATED; all subsequent auth requests rejected with `CARD_TERMINATED`
- [ ] State is immutable: any further mutation attempt → HTTP 422 `INVALID_STATE_TRANSITION`
- [ ] Missing or invalid MFA → HTTP 403 `MFA_REQUIRED`; no state change
- [ ] Audit event includes final `from_state` accurately
- [ ] Optimistic lock conflict → HTTP 409; no state change

---

### Task 6: REPLACE_CARD
**Serves:** MO-5

Terminate existing card and issue a replacement with a new PAN.

**Steps:**
1. Validate MFA; call TERMINATE_CARD on original card (Task 5)
2. Call CREATE_CARD to create new card (Task 1); on success, set `replaced_by = new_card_id` on original card row
3. Both the termination audit event and the new-card creation audit event are written

**Acceptance Criteria:**
- [ ] Original card terminated; new card in PENDING state with new `pan_token` and `masked_pan`
- [ ] `replaced_by` on original card row points to new card ID
- [ ] Tokenizer failure on new card → original card remains TERMINATED; HTTP 503 returned; caller must initiate a fresh replacement request
- [ ] Both audit events (terminate + create) are present and correctly linked via `card_id`

---

### Task 7: SET_DAILY_LIMIT
**Serves:** MO-3

Upsert a daily aggregate spending limit for a card.

**Steps:**
1. Assert card `status=ACTIVE`
2. Validate `amount_minor_units` > 0 and ≤ 99_999_99
3. Validate `currency` is a valid ISO 4217 code
4. Upsert `card_limits` row `{ card_id, limit_type=DAILY, amount_minor_units, currency, updated_by }`
5. Write audit event for the limit change

**Acceptance Criteria:**
- [ ] Limit persisted; enforced on next authorization request
- [ ] `amount_minor_units = 0` → HTTP 422 `INVALID_LIMIT_VALUE`
- [ ] Limit on FROZEN or TERMINATED card → HTTP 422 `CARD_NOT_ACTIVE`
- [ ] Limit update reflected within 1 000 ms (p95)

---

### Task 8: SET_PER_TRANSACTION_LIMIT
**Serves:** MO-3

Upsert a per-transaction spending limit for a card.

**Steps:**
Same as Task 7 with `limit_type=PER_TRANSACTION`.

**Acceptance Criteria:**
- [ ] Single transaction with amount > limit → auth rejected with `LIMIT_EXCEEDED`
- [ ] Single transaction with amount ≤ limit → auth proceeds (limit check passes)
- [ ] Limit update reflected within 1 000 ms (p95)
- [ ] `amount_minor_units = 0` → HTTP 422 `INVALID_LIMIT_VALUE`

---

### Task 9: SET_MCC_LIMIT
**Serves:** MO-3

Configure a merchant category code allow or block rule for a card.

**Steps:**
1. Assert card `status=ACTIVE`
2. Validate `mcc_code` is a 4-digit numeric string
3. Validate `mcc_action` is `BLOCK` or `ALLOW`
4. Upsert `card_limits` row `{ card_id, limit_type=MCC, mcc_code, mcc_action, updated_by }`
5. Write audit event

**Acceptance Criteria:**
- [ ] Transaction with MCC matching a BLOCK rule → auth rejected with `MCC_BLOCKED`
- [ ] Transaction with MCC not matching any rule → auth proceeds (default allow)
- [ ] Invalid MCC format (non-4-digit, non-numeric) → HTTP 422 `INVALID_MCC`
- [ ] Duplicate rule for same MCC → upsert overwrites; one row per card+MCC pair

---

### Task 10: LIST_TRANSACTIONS
**Serves:** MO-4

Return paginated transaction history for a card.

**Steps:**
1. Assert requesting user owns the card (role=USER) or is an ops agent (role=OPS)
2. Query `card_transactions` with cursor-based pagination (cursor = last seen `id`); max page size 50
3. Apply optional date range filter (`from_date`, `to_date` in ISO 8601)
4. Return `{ data: [...], next_cursor, total_count }`

**Acceptance Criteria:**
- [ ] Response never includes `pan_token`, raw PAN, or CVV fields
- [ ] Cursor-based pagination produces consistent results across pages (no duplicates, no gaps)
- [ ] Request for another user's card by a USER role → HTTP 403 `FORBIDDEN`
- [ ] Empty transaction history → `{ data: [], next_cursor: null, total_count: 0 }`
- [ ] Page size > 50 in request → capped at 50; no error

---

### Task 11: GET_CARD_DETAILS
**Serves:** MO-1, MO-4

Return card metadata to the cardholder or ops.

**Acceptance Criteria:**
- [ ] Response includes `card_id`, `masked_pan`, `status`, `limits`, `created_at`, `updated_at`
- [ ] Raw PAN and `pan_token` absent from response in all cases
- [ ] TERMINATED card → HTTP 200 with `status=TERMINATED`; all fields present (read-only historical access)
- [ ] Another user's card (USER role) → HTTP 403 `FORBIDDEN`

---

### Task 12: GET_AUDIT_TRAIL
**Serves:** MO-4

Return the full state transition history for a card (ops-only).

**Acceptance Criteria:**
- [ ] Non-OPS role → HTTP 403 `FORBIDDEN`
- [ ] Events returned sorted by `timestamp_utc` ascending
- [ ] Every state transition for the card's lifetime is present; `from_state/to_state` chain has no gaps
- [ ] `source_ip` field present for events before GDPR erasure; `null` for events after erasure

---

### Task 13: AUDIT_EVENT_WRITER (shared internal module)
**Serves:** Cross-cutting compliance

Internal module called by every mutating operation.

**Contract:**
```
write_audit_event(
  card_id: UUID,
  actor_id: UUID,
  actor_role: Enum[USER, OPS, SYSTEM],
  from_state: Optional[str],
  to_state: str,
  reason: Optional[str],
  source_ip: Optional[str]
) -> event_id: UUID
```

This function is called inside the same DB transaction as the parent operation. It must never be called outside a transaction context.

**Acceptance Criteria:**
- [ ] No mutating operation path exists in the codebase that does not call `write_audit_event`
- [ ] Audit write failure → entire parent transaction rolls back (verified by integration test: simulate audit DB failure → assert parent operation also absent)
- [ ] Audit event schema validated before insert; missing required fields → raise `AuditSchemaError`
- [ ] Function is synchronous; no fire-and-forget path

---

### Task 14: PAN_TOKENIZATION_MODULE
**Serves:** MO-1, PCI DSS compliance

Wrapper around the external tokenizer service. Guarantees no PAN leakage.

**Contract:**
```
tokenize_pan(raw_pan: str) -> { pan_token: str, masked_pan: str }
```

**Implementation constraints:**
- `raw_pan` parameter must not be logged at any log level
- If the external call exceeds 2 000 ms, raise `TokenizerTimeoutError`; do not store a partial result
- On success, caller must discard `raw_pan` from memory immediately (function does not cache the input)

**Acceptance Criteria:**
- [ ] Raw PAN never appears in application logs, error messages, or stack traces
- [ ] CI log scan (regex `[0-9]{16}`) on test run output returns 0 matches
- [ ] Tokenizer timeout (> 2 000 ms) → `TokenizerTimeoutError` raised; no `pan_token` stored
- [ ] `masked_pan` always returns format `****-****-****-XXXX`

---

### Task 15: GDPR_ERASURE_JOB
**Serves:** GDPR Art. 17 compliance

Scheduled job that processes verified erasure requests within the 30-day regulatory SLA.

**Steps:**
1. Load all pending erasure requests where `status=PENDING` and `requested_at < NOW() - 30 days` (SLA warning threshold)
2. For each request: check for legal holds (active disputes, open fraud investigations); if hold exists → set `status=BLOCKED`, log block reason, notify user via notification service; skip erasure
3. For records with no hold: nullify `source_ip` in `card_audit_log` for all events belonging to the card; nullify `user_id` reference and PII fields in `cards`; preserve `card_id`, `amount_minor_units`, `timestamp_utc`, `event_id`
4. Mark erasure request `status=COMPLETED`; log completion with timestamp

**Documented Conflict — GDPR Art. 17(3)(e):**
Audit records must be retained for 7 years (PCI DSS Req. 10.7). GDPR Art. 17(3)(e) permits retention where processing is necessary for the establishment, exercise, or defence of legal claims or where required by law. Therefore: structural audit fields are retained; only PII fields (`source_ip`) are nullified. This tradeoff is explicitly documented here and communicated to users in the privacy notice.

**Acceptance Criteria:**
- [ ] PII fields nullified within 30 days of verified request (integration test with time-shifted clock)
- [ ] Audit record structurally intact after erasure: `event_id`, `card_id`, `amounts`, `timestamp_utc` all present
- [ ] Legal hold → user notified; request logged with block reason; erasure not performed
- [ ] Job is idempotent: re-running on an already-erased card → no-op; no error
- [ ] Erasure request for non-existent card → logged as `NOT_FOUND`; no action

---

### Task 16: IDEMPOTENCY_MIDDLEWARE
**Serves:** Reliability, MO-2

Request deduplication layer applied to all mutating endpoints.

**Steps:**
1. Extract `Idempotency-Key` header; validate UUID v4 format; reject with HTTP 400 `MISSING_IDEMPOTENCY_KEY` if absent on any mutating endpoint
2. Check cache: cache hit → return cached response body with original HTTP status code immediately (do not re-execute handler)
3. Cache miss → execute handler; on response, store `{ key, response_body, http_status, created_at }` in cache with 24 h TTL
4. If same key arrives with different request payload → HTTP 422 `IDEMPOTENCY_KEY_CONFLICT`

**Acceptance Criteria:**
- [ ] Duplicate freeze request with same `Idempotency-Key` returns same 200 response; only one `ACTIVE→FROZEN` transition in DB
- [ ] Different payload + same key → HTTP 422 `IDEMPOTENCY_KEY_CONFLICT`
- [ ] Absent key on mutating endpoint → HTTP 400 `MISSING_IDEMPOTENCY_KEY`
- [ ] Cache TTL expires after 24 h; subsequent request treated as new (verified by integration test with TTL override)
