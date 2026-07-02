# 🏦 Multi-Agent Banking Transaction Pipeline

> **Created by Vladyslav Nahirych** · Homework 6 (Final Capstone)
> **AI tools used:** Claude Code (Anthropic)

A file-based, multi-agent pipeline that processes banking transactions end to
end. Each transaction is validated, risk-scored for fraud, screened for
compliance, and settled — with an auditable result written for every record.

---

## What it does

Raw transactions are read from `sample-transactions.json` and passed as JSON
messages through four cooperating agents. Agents communicate **only through
files** in `shared/{input,processing,output,results}/`, mimicking a real
message-bus architecture. Money is handled exclusively with `decimal.Decimal`
(never `float`), currencies are validated against ISO 4217, and account numbers
are masked in logs (PII protection). The run produces one result file per
transaction plus a `pipeline_summary.json`.

A run over the 8 sample transactions yields: **6 settled, 2 rejected, 3 flagged**
(TXN006 rejected for currency `XYZ`, TXN007 for a negative amount; TXN002/004/005
flagged for fraud review).

## Agents

- **Transaction Validator** — checks required fields, positive `Decimal` amounts
  (≤ 2 decimals), ISO 4217 currency, and `ACC-XXXX` account format; rejects the
  rest with a reason. Has a `--dry-run` report mode.
- **Fraud Detector** — scores risk 0–100: high-value (≥ $10k) +40, off-hours
  (< 06:00) +30, cross-border +30; flags transactions scoring ≥ 40.
- **Compliance Checker** — rejects sanctioned-country transactions and marks
  `requires_ctr` for amounts ≥ $10k (currency transaction report).
- **Settlement Processor** — computes a 10 bps fee and net amount with
  `ROUND_HALF_UP`, marks the transaction `settled`, and finalizes it.

The **Integrator** (`integrator.py`) orchestrates the four agents; a custom
**FastMCP server** (`mcp/server.py`) makes the results queryable.

## Architecture

```
                       sample-transactions.json
                                 │
                                 ▼
                          ┌─────────────┐
                          │ integrator  │  setup shared/, load, orchestrate
                          └──────┬──────┘
                                 │  input/
                                 ▼
   ┌──────────────────┐   validated    ┌──────────────────┐
   │ Transaction      │──────────────▶ │ Fraud Detector   │
   │ Validator        │                │ risk_score/level │
   └────────┬─────────┘                └────────┬─────────┘
            │ reject                            │ flagged?
            ▼                                    ▼
        results/                        ┌──────────────────┐
            ▲   reject                  │ Compliance       │
            │◀──────────────────────────│ Checker (AML)    │
            │                           └────────┬─────────┘
            │                                    │ cleared
            │                                    ▼
            │   settled              ┌──────────────────┐
            └────────────────────────│ Settlement       │
                                     │ Processor (fee)  │
                                     └──────────────────┘
                                 │
                                 ▼
              shared/results/*.json  +  pipeline_summary.json
```

## Tech stack

| Area | Choice |
|------|--------|
| Language | Python 3.11 |
| Money | `decimal.Decimal` + `ROUND_HALF_UP` |
| Messaging | File-based JSON bus (`shared/`) |
| Tests | `pytest` + `coverage` (92%, gate 80%) |
| MCP server | FastMCP (`mcp/server.py`) |
| Docs lookup | context7 MCP (see `research-notes.md`) |
| Automation | Claude Code slash commands + coverage-gate hook |

## Repository layout

```
homework-6/
├── agents/            transaction_validator, fraud_detector, compliance_checker,
│                      settlement_processor, base
├── integrator.py      orchestrator (run_pipeline, main)
├── models.py          message envelope, Status enum, to_decimal
├── shared_bus.py      file-based message bus
├── mcp/server.py      custom FastMCP server + mcp.json
├── tests/             unit tests per agent + integration + CLI
├── .claude/           slash commands + coverage-gate hook + settings.json
├── shared/            input · processing · output · results
├── specification.md · agents.md · research-notes.md
└── docs/screenshots/  submission screenshots
```

## Screenshots

See [`docs/screenshots/`](docs/screenshots/):

| File | Shows |
|------|-------|
| `pipeline-run.png` | `python integrator.py` full output |
| `test-coverage.png` | coverage report (≥ 90%) |
| `skill-run-pipeline.png` | `/run-pipeline` skill executing |
| `hook-trigger.png` | coverage-gate hook blocking a push |
| `mcp-interaction.png` | context7 query + custom MCP tool call |

## Quick start

See [HOWTORUN.md](HOWTORUN.md) for full step-by-step instructions.

```bash
cd homework-6
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python integrator.py
```
