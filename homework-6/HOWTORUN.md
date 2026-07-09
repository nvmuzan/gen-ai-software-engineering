# ▶️ How to Run

> Multi-Agent Banking Pipeline — Homework 6 · Created by Vladyslav Nahirych

All commands are run from the `homework-6/` directory. Examples use the Windows
venv path `.venv/Scripts/python`; on macOS/Linux use `.venv/bin/python`.

## 1. Set up the environment

```bash
cd homework-6
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## 2. Run the full pipeline

```bash
.venv/Scripts/python integrator.py
```

Expected output (8 sample transactions):

```
Processed 8 | settled=6 rejected=2 flagged=3
TXN       STATUS      RISK    NOTE
TXN001    settled     low
TXN002    settled     medium  FLAGGED
TXN003    settled     low
TXN004    settled     medium  FLAGGED
TXN005    settled     medium  FLAGGED
TXN006    rejected    -       invalid ISO 4217 currency: XYZ
TXN007    rejected    -       amount must be positive
TXN008    settled     low
```

Results land in `shared/results/` (one file per transaction) plus
`shared/results/pipeline_summary.json`.

## 3. Validate transactions without processing (dry-run)

```bash
.venv/Scripts/python -m agents.transaction_validator --dry-run
```

## 4. Run the tests and check coverage

```bash
.venv/Scripts/python -m coverage run -m pytest -q
.venv/Scripts/python -m coverage report
```

Expected: all tests pass, `TOTAL` coverage ≥ 90% (gate is 80%).

## 5. Run the custom MCP server

```bash
.venv/Scripts/python mcp/server.py
```

This starts the FastMCP `pipeline-status` server exposing the tools
`get_transaction_status`, `list_pipeline_results`, and the resource
`pipeline://summary`. Both servers are configured in `mcp.json` (context7 +
pipeline-status).

## 6. Use the Claude Code slash commands

From Claude Code in this directory:

- `/run-pipeline` — clears `shared/`, runs the pipeline, summarizes results.
- `/validate-transactions` — runs the validator in dry-run and reports.
- `/write-spec` — regenerates `specification.md` from the template.

## 7. See the coverage-gate hook fire

The hook (`.claude/hooks/coverage_gate.py`, wired in `.claude/settings.json`)
blocks `git push` when coverage < 80%. To see it block, temporarily lower a
coverage number or run the hook directly with a low value:

```bash
echo '{"tool_input": {"command": "git push origin main"}}' | .venv/Scripts/python .claude/hooks/coverage_gate.py
echo "exit code: $?"
```

---

## Screenshots to capture (for the PR)

Save each into `docs/screenshots/`:

| File | Command / action to capture |
|------|-----------------------------|
| `pipeline-run.png` | terminal after `.venv/Scripts/python integrator.py` (step 2) |
| `test-coverage.png` | `.venv/Scripts/python -m coverage report` showing ≥ 90% (step 4) |
| `skill-run-pipeline.png` | `/run-pipeline` executing in Claude Code (step 6) |
| `hook-trigger.png` | the coverage-gate hook blocking a push (step 7) |
| `mcp-interaction.png` | a context7 query result **and** a custom MCP tool call (`get_transaction_status` or `list_pipeline_results`) |
