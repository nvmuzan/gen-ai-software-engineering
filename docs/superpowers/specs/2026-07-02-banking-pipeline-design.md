# Design: AI-Powered Multi-Agent Banking Pipeline (Homework 6)

- **Date:** 2026-07-02
- **Author:** Vladyslav Nahirych
- **Status:** Approved (design), pending spec review

---

## 1. Goal

Build four **meta-agents** (AI/automation workflows in Claude Code) that *create* a
transaction-processing system, and the resulting **runtime pipeline** itself. Meta-agent
mapping:

| Meta-agent | Deliverable |
|---|---|
| Agent 1 — Specification | Skill `/write-spec` + `specification.md` |
| Agent 2 — Code generation | Pipeline code (uses MCP context7 during generation) |
| Agent 3 — Unit tests | Test suite + coverage-gate hook |
| Agent 4 — Documentation | `README.md` / `HOWTORUN.md` (with author name) |

Stack: **Python 3.11**, `pytest` + `coverage`, FastMCP for the custom MCP server.
Skills/hooks live locally in `homework-6/.claude/`. Four runtime agents.

## 2. Runtime pipeline architecture

File-based protocol: JSON messages flow through `shared/`. The integrator runs each
transaction sequentially through four agents.

```
sample-transactions.json
        │
        ▼
   [integrator.py]  ── creates shared/, loads transactions into input/
        │
        ▼
 shared/input/    ─→ [1. Validator]         required fields, amount>0, ISO 4217,
        │                                   account format ACC-XXXX
        ▼                                   (TXN006 XYZ ✗, TXN007 -100 ✗ → reject)
 shared/output/   ─→ [2. Fraud Detector]    risk_score 0-100: high-value(>10k),
        │                                   off-hours, cross-border
        ▼
 shared/output/   ─→ [3. Compliance]        AML thresholds, sanctioned countries
        │
        ▼
 shared/output/   ─→ [4. Settlement]        fee (Decimal, ROUND_HALF_UP), net amount
        │
        ▼
 shared/results/  ─→ per-TXN outcome + pipeline_summary.json (reporting rollup)
```

- A transaction rejected at any stage goes straight to `results/` with a `reason`
  field and does not continue.
- Every operation appends to an audit log (ISO 8601 timestamp, agent name,
  transaction id, outcome).
- PII (account numbers, names) is masked in logs — never plaintext.

## 3. Components

Each unit has one responsibility and a well-defined interface.

| File | Responsibility |
|---|---|
| `agents/base.py` | Shared contract `process_message(message: dict) -> dict`, JSON read/write, logger, PII masking |
| `agents/transaction_validator.py` | Field validation, `Decimal` amounts, ISO 4217, account format; `--dry-run` mode |
| `agents/fraud_detector.py` | Risk scoring 0-100 + `risk_level` |
| `agents/compliance_checker.py` | AML rules, sanctioned countries, reporting threshold |
| `agents/settlement_processor.py` | Fee/net calculation in `Decimal`, final status |
| `models.py` | Dataclasses for message/transaction, status enum |
| `shared_bus.py` | shared/ directory ops (stage moves, atomic write) |
| `integrator.py` | Orchestrator: setup → load → run agents in order → summary |

Standard message format:

```json
{
  "message_id": "uuid4-string",
  "timestamp": "2026-03-16T10:00:00Z",
  "source_agent": "transaction_validator",
  "target_agent": "fraud_detector",
  "message_type": "transaction",
  "data": { "transaction_id": "TXN001", "amount": "1500.00", "currency": "USD", "status": "validated" }
}
```

## 4. MCP integration (Task 4)

- **context7** — invoked for real via the `docs` subagent during code generation.
  At least 2 queries documented in `research-notes.md` (search term, returned library id,
  applied insight). Planned queries: Python `decimal` `ROUND_HALF_UP`; FastMCP tools/resource API.
- **Custom FastMCP server** `mcp/server.py`:
  - Tool `get_transaction_status(transaction_id: str)` → status from `shared/results/`
  - Tool `list_pipeline_results()` → summary of all processed transactions
  - Resource `pipeline://summary` → latest run summary as text
- `mcp.json` configures both servers.

## 5. Skills + hook (Task 3)

In `homework-6/.claude/`:

- `commands/write-spec.md` — generates a spec from the template
- `commands/run-pipeline.md` — runs the pipeline end-to-end
- `commands/validate-transactions.md` — validator dry-run report
- `hooks/coverage_gate.py` + `settings.json` — **PreToolUse hook on `git push`**:
  runs `coverage`, exits non-zero (blocks) when total coverage < 80%.

## 6. Tests (Task 5)

`pytest` + `coverage`. Unit tests per agent + one integration test for the full
pipeline. Isolate from real `shared/` via `tmp_path`. Target ≥ 90%.

## 7. Documentation (Task 5 / Agent 4)

- `README.md` — author "Created by Vladyslav Nahirych", what the system does,
  per-agent bullets, ASCII architecture diagram, tech-stack table.
- `HOWTORUN.md` — numbered setup-to-demo steps.

## 8. Screenshots (done by user — no GUI capture available to the agent)

5 files in `docs/screenshots/`: `pipeline-run.png`, `test-coverage.png`,
`skill-run-pipeline.png`, `hook-trigger.png`, `mcp-interaction.png`. The agent
prepares everything so each is a one-command capture, with exact instructions and
`.gitkeep` placeholders + PR links.

## 9. Final layout

```
homework-6/
├── .claude/{commands/*.md, hooks/coverage_gate.py, settings.json}
├── agents/{base,transaction_validator,fraud_detector,compliance_checker,settlement_processor}.py
├── mcp/server.py
├── tests/
├── shared/{input,processing,output,results}/
├── integrator.py, models.py, shared_bus.py
├── specification.md, agents.md, research-notes.md
├── mcp.json, requirements.txt, README.md, HOWTORUN.md
└── docs/screenshots/
```

## 10. Verification criteria

- `python integrator.py` runs clean; all 8 transactions land in `shared/results/`.
- Rejected: TXN006 (currency XYZ), TXN007 (negative amount). Flagged high-value:
  TXN002 (25k), TXN005 (75k). TXN004 off-hours (02:47) + cross-border (DE).
- `pytest --cov` ≥ 90%; coverage-gate hook blocks a simulated push under 80%.
- Custom MCP tools respond; context7 queries documented.
- README contains the author name and ASCII diagram.
```
