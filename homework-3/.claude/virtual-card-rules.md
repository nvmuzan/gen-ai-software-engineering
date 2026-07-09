# Virtual Card Service — Claude Code Working Rules

> **Scope of this file.** This is *not* a restatement of the domain contract.
> The **domain rules, tech stack, sensitive-data classification, and the full
> error-code reference live in [`agents.md`](../agents.md)**; the **product
> requirements and state machine live in [`specification.md`](../specification.md)**.
> This file defines **how Claude Code should *work* in this repo** — the
> coding-time conventions, self-checks, and workflow that make sure the code it
> produces actually satisfies that contract. When something here would repeat a
> domain rule, it links instead of copying.

---

## Where things live (read before generating)

| You need… | Read |
|-----------|------|
| What the feature must do, tasks, acceptance criteria | `specification.md` |
| Domain invariants, tech stack, sensitive-data table, error codes | `agents.md` |
| How to *name*, *check yourself*, and *sequence work* | this file |

If a request conflicts with `agents.md` or `specification.md`, **stop and surface
the conflict** — do not silently pick one. Those two files are the source of
truth; this file never overrides them.

---

## Naming Conventions (this repo's house style)

These are enforced here and are *not* documented elsewhere — follow them exactly.

- **Card states:** `SCREAMING_SNAKE_CASE` enum strings — `PENDING`, `ACTIVE`, `FROZEN`, `TERMINATED`
- **Error codes:** `SCREAMING_SNAKE_CASE` — e.g. `CARD_FROZEN`, `CONCURRENT_MODIFICATION`, `INVALID_STATE_TRANSITION` (full list: `agents.md` § Error Code Reference — do not invent new ones without adding them there)
- **DB columns:** `snake_case`; every monetary column suffixed `_minor_units` (e.g. `amount_minor_units`, `daily_limit_minor_units`)
- **State-mutating functions:** `verb_noun` — `freeze_card`, `terminate_card`, `create_card`, `set_daily_limit`. One state transition per function; no multi-purpose mutators.
- **Disambiguation:** when both an HTTP status and a card status are in scope, name them `http_status` and `card_status`. Never let one shadow the other.
- **Error payload key:** the human-readable field is `user_message` — never `message`, `msg`, or `detail`. (Structure defined in `agents.md`; only the key name is repeated here because it is the one thing most easily gotten wrong.)

---

## Self-Verification Checklist (run before proposing or finalizing any code)

Do not wait for CI to catch these. Before you present code that touches card data,
walk this list explicitly:

- [ ] **PAN scan.** Search the diff for any 16-digit sequence (`[0-9]{16}`) in logs, error strings, or responses. Must be zero. (Why: `agents.md` Domain Rule #1.)
- [ ] **Every `UPDATE cards …` carries `WHERE version = :current_version`.** No exceptions — a bare update is a data-race bug.
- [ ] **Every code path that mutates `cards.status` calls `audit_event_writer` in the *same* transaction.** If the audit write can't happen, the mutation must not commit.
- [ ] **Every mutating endpoint checks `Idempotency-Key` before any handler logic.** Missing key → `MISSING_IDEMPOTENCY_KEY`, returned first.
- [ ] **No `float`/`double` anywhere near money.** Amounts are integers in minor units.
- [ ] **`card_audit_log` touched?** Insert-only. If you generated an `UPDATE`/`DELETE` against it, delete that code.
- [ ] **Migration generated?** It has a `-- rollback:` section with the inverse op.

State only what you actually checked. If you couldn't verify an item, say so —
don't claim the checklist passed when it didn't.

---

## How to sequence a coding task (plan → implement → verify)

1. **Plan.** Identify which task number in `specification.md` the request implements, and state it. If the request maps to no task or spans several, say so before writing code.
2. **Implement** the smallest slice that satisfies that one task. Don't bundle unrelated changes.
3. **Verify** against the checklist above and against the task's acceptance criteria in `specification.md`. Report what you checked.

Every code suggestion should be traceable back to a spec task — that traceability
is the whole point of this project.

---

## Generation smells to avoid (things Claude tends to do that are wrong here)

- Adding a "convenience" route, flag, or param that bypasses auth / MFA / idempotency middleware — never, not even in test or debug mode.
- `try/except Exception` or `catch (e)` that swallows the error silently.
- Raw SQL string interpolation (`f"... WHERE id={card_id}"`). Parameterized queries or ORM only.
- Returning `pan_token` or raw PAN in *any* response body, including error bodies. Only `masked_pan` is safe.
- Widening an error response with extra fields, or renaming `user_message`.
- Inventing a new state transition or error code without first updating `specification.md` / `agents.md`.

---

## When unsure

Ask a clarifying question rather than guessing on anything touching money,
state transitions, audit, or PII. In a regulated FinTech domain a wrong guess is
a compliance incident, not a cosmetic bug — the cost of asking is always lower.
