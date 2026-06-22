---
name: research-quality-measurement
description: Defines quality levels for rating bug research output. Used by Research Verifier to score codebase-research.md.
---

# Research Quality Measurement

Use this skill when writing `verified-research.md`. Rate the research using the table below and include the chosen label in the **Research Quality Assessment** section.

## Quality Levels

| Level | Label | Criteria |
|-------|-------|----------|
| 5 | EXCELLENT | All file:line references valid and verified against source; all snippets match source exactly; no missed bugs; analysis complete and correct |
| 4 | GOOD | ≥90% of references valid; snippets match with trivial differences (whitespace); minor discrepancies documented; no critical bugs missed |
| 3 | ACCEPTABLE | ≥70% of references valid; discrepancies present but non-critical; all seeded bugs identified even if location slightly off |
| 2 | POOR | <70% of references valid; or at least one critical bug missed entirely; analysis incomplete |
| 1 | INVALID | References point to non-existent files or functions; snippets don't match source; research cannot be used as input to planning |

## Required Sections in verified-research.md

1. **Verification Summary** — pass/fail verdict, Research Quality label and level number
2. **Verified Claims** — each reference confirmed correct: `file:line — description — VERIFIED`
3. **Discrepancies Found** — each error found: `file:stated_line (actual: actual_line) — description — DISCREPANCY`
4. **Research Quality Assessment** — chosen level (1–5), label, and 2–3 sentences of reasoning
5. **References** — list of source files read during verification

## How to Verify a Reference

For each `file:line` reference in the research:
1. Read the referenced file at the stated line
2. Compare the snippet in the research to the actual source
3. VERIFIED if content matches within ±2 lines; DISCREPANCY if off by more or content differs
