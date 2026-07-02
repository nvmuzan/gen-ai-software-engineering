# Specification — Multi-Agent Banking Transaction Pipeline

> Author: Vladyslav Nahirych · Homework 6 (Capstone)

---

## 1. High-Level Objective

A file-based multi-agent pipeline that ingests raw banking transactions, then
validates, risk-scores, compliance-screens, and settles each one, writing an
auditable per-transaction result and a run summary.

---

## 2. Mid-Level Objectives

1. Every transaction in `sample-transactions.json` is processed and produces
   exactly one final record in `shared/results/` (settled or rejected).
2. Transactions with an invalid amount (non-positive or > 2 decimal places),
   an unknown ISO 4217 currency, a malformed account, or a missing required
   field are **rejected** with a human-readable `reason`.
3. Transactions above $10,000 are **flagged for fraud review** with a numeric
   `risk_score` and `risk_level`; off-hours and cross-border activity add risk.
4. Transactions from sanctioned countries are rejected at the compliance stage;
   amounts ≥ $10,000 are marked `requires_ctr` (currency transaction report).
5. Settlement computes a fee and net amount using `decimal.Decimal` with
   `ROUND_HALF_UP`, and the run emits `shared/results/pipeline_summary.json`
   plus an audit trail with ISO 8601 timestamps; test coverage ≥ 90%.

---

## 3. Implementation Notes

- **Monetary values:** `decimal.Decimal` only — never `float`. Amounts travel as
  strings in messages; arithmetic quantizes to 2 places with `ROUND_HALF_UP`.
- **Currency codes:** validated against an ISO 4217 subset (USD, EUR, GBP, JPY,
  UAH, CHF, CAD, AUD, SEK, NOK).
- **Account format:** `ACC-` followed by 4+ uppercase alphanumerics.
- **Logging / audit trail:** each agent can emit an audit line of the form
  `<ISO-8601 UTC> | <agent> | <transaction_id> | <outcome>`.
- **PII:** account numbers are masked (`ACC-****1001`) and names are never
  logged in plaintext.
- **Message envelope:** `{message_id, timestamp, source_agent, target_agent,
  message_type, data}`; agents communicate by moving JSON files through
  `shared/{input,processing,output,results}/`.

---

## 4. Context

**Beginning state:** `sample-transactions.json` — 8 raw transaction records,
including deliberately bad data (currency `XYZ`, a negative refund) and
high-value wires.

**Ending state:** one JSON result file per transaction in `shared/results/`, a
`pipeline_summary.json` with total / settled / rejected / flagged counts, and a
green test suite at ≥ 90% coverage. Intermediate stage directories
(`input/`, `processing/`, `output/`) are empty after a run.

---

## 5. Low-Level Tasks

```
Task: Transaction Validator
Prompt: "Create a TransactionValidator agent that validates required fields,
         positive Decimal amounts with <=2 decimals, ISO 4217 currency, and
         ACC-XXXX account format; advance valid transactions to fraud_detector,
         reject the rest with a reason. Support a --dry-run report mode."
File to CREATE: agents/transaction_validator.py
Function to CREATE: TransactionValidator.process_message(message: dict) -> dict
Details: Checks presence of required fields, amount > 0 and exponent >= -2,
         currency in VALID_CURRENCIES, source/destination match ACCOUNT_RE.
```

```
Task: Fraud Detector
Prompt: "Create a FraudDetector agent that scores each transaction 0-100 for
         risk: +40 high-value (>= 10000), +30 off-hours (hour < 6), +30
         cross-border (country != US). Flag transactions scoring >= 40 and pass
         them to compliance_checker."
File to CREATE: agents/fraud_detector.py
Function to CREATE: FraudDetector.process_message(message: dict) -> dict
Details: Adds risk_score, risk_level (low/medium/high), fraud_reasons; sets
         status=flagged when score >= 40.
```

```
Task: Compliance Checker
Prompt: "Create a ComplianceChecker agent that rejects transactions from
         sanctioned countries {IR, KP, SY, CU} and marks requires_ctr for
         amounts >= 10000; otherwise advance to settlement_processor,
         preserving a flagged status."
File to CREATE: agents/compliance_checker.py
Function to CREATE: ComplianceChecker.process_message(message: dict) -> dict
Details: Screens metadata.country against SANCTIONED, sets compliance_status,
         requires_ctr, and status=cleared unless already flagged.
```

```
Task: Settlement Processor
Prompt: "Create a SettlementProcessor agent that computes a 10 bps fee and net
         amount with Decimal ROUND_HALF_UP, marks the transaction settled, and
         routes the final message to results."
File to CREATE: agents/settlement_processor.py
Function to CREATE: SettlementProcessor.process_message(message: dict) -> dict
Details: fee = amount * 0.001 quantized to cents; net = amount - fee; sets
         status=settled and a flagged boolean; target=results.
```

```
Task: Integrator / Orchestrator
Prompt: "Create integrator.py that sets up shared/, loads
         sample-transactions.json, runs each transaction through the four
         agents in order via the file bus, and writes pipeline_summary.json."
File to CREATE: integrator.py
Function to CREATE: run_pipeline(root: Path, transactions: list[dict]) -> dict
Details: Moves messages input -> processing -> output -> results, short-circuits
         rejects, and returns {total, settled, rejected, flagged, results}.
```
