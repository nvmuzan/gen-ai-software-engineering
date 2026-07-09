Generate a full project specification for the multi-agent banking pipeline,
following the Homework 6 specification template.

Steps:
1. Read `specification-TEMPLATE-hint.md` (if present in this folder) and
   `sample-transactions.json` to understand the input data shape.
2. Produce `specification.md` containing all five required sections:
   - **High-Level Objective** — one sentence describing what the pipeline does.
   - **Mid-Level Objectives** — 4–5 concrete, testable requirements.
   - **Implementation Notes** — decimal.Decimal for money, ISO 4217 currencies,
     audit logging with ISO 8601 timestamps, PII masking for account numbers.
   - **Context** — beginning state (`sample-transactions.json`) and ending state
     (processed results in `shared/results/`, a summary report, coverage ≥ 90%).
   - **Low-Level Tasks** — one entry per agent, each with
     Task / Prompt / File to CREATE / Function to CREATE / Details.
3. Save the result to `specification.md` and report what was written.
