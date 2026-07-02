# agents.md — Project Context for AI Agents

> Author: Vladyslav Nahirych · Homework 6 (Capstone)

This file gives an AI coding assistant (Claude Code / Copilot) the context it
needs to work on this repository.

## Project

A multi-agent banking transaction pipeline. Raw transactions flow through four
cooperating agents that communicate by moving JSON messages through shared
directories. The system is language-agnostic by assignment; this implementation
uses **Python 3.11**.

## Ground rules

- **Money is `decimal.Decimal`, never `float`.** Amounts are strings in
  messages; quantize to 2 places with `ROUND_HALF_UP`.
- **Currencies** are validated against an ISO 4217 subset.
- **PII** (account numbers, names) must never be logged in plaintext — mask it.
- Every change ships with tests; the suite must stay green and coverage ≥ 90%
  (a push hook blocks below 80%).
- Prefer small, single-responsibility modules with a clear interface.

## Message contract

```json
{
  "message_id": "uuid4",
  "timestamp": "ISO-8601 UTC",
  "source_agent": "transaction_validator",
  "target_agent": "fraud_detector",
  "message_type": "transaction",
  "data": { "transaction_id": "TXN001", "amount": "1500.00", "currency": "USD", "status": "validated" }
}
```

All agents implement `process_message(message: dict) -> dict` (see
`agents/base.py`), returning either an advanced message (new `target_agent`) or a
rejection routed to `results`.

## The agents

| Order | Agent | File | Input → Output | Decides |
|-------|-------|------|----------------|---------|
| 1 | Transaction Validator | `agents/transaction_validator.py` | input → fraud_detector / reject | fields present, amount > 0 & ≤ 2dp, ISO 4217 currency, `ACC-XXXX` accounts |
| 2 | Fraud Detector | `agents/fraud_detector.py` | → compliance_checker | risk_score (high-value +40, off-hours +30, cross-border +30); flags at ≥ 40 |
| 3 | Compliance Checker | `agents/compliance_checker.py` | → settlement_processor / reject | sanctioned-country screening, `requires_ctr` at ≥ $10k |
| 4 | Settlement Processor | `agents/settlement_processor.py` | → results | fee (10 bps, ROUND_HALF_UP) + net amount, marks settled |

Orchestration lives in `integrator.py` (`run_pipeline`), and the file bus in
`shared_bus.py`. A custom FastMCP server (`mcp/server.py`) makes results
queryable.

## Layout

```
agents/            four pipeline agents + base.py
integrator.py      orchestrator (run_pipeline, main)
models.py          message envelope, Status enum, to_decimal
shared_bus.py      file-based message bus over shared/
mcp/server.py      custom FastMCP server (get_transaction_status, list_pipeline_results, pipeline://summary)
tests/             pytest suite (unit per agent + integration)
.claude/           slash commands + coverage-gate hook
shared/            input, processing, output, results (runtime message dirs)
```

## Running

```bash
.venv/Scripts/python integrator.py                 # run the full pipeline
.venv/Scripts/python -m agents.transaction_validator --dry-run   # validate only
.venv/Scripts/python -m coverage run -m pytest && .venv/Scripts/python -m coverage report
```
