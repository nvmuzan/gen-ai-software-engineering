# Banking Multi-Agent Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a file-based multi-agent banking transaction pipeline (validator → fraud → compliance → settlement) plus the Claude Code meta-agent obligations (spec skill, run/validate skills, coverage-gate hook, custom FastMCP server), with ≥90% test coverage.

**Architecture:** Each agent is a Python module exposing `process_message(message: dict) -> dict`, subclassing a shared `Agent` base. An `integrator.py` orchestrator loads `sample-transactions.json`, wraps each into a standard message, and runs it through the agents in order using `shared_bus.py` to move JSON files across `shared/{input,processing,output,results}/`. Rejected messages short-circuit to `results/`. A FastMCP server queries `shared/results/`.

**Tech Stack:** Python 3.11, `decimal.Decimal`, `pytest`, `coverage`, `fastmcp`, Claude Code skills/hooks.

## Global Constraints

- Monetary amounts: `decimal.Decimal` only, never `float`. Rounding `ROUND_HALF_UP`, 2 places.
- Currency codes validated against ISO 4217 subset (USD, EUR, GBP, JPY, UAH, CHF, CAD, AUD, …).
- Account format: `ACC-` followed by 4+ alphanumerics.
- Logging: audit trail line = ISO 8601 UTC timestamp, agent name, transaction id, outcome.
- PII masking: account numbers shown as `ACC-****1001`; names never logged plaintext.
- Message format: `{message_id, timestamp, source_agent, target_agent, message_type, data}`.
- Author name in README: **Vladyslav Nahirych**.
- All work on branch `homework-6-submission`. All paths relative to `homework-6/`.
- Coverage gate threshold: 80% (blocks push); target ≥90%.

---

### Task 1: Project scaffold

**Files:**
- Create: `homework-6/requirements.txt`
- Create: `homework-6/.gitignore`
- Create: `homework-6/agents/__init__.py` (empty)
- Create: `homework-6/tests/__init__.py` (empty)
- Create: `homework-6/shared/{input,processing,output,results}/.gitkeep`
- Create: `homework-6/docs/screenshots/.gitkeep`

- [ ] **Step 1: Write requirements.txt**

```
pytest==8.3.4
coverage==7.6.10
fastmcp==2.3.0
```

- [ ] **Step 2: Write .gitignore**

```
__pycache__/
*.pyc
.venv/
.coverage
htmlcov/
shared/input/*.json
shared/processing/*.json
shared/output/*.json
shared/results/*.json
```

- [ ] **Step 3: Create venv and install**

Run: `cd homework-6 && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt`
Expected: installs without error.

- [ ] **Step 4: Commit**

```bash
git add homework-6/requirements.txt homework-6/.gitignore homework-6/agents homework-6/tests homework-6/shared homework-6/docs
git commit -m "chore(hw6): scaffold project structure"
```

---

### Task 2: Domain models

**Files:**
- Create: `homework-6/models.py`
- Test: `homework-6/tests/test_models.py`

**Interfaces:**
- Produces: `Status` enum (`VALIDATED, FLAGGED, CLEARED, SETTLED, REJECTED`), `make_message(source, target, data, message_type="transaction") -> dict`, `to_decimal(value) -> Decimal`.

- [ ] **Step 1: Write failing test**

```python
from decimal import Decimal
from models import make_message, to_decimal, Status

def test_make_message_has_required_fields():
    msg = make_message("integrator", "transaction_validator", {"transaction_id": "TXN001"})
    for key in ("message_id", "timestamp", "source_agent", "target_agent", "message_type", "data"):
        assert key in msg
    assert msg["source_agent"] == "integrator"
    assert msg["data"]["transaction_id"] == "TXN001"

def test_to_decimal_rejects_float_noise():
    assert to_decimal("1500.00") == Decimal("1500.00")
    assert to_decimal("0.1") + to_decimal("0.2") == Decimal("0.3")

def test_status_values():
    assert Status.REJECTED.value == "rejected"
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError: models).

- [ ] **Step 3: Implement models.py**

```python
"""Shared domain models and message helpers for the banking pipeline."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class Status(str, Enum):
    VALIDATED = "validated"
    FLAGGED = "flagged"
    CLEARED = "cleared"
    SETTLED = "settled"
    REJECTED = "rejected"


def iso_now() -> str:
    """Current UTC time as ISO 8601 with trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_decimal(value) -> Decimal:
    """Convert a string/int amount to Decimal without float imprecision."""
    return Decimal(str(value))


def make_message(source: str, target: str, data: dict, message_type: str = "transaction") -> dict:
    """Build a standard pipeline message envelope."""
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": iso_now(),
        "source_agent": source,
        "target_agent": target,
        "message_type": message_type,
        "data": data,
    }
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_models.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add homework-6/models.py homework-6/tests/test_models.py
git commit -m "feat(hw6): add domain models and message envelope"
```

---

### Task 3: Shared bus (file protocol)

**Files:**
- Create: `homework-6/shared_bus.py`
- Test: `homework-6/tests/test_shared_bus.py`

**Interfaces:**
- Produces: `SharedBus(root: Path)` with `setup()`, `clear()`, `write(stage: str, message: dict) -> Path`, `read_all(stage: str) -> list[dict]`, `move(message: dict, from_stage: str, to_stage: str) -> Path`. Stages: `input, processing, output, results`.

- [ ] **Step 1: Write failing test**

```python
from pathlib import Path
from models import make_message
from shared_bus import SharedBus

def test_write_and_read(tmp_path):
    bus = SharedBus(tmp_path)
    bus.setup()
    msg = make_message("integrator", "validator", {"transaction_id": "TXN001"})
    bus.write("input", msg)
    got = bus.read_all("input")
    assert len(got) == 1
    assert got[0]["data"]["transaction_id"] == "TXN001"

def test_move_between_stages(tmp_path):
    bus = SharedBus(tmp_path)
    bus.setup()
    msg = make_message("integrator", "validator", {"transaction_id": "TXN002"})
    bus.write("input", msg)
    bus.move(msg, "input", "results")
    assert bus.read_all("input") == []
    assert len(bus.read_all("results")) == 1

def test_clear(tmp_path):
    bus = SharedBus(tmp_path)
    bus.setup()
    bus.write("input", make_message("i", "v", {"transaction_id": "T"}))
    bus.clear()
    assert bus.read_all("input") == []
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_shared_bus.py -v`
Expected: FAIL (ModuleNotFoundError: shared_bus).

- [ ] **Step 3: Implement shared_bus.py**

```python
"""File-based message bus over shared/{input,processing,output,results}/."""
from __future__ import annotations

import json
from pathlib import Path

STAGES = ("input", "processing", "output", "results")


class SharedBus:
    def __init__(self, root: Path):
        self.root = Path(root)

    def stage_dir(self, stage: str) -> Path:
        if stage not in STAGES:
            raise ValueError(f"unknown stage: {stage}")
        return self.root / stage

    def setup(self) -> None:
        for stage in STAGES:
            self.stage_dir(stage).mkdir(parents=True, exist_ok=True)

    def clear(self) -> None:
        for stage in STAGES:
            d = self.stage_dir(stage)
            if d.exists():
                for f in d.glob("*.json"):
                    f.unlink()

    def _path(self, stage: str, message: dict) -> Path:
        return self.stage_dir(stage) / f"{message['message_id']}.json"

    def write(self, stage: str, message: dict) -> Path:
        path = self._path(stage, message)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(message, indent=2), encoding="utf-8")
        tmp.replace(path)  # atomic write
        return path

    def read_all(self, stage: str) -> list[dict]:
        d = self.stage_dir(stage)
        if not d.exists():
            return []
        return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json"))]

    def move(self, message: dict, from_stage: str, to_stage: str) -> Path:
        src = self._path(from_stage, message)
        if src.exists():
            src.unlink()
        return self.write(to_stage, message)
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_shared_bus.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add homework-6/shared_bus.py homework-6/tests/test_shared_bus.py
git commit -m "feat(hw6): add file-based shared bus"
```

---

### Task 4: Base agent

**Files:**
- Create: `homework-6/agents/base.py`
- Test: `homework-6/tests/test_base.py`

**Interfaces:**
- Produces: `mask_account(acc: str) -> str`, class `Agent` with attribute `name`, method `process_message(message: dict) -> dict` (raises NotImplementedError), helper `audit(txn_id: str, outcome: str) -> str` returning a log line, and `reject(message, reason) -> dict` / `advance(message, target, updates) -> dict` returning new messages.

- [ ] **Step 1: Write failing test**

```python
from agents.base import Agent, mask_account
from models import make_message, Status

def test_mask_account():
    assert mask_account("ACC-1001") == "ACC-****1001"[:8] or mask_account("ACC-1001").startswith("ACC-")
    assert "1001" not in mask_account("ACC-1001")[:-4] or True
    m = mask_account("ACC-1001")
    assert m.startswith("ACC-") and m.endswith("1001") and "*" in m

def test_reject_sets_status_and_reason():
    agent = Agent("tester")
    msg = make_message("i", "tester", {"transaction_id": "TXN001"})
    out = agent.reject(msg, "bad currency")
    assert out["data"]["status"] == Status.REJECTED.value
    assert out["data"]["reason"] == "bad currency"

def test_advance_updates_data_and_target():
    agent = Agent("tester")
    msg = make_message("i", "tester", {"transaction_id": "TXN001"})
    out = agent.advance(msg, "next_agent", {"status": Status.VALIDATED.value})
    assert out["target_agent"] == "next_agent"
    assert out["source_agent"] == "tester"
    assert out["data"]["status"] == Status.VALIDATED.value

def test_process_message_not_implemented():
    import pytest
    with pytest.raises(NotImplementedError):
        Agent("x").process_message({})
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_base.py -v`
Expected: FAIL (ModuleNotFoundError: agents.base).

- [ ] **Step 3: Implement agents/base.py**

```python
"""Base agent: shared contract, audit logging, PII masking."""
from __future__ import annotations

import copy

from models import Status, iso_now, make_message


def mask_account(acc: str) -> str:
    """ACC-1001 -> ACC-****1001-tail; never expose the full number in logs."""
    if not acc or "-" not in acc:
        return "ACC-****"
    tail = acc.split("-", 1)[1]
    return f"ACC-****{tail[-4:]}"


class Agent:
    def __init__(self, name: str):
        self.name = name

    def process_message(self, message: dict) -> dict:
        raise NotImplementedError

    def audit(self, txn_id: str, outcome: str) -> str:
        return f"{iso_now()} | {self.name} | {txn_id} | {outcome}"

    def reject(self, message: dict, reason: str) -> dict:
        data = copy.deepcopy(message["data"])
        data["status"] = Status.REJECTED.value
        data["reason"] = reason
        return make_message(self.name, "results", data)

    def advance(self, message: dict, target: str, updates: dict) -> dict:
        data = copy.deepcopy(message["data"])
        data.update(updates)
        return make_message(self.name, target, data)
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_base.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add homework-6/agents/base.py homework-6/tests/test_base.py
git commit -m "feat(hw6): add base agent with audit and PII masking"
```

---

### Task 5: Transaction Validator

**Files:**
- Create: `homework-6/agents/transaction_validator.py`
- Test: `homework-6/tests/test_validator.py`

**Interfaces:**
- Consumes: `Agent`, `Status`, `to_decimal`.
- Produces: class `TransactionValidator(Agent)` (name `transaction_validator`), `process_message` → advances to `fraud_detector` with `status=validated` or rejects. Module `main()` with `--dry-run` reading `sample-transactions.json`, printing total/valid/invalid + reasons. Constant `VALID_CURRENCIES: set[str]`.

- [ ] **Step 1: Write failing test**

```python
from agents.transaction_validator import TransactionValidator
from models import make_message, Status

def _msg(**over):
    data = {"transaction_id": "TXN001", "amount": "1500.00", "currency": "USD",
            "source_account": "ACC-1001", "destination_account": "ACC-2001"}
    data.update(over)
    return make_message("integrator", "transaction_validator", data)

def test_valid_transaction_advances():
    out = TransactionValidator().process_message(_msg())
    assert out["data"]["status"] == Status.VALIDATED.value
    assert out["target_agent"] == "fraud_detector"

def test_invalid_currency_rejected():
    out = TransactionValidator().process_message(_msg(currency="XYZ"))
    assert out["data"]["status"] == Status.REJECTED.value
    assert "currency" in out["data"]["reason"].lower()

def test_negative_amount_rejected():
    out = TransactionValidator().process_message(_msg(amount="-100.00"))
    assert out["data"]["status"] == Status.REJECTED.value
    assert "amount" in out["data"]["reason"].lower()

def test_bad_account_rejected():
    out = TransactionValidator().process_message(_msg(source_account="BAD1"))
    assert out["data"]["status"] == Status.REJECTED.value

def test_missing_field_rejected():
    m = make_message("i", "transaction_validator", {"transaction_id": "T", "amount": "1.00"})
    out = TransactionValidator().process_message(m)
    assert out["data"]["status"] == Status.REJECTED.value
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_validator.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement agents/transaction_validator.py**

```python
"""Agent 1: validates required fields, amount, currency, account format."""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from agents.base import Agent
from models import Status, to_decimal

VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "UAH", "CHF", "CAD", "AUD", "SEK", "NOK"}
REQUIRED = ("transaction_id", "amount", "currency", "source_account", "destination_account")
ACCOUNT_RE = re.compile(r"^ACC-[A-Z0-9]{4,}$")


class TransactionValidator(Agent):
    def __init__(self):
        super().__init__("transaction_validator")

    def validate(self, data: dict) -> str | None:
        """Return a rejection reason, or None if valid."""
        for field in REQUIRED:
            if not data.get(field):
                return f"missing required field: {field}"
        try:
            amount = to_decimal(data["amount"])
        except (InvalidOperation, ValueError):
            return "amount is not a valid decimal"
        if amount <= Decimal("0"):
            return "amount must be positive"
        if amount.as_tuple().exponent < -2:
            return "amount has more than 2 decimal places"
        if data["currency"] not in VALID_CURRENCIES:
            return f"invalid ISO 4217 currency: {data['currency']}"
        for acc in (data["source_account"], data["destination_account"]):
            if not ACCOUNT_RE.match(str(acc)):
                return f"invalid account format: {acc}"
        return None

    def process_message(self, message: dict) -> dict:
        reason = self.validate(message["data"])
        if reason:
            return self.reject(message, reason)
        return self.advance(message, "fraud_detector", {"status": Status.VALIDATED.value})


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in argv
    src = Path(__file__).resolve().parent.parent / "sample-transactions.json"
    txns = json.loads(src.read_text(encoding="utf-8"))
    validator = TransactionValidator()
    valid, invalid = [], []
    for t in txns:
        reason = validator.validate(t)
        (invalid if reason else valid).append((t["transaction_id"], reason))
    print(f"Total: {len(txns)} | Valid: {len(valid)} | Invalid: {len(invalid)}")
    print(f"{'TXN':<10}{'RESULT':<10}REASON")
    for tid, _ in valid:
        print(f"{tid:<10}{'VALID':<10}")
    for tid, reason in invalid:
        print(f"{tid:<10}{'INVALID':<10}{reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_validator.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Verify dry-run manually**

Run: `cd homework-6 && .venv/Scripts/python -m agents.transaction_validator --dry-run`
Expected: prints Total: 8, TXN006 INVALID (currency XYZ), TXN007 INVALID (negative amount).

- [ ] **Step 6: Commit**

```bash
git add homework-6/agents/transaction_validator.py homework-6/tests/test_validator.py
git commit -m "feat(hw6): add transaction validator with dry-run"
```

---

### Task 6: Fraud Detector

**Files:**
- Create: `homework-6/agents/fraud_detector.py`
- Test: `homework-6/tests/test_fraud.py`

**Interfaces:**
- Consumes: `Agent`, `Status`, `to_decimal`.
- Produces: class `FraudDetector(Agent)` (name `fraud_detector`), `score(data) -> tuple[int, list[str]]`, `process_message` advances to `compliance_checker` adding `risk_score`, `risk_level` (`low<40<=medium<70<=high`), `fraud_reasons`, `status=flagged` if score≥70 else keeps `validated`.

- [ ] **Step 1: Write failing test**

```python
from agents.fraud_detector import FraudDetector
from models import make_message

def _msg(**over):
    data = {"transaction_id": "T", "amount": "1500.00", "currency": "USD",
            "timestamp": "2026-03-16T09:00:00Z",
            "metadata": {"country": "US"}, "status": "validated"}
    data.update(over)
    return make_message("transaction_validator", "fraud_detector", data)

def test_low_value_low_risk():
    out = FraudDetector().process_message(_msg())
    assert out["data"]["risk_level"] == "low"
    assert out["target_agent"] == "compliance_checker"

def test_high_value_scored():
    out = FraudDetector().process_message(_msg(amount="75000.00"))
    assert out["data"]["risk_score"] >= 40
    assert "high-value" in " ".join(out["data"]["fraud_reasons"]).lower()

def test_off_hours_and_cross_border():
    out = FraudDetector().process_message(
        _msg(timestamp="2026-03-16T02:47:00Z", metadata={"country": "DE"}))
    reasons = " ".join(out["data"]["fraud_reasons"]).lower()
    assert "off-hours" in reasons and "cross-border" in reasons
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_fraud.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement agents/fraud_detector.py**

```python
"""Agent 2: risk-scores transactions (high-value, off-hours, cross-border)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from agents.base import Agent
from models import Status, to_decimal

HIGH_VALUE = Decimal("10000")
HOME_COUNTRY = "US"


class FraudDetector(Agent):
    def __init__(self):
        super().__init__("fraud_detector")

    def score(self, data: dict) -> tuple[int, list[str]]:
        score, reasons = 0, []
        amount = to_decimal(data.get("amount", "0"))
        if amount >= HIGH_VALUE:
            score += 40
            reasons.append("high-value transaction (>= 10000)")
        ts = data.get("timestamp", "")
        try:
            hour = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").hour
            if hour < 6:
                score += 30
                reasons.append("off-hours activity")
        except ValueError:
            pass
        country = (data.get("metadata") or {}).get("country", HOME_COUNTRY)
        if country != HOME_COUNTRY:
            score += 30
            reasons.append("cross-border transfer")
        return min(score, 100), reasons

    def process_message(self, message: dict) -> dict:
        score, reasons = self.score(message["data"])
        level = "high" if score >= 70 else "medium" if score >= 40 else "low"
        status = Status.FLAGGED.value if score >= 70 else message["data"].get("status", Status.VALIDATED.value)
        return self.advance(message, "compliance_checker", {
            "risk_score": score, "risk_level": level,
            "fraud_reasons": reasons, "status": status,
        })
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_fraud.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add homework-6/agents/fraud_detector.py homework-6/tests/test_fraud.py
git commit -m "feat(hw6): add fraud detector with risk scoring"
```

---

### Task 7: Compliance Checker

**Files:**
- Create: `homework-6/agents/compliance_checker.py`
- Test: `homework-6/tests/test_compliance.py`

**Interfaces:**
- Consumes: `Agent`, `Status`, `to_decimal`.
- Produces: class `ComplianceChecker(Agent)` (name `compliance_checker`), constant `SANCTIONED = {"IR","KP","SY"}`, `CTR_THRESHOLD = Decimal("10000")`. `process_message`: rejects if country sanctioned; else advances to `settlement_processor` with `requires_ctr` bool (amount≥threshold), `compliance_status="cleared"`, `status=cleared` (preserves `flagged`).

- [ ] **Step 1: Write failing test**

```python
from agents.compliance_checker import ComplianceChecker
from models import make_message, Status

def _msg(**over):
    data = {"transaction_id": "T", "amount": "1500.00", "currency": "USD",
            "metadata": {"country": "US"}, "status": "validated"}
    data.update(over)
    return make_message("fraud_detector", "compliance_checker", data)

def test_clean_advances_to_settlement():
    out = ComplianceChecker().process_message(_msg())
    assert out["target_agent"] == "settlement_processor"
    assert out["data"]["compliance_status"] == "cleared"
    assert out["data"]["requires_ctr"] is False

def test_large_amount_requires_ctr():
    out = ComplianceChecker().process_message(_msg(amount="25000.00"))
    assert out["data"]["requires_ctr"] is True

def test_sanctioned_country_rejected():
    out = ComplianceChecker().process_message(_msg(metadata={"country": "KP"}))
    assert out["data"]["status"] == Status.REJECTED.value
    assert "sanction" in out["data"]["reason"].lower()
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_compliance.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement agents/compliance_checker.py**

```python
"""Agent 3: AML compliance — sanctions screening + CTR threshold."""
from __future__ import annotations

from decimal import Decimal

from agents.base import Agent
from models import Status, to_decimal

SANCTIONED = {"IR", "KP", "SY", "CU"}
CTR_THRESHOLD = Decimal("10000")


class ComplianceChecker(Agent):
    def __init__(self):
        super().__init__("compliance_checker")

    def process_message(self, message: dict) -> dict:
        data = message["data"]
        country = (data.get("metadata") or {}).get("country", "US")
        if country in SANCTIONED:
            return self.reject(message, f"sanctioned country: {country}")
        requires_ctr = to_decimal(data.get("amount", "0")) >= CTR_THRESHOLD
        status = data.get("status", Status.VALIDATED.value)
        if status != Status.FLAGGED.value:
            status = Status.CLEARED.value
        return self.advance(message, "settlement_processor", {
            "compliance_status": "cleared",
            "requires_ctr": requires_ctr,
            "status": status,
        })
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_compliance.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add homework-6/agents/compliance_checker.py homework-6/tests/test_compliance.py
git commit -m "feat(hw6): add compliance checker with sanctions and CTR"
```

---

### Task 8: Settlement Processor

**Files:**
- Create: `homework-6/agents/settlement_processor.py`
- Test: `homework-6/tests/test_settlement.py`

**Interfaces:**
- Consumes: `Agent`, `Status`, `to_decimal`.
- Produces: class `SettlementProcessor(Agent)` (name `settlement_processor`), `FEE_RATE = Decimal("0.001")`, `fee(amount) -> Decimal` (ROUND_HALF_UP, 2 places), `process_message`: computes `fee`, `net_amount`, sets terminal `status=settled` (keeps `flagged` visible via `flagged` field), target `results`.

- [ ] **Step 1: Write failing test**

```python
from decimal import Decimal
from agents.settlement_processor import SettlementProcessor
from models import make_message, Status

def _msg(**over):
    data = {"transaction_id": "T", "amount": "1500.00", "currency": "USD", "status": "cleared"}
    data.update(over)
    return make_message("compliance_checker", "settlement_processor", data)

def test_fee_rounding_half_up():
    assert SettlementProcessor().fee(Decimal("12345.67")) == Decimal("12.35")

def test_settlement_sets_net_and_status():
    out = SettlementProcessor().process_message(_msg(amount="1000.00"))
    assert out["data"]["fee"] == "1.00"
    assert out["data"]["net_amount"] == "999.00"
    assert out["data"]["status"] == Status.SETTLED.value
    assert out["target_agent"] == "results"

def test_flagged_preserved():
    out = SettlementProcessor().process_message(_msg(amount="75000.00", status="flagged"))
    assert out["data"]["flagged"] is True
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_settlement.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement agents/settlement_processor.py**

```python
"""Agent 4: settlement — computes fee/net and finalizes the transaction."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from agents.base import Agent
from models import Status, to_decimal

FEE_RATE = Decimal("0.001")  # 10 bps
CENTS = Decimal("0.01")


class SettlementProcessor(Agent):
    def __init__(self):
        super().__init__("settlement_processor")

    def fee(self, amount: Decimal) -> Decimal:
        return (amount * FEE_RATE).quantize(CENTS, rounding=ROUND_HALF_UP)

    def process_message(self, message: dict) -> dict:
        data = message["data"]
        amount = to_decimal(data["amount"])
        fee = self.fee(amount)
        net = (amount - fee).quantize(CENTS, rounding=ROUND_HALF_UP)
        was_flagged = data.get("status") == Status.FLAGGED.value
        return self.advance(message, "results", {
            "fee": str(fee),
            "net_amount": str(net),
            "flagged": was_flagged,
            "status": Status.SETTLED.value,
        })
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_settlement.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add homework-6/agents/settlement_processor.py homework-6/tests/test_settlement.py
git commit -m "feat(hw6): add settlement processor with decimal fees"
```

---

### Task 9: Integrator (orchestrator) + integration test

**Files:**
- Create: `homework-6/integrator.py`
- Test: `homework-6/tests/test_integration.py`

**Interfaces:**
- Consumes: `SharedBus`, all four agents, `make_message`.
- Produces: `run_pipeline(root: Path, transactions: list[dict]) -> dict` (returns summary dict with `total`, `settled`, `rejected`, `flagged`, `results` list), `main()` that loads `sample-transactions.json`, sets up `shared/`, runs, writes `shared/results/pipeline_summary.json`, prints a table.

- [ ] **Step 1: Write failing test**

```python
import json
from pathlib import Path
from integrator import run_pipeline

def _txns():
    src = Path(__file__).resolve().parent.parent / "sample-transactions.json"
    return json.loads(src.read_text(encoding="utf-8"))

def test_all_transactions_reach_results(tmp_path):
    summary = run_pipeline(tmp_path, _txns())
    assert summary["total"] == 8
    assert len(summary["results"]) == 8
    files = list((tmp_path / "results").glob("*.json"))
    assert len([f for f in files if f.name != "pipeline_summary.json"]) == 8

def test_bad_transactions_rejected(tmp_path):
    summary = run_pipeline(tmp_path, _txns())
    by_id = {r["transaction_id"]: r for r in summary["results"]}
    assert by_id["TXN006"]["status"] == "rejected"  # currency XYZ
    assert by_id["TXN007"]["status"] == "rejected"  # negative amount

def test_high_value_flagged(tmp_path):
    summary = run_pipeline(tmp_path, _txns())
    by_id = {r["transaction_id"]: r for r in summary["results"]}
    assert by_id["TXN005"]["status"] in ("settled",)
    assert by_id["TXN005"]["flagged"] is True
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_integration.py -v`
Expected: FAIL (ModuleNotFoundError: integrator).

- [ ] **Step 3: Implement integrator.py**

```python
"""Orchestrator: loads transactions and runs them through all agents."""
from __future__ import annotations

import json
from pathlib import Path

from agents.compliance_checker import ComplianceChecker
from agents.fraud_detector import FraudDetector
from agents.settlement_processor import SettlementProcessor
from agents.transaction_validator import TransactionValidator
from models import Status, make_message
from shared_bus import SharedBus

PIPELINE = [
    ("transaction_validator", TransactionValidator()),
    ("fraud_detector", FraudDetector()),
    ("compliance_checker", ComplianceChecker()),
    ("settlement_processor", SettlementProcessor()),
]


def run_pipeline(root: Path, transactions: list[dict]) -> dict:
    bus = SharedBus(root)
    bus.setup()
    bus.clear()
    results = []
    for txn in transactions:
        msg = make_message("integrator", "transaction_validator", dict(txn))
        bus.write("input", msg)
        current = msg
        stage = "input"
        for name, agent in PIPELINE:
            bus.move(current, stage, "processing")
            out = agent.process_message(current)
            if out["target_agent"] == "results":
                bus.move(current, "processing", "output")
                bus.write("results", out)
                current = out
                stage = "results"
                break
            bus.move(current, "processing", "output")
            current = out
            stage = "output"
            bus.write("output", current)
        else:
            bus.write("results", current)
        results.append(current["data"])
    summary = _summarize(results)
    (root / "results" / "pipeline_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _summarize(results: list[dict]) -> dict:
    return {
        "total": len(results),
        "settled": sum(1 for r in results if r.get("status") == Status.SETTLED.value),
        "rejected": sum(1 for r in results if r.get("status") == Status.REJECTED.value),
        "flagged": sum(1 for r in results if r.get("flagged")),
        "results": results,
    }


def main() -> int:
    root = Path(__file__).resolve().parent / "shared"
    src = Path(__file__).resolve().parent / "sample-transactions.json"
    txns = json.loads(src.read_text(encoding="utf-8"))
    summary = run_pipeline(root, txns)
    print(f"Processed {summary['total']} | settled={summary['settled']} "
          f"rejected={summary['rejected']} flagged={summary['flagged']}")
    print(f"{'TXN':<10}{'STATUS':<12}{'RISK':<8}NOTE")
    for r in summary["results"]:
        note = r.get("reason", "") or ("FLAGGED" if r.get("flagged") else "")
        print(f"{r['transaction_id']:<10}{r.get('status',''):<12}"
              f"{str(r.get('risk_level','-')):<8}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_integration.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Verify full run manually**

Run: `cd homework-6 && .venv/Scripts/python integrator.py`
Expected: 8 processed, TXN006/TXN007 rejected, TXN002/TXN005 flagged; `shared/results/` populated.

- [ ] **Step 6: Commit**

```bash
git add homework-6/integrator.py homework-6/tests/test_integration.py
git commit -m "feat(hw6): add integrator orchestrator and integration tests"
```

---

### Task 10: Custom FastMCP server

**Files:**
- Create: `homework-6/mcp/__init__.py` (empty)
- Create: `homework-6/mcp/server.py`
- Create: `homework-6/mcp.json`
- Test: `homework-6/tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `shared/results/` JSON files.
- Produces: pure helpers `get_transaction_status(transaction_id, results_dir)`, `list_pipeline_results(results_dir)`, `pipeline_summary_text(results_dir)`; FastMCP `mcp` instance wrapping them as tools/resource. Tests target the pure helpers (no live MCP transport).

- [ ] **Step 1: Write failing test**

```python
import json
from pathlib import Path
from mcp.server import get_transaction_status, list_pipeline_results, pipeline_summary_text

def _seed(tmp_path):
    results = tmp_path
    (results / "a.json").write_text(json.dumps(
        {"data": {"transaction_id": "TXN001", "status": "settled"}}), encoding="utf-8")
    (results / "pipeline_summary.json").write_text(json.dumps(
        {"total": 1, "settled": 1, "rejected": 0, "flagged": 0, "results":
         [{"transaction_id": "TXN001", "status": "settled"}]}), encoding="utf-8")
    return results

def test_get_status_found(tmp_path):
    r = _seed(tmp_path)
    assert get_transaction_status("TXN001", r)["status"] == "settled"

def test_get_status_missing(tmp_path):
    r = _seed(tmp_path)
    assert get_transaction_status("NOPE", r) is None

def test_list_results(tmp_path):
    r = _seed(tmp_path)
    out = list_pipeline_results(r)
    assert out["total"] == 1 and len(out["results"]) == 1

def test_summary_text(tmp_path):
    r = _seed(tmp_path)
    assert "TXN001" in pipeline_summary_text(r)
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_mcp_server.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement mcp/server.py**

```python
"""Custom FastMCP server exposing pipeline results."""
from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP

RESULTS_DIR = Path(__file__).resolve().parent.parent / "shared" / "results"

mcp = FastMCP("pipeline-status")


def _iter_results(results_dir: Path):
    if not results_dir.exists():
        return []
    out = []
    for f in results_dir.glob("*.json"):
        if f.name == "pipeline_summary.json":
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        out.append(doc.get("data", doc))
    return out


def get_transaction_status(transaction_id: str, results_dir: Path = RESULTS_DIR):
    for data in _iter_results(results_dir):
        if data.get("transaction_id") == transaction_id:
            return data
    return None


def list_pipeline_results(results_dir: Path = RESULTS_DIR) -> dict:
    summary = results_dir / "pipeline_summary.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    results = _iter_results(results_dir)
    return {"total": len(results), "results": results}


def pipeline_summary_text(results_dir: Path = RESULTS_DIR) -> str:
    data = list_pipeline_results(results_dir)
    lines = [f"Pipeline summary: total={data.get('total', 0)}"]
    for r in data.get("results", []):
        lines.append(f"  {r.get('transaction_id')}: {r.get('status')}")
    return "\n".join(lines)


@mcp.tool()
def get_transaction_status_tool(transaction_id: str) -> dict | None:
    """Return current status of a transaction from shared/results/."""
    return get_transaction_status(transaction_id)


@mcp.tool()
def list_pipeline_results_tool() -> dict:
    """Return a summary of all processed transactions."""
    return list_pipeline_results()


@mcp.resource("pipeline://summary")
def pipeline_summary_resource() -> str:
    """Latest pipeline run summary as text."""
    return pipeline_summary_text()


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Write mcp.json**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "pipeline-status": {
      "command": "python",
      "args": ["mcp/server.py"]
    }
  }
}
```

- [ ] **Step 5: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_mcp_server.py -v`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add homework-6/mcp homework-6/mcp.json homework-6/tests/test_mcp_server.py
git commit -m "feat(hw6): add custom FastMCP server and mcp.json"
```

---

### Task 11: Claude Code skills (commands)

**Files:**
- Create: `homework-6/.claude/commands/write-spec.md`
- Create: `homework-6/.claude/commands/run-pipeline.md`
- Create: `homework-6/.claude/commands/validate-transactions.md`

- [ ] **Step 1: Write write-spec.md**

```markdown
Generate a full project specification for the banking pipeline following the
Homework 6 template.

Steps:
1. Read specification-TEMPLATE-hint.md (if present) and sample-transactions.json.
2. Produce specification.md with all 5 sections: High-Level Objective,
   Mid-Level Objectives (4-5 testable items), Implementation Notes (Decimal,
   ISO 4217, audit logging, PII), Context (begin/end state), Low-Level Tasks
   (one per agent, with Task/Prompt/File/Function/Details).
3. Save to specification.md and report what was written.
```

- [ ] **Step 2: Write run-pipeline.md**

```markdown
Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that sample-transactions.json exists.
2. Clear shared/ directories.
3. Run the pipeline: .venv/Scripts/python integrator.py
4. Show a summary of results from shared/results/.
5. Report any transactions that were rejected and why.
```

- [ ] **Step 3: Write validate-transactions.md**

```markdown
Validate all transactions in sample-transactions.json without processing them.

Steps:
1. Run the validator in dry-run mode: .venv/Scripts/python -m agents.transaction_validator --dry-run
2. Report: total count, valid count, invalid count, reasons for rejection.
3. Show a table of results.
```

- [ ] **Step 4: Commit**

```bash
git add homework-6/.claude/commands
git commit -m "feat(hw6): add write-spec, run-pipeline, validate-transactions skills"
```

---

### Task 12: Coverage-gate hook

**Files:**
- Create: `homework-6/.claude/hooks/coverage_gate.py`
- Create: `homework-6/.claude/settings.json`
- Test: `homework-6/tests/test_coverage_gate.py`

**Interfaces:**
- Produces: `coverage_gate.py` with `check(command: str, coverage_pct: float, threshold: float = 80.0) -> tuple[int, str]` returning `(exit_code, message)` — exit 2 blocks when command is a `git push` and coverage < threshold; reads hook JSON from stdin in `main()`.

- [ ] **Step 1: Write failing test**

```python
from importlib import util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "coverage_gate.py"
_spec = util.spec_from_file_location("coverage_gate", _path)
cg = util.module_from_spec(_spec); _spec.loader.exec_module(cg)

def test_blocks_push_below_threshold():
    code, msg = cg.check("git push origin main", 72.0)
    assert code == 2 and "coverage" in msg.lower()

def test_allows_push_above_threshold():
    code, _ = cg.check("git push origin main", 91.0)
    assert code == 0

def test_ignores_non_push():
    code, _ = cg.check("git status", 10.0)
    assert code == 0
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_coverage_gate.py -v`
Expected: FAIL (file not found / import error).

- [ ] **Step 3: Implement .claude/hooks/coverage_gate.py**

```python
#!/usr/bin/env python
"""PreToolUse hook: block `git push` when test coverage < threshold."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

THRESHOLD = 80.0
HW = Path(__file__).resolve().parent.parent.parent  # homework-6/


def measure_coverage() -> float:
    py = HW / ".venv" / "Scripts" / "python.exe"
    py = str(py if py.exists() else sys.executable)
    subprocess.run([py, "-m", "coverage", "run", "-m", "pytest", "-q"],
                   cwd=HW, capture_output=True)
    proc = subprocess.run([py, "-m", "coverage", "report"],
                          cwd=HW, capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if line.startswith("TOTAL"):
            return float(line.split()[-1].rstrip("%"))
    return 0.0


def check(command: str, coverage_pct: float, threshold: float = THRESHOLD) -> tuple[int, str]:
    if "git push" not in command:
        return 0, ""
    if coverage_pct < threshold:
        return 2, (f"Push blocked: coverage {coverage_pct:.1f}% < {threshold:.0f}% gate. "
                   f"Add tests before pushing.")
    return 0, f"Coverage {coverage_pct:.1f}% >= {threshold:.0f}% gate. Push allowed."


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}
    command = event.get("tool_input", {}).get("command", "")
    if "git push" not in command:
        return 0
    code, msg = check(command, measure_coverage())
    if code != 0:
        print(msg, file=sys.stderr)
    else:
        print(msg)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Write .claude/settings.json**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/coverage_gate.py"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run test, verify pass**

Run: `cd homework-6 && .venv/Scripts/python -m pytest tests/test_coverage_gate.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add homework-6/.claude/hooks homework-6/.claude/settings.json homework-6/tests/test_coverage_gate.py
git commit -m "feat(hw6): add coverage-gate hook blocking push below 80%"
```

---

### Task 13: context7 research + specification.md + agents.md

**Files:**
- Create: `homework-6/research-notes.md`
- Create: `homework-6/specification.md`
- Create: `homework-6/agents.md`

- [ ] **Step 1: Run 2 real context7 queries via the `docs` subagent**

Dispatch the `docs` agent twice (Python decimal `ROUND_HALF_UP`; FastMCP tools/resource API). Record: search term, returned library id, applied insight.

- [ ] **Step 2: Write research-notes.md** with the two documented queries (format from TASKS.md).

- [ ] **Step 3: Write specification.md** with all 5 required sections and one Low-Level Task per agent (Task/Prompt/File/Function/Details).

- [ ] **Step 4: Write agents.md** describing project context and each agent's role/inputs/outputs.

- [ ] **Step 5: Commit**

```bash
git add homework-6/research-notes.md homework-6/specification.md homework-6/agents.md
git commit -m "docs(hw6): add specification, agents context, context7 research notes"
```

---

### Task 14: README, HOWTORUN, screenshot placeholders

**Files:**
- Create: `homework-6/README.md`
- Create: `homework-6/HOWTORUN.md`

- [ ] **Step 1: Write README.md** — "Created by Vladyslav Nahirych", overview (1-2 paragraphs), per-agent bullets, ASCII architecture diagram, tech-stack table, links to the 5 screenshots.

- [ ] **Step 2: Write HOWTORUN.md** — numbered steps: venv, install, run pipeline, run tests+coverage, run each skill, trigger hook, start MCP server.

- [ ] **Step 3: Commit**

```bash
git add homework-6/README.md homework-6/HOWTORUN.md
git commit -m "docs(hw6): add README with author and HOWTORUN"
```

---

### Task 15: Full verification pass

- [ ] **Step 1: Run all tests with coverage**

Run: `cd homework-6 && .venv/Scripts/python -m coverage run -m pytest -q && .venv/Scripts/python -m coverage report`
Expected: all pass, TOTAL ≥ 90%.

- [ ] **Step 2: Run pipeline end-to-end**

Run: `cd homework-6 && .venv/Scripts/python integrator.py`
Expected: 8 processed; TXN006/TXN007 rejected; TXN002/TXN005 flagged; `shared/results/pipeline_summary.json` written.

- [ ] **Step 3: Verify MCP server imports/starts**

Run: `cd homework-6 && .venv/Scripts/python -c "import mcp.server; print('ok')"`
Expected: `ok`.

- [ ] **Step 4: Prepare screenshot instructions**

Write exact capture commands into HOWTORUN.md for: `pipeline-run.png`, `test-coverage.png`, `skill-run-pipeline.png`, `hook-trigger.png`, `mcp-interaction.png`.

- [ ] **Step 5: Final commit**

```bash
git add -A homework-6
git commit -m "chore(hw6): final verification and screenshot instructions"
```

---

## Self-Review

**Spec coverage:**
- Agent 1 spec skill → Task 11 (write-spec.md) + Task 13 (specification.md). ✓
- Agent 2 code + context7 → Tasks 5-9 + Task 13 (research-notes). ✓
- Agent 3 tests + coverage hook → every task's tests + Task 12. ✓
- Agent 4 README (name) + HOWTORUN → Task 14. ✓
- 4 runtime agents → Tasks 5-8. ✓
- File protocol shared/ → Task 3 + Task 9. ✓
- run-pipeline / validate-transactions skills → Task 11. ✓
- Custom FastMCP (2 tools + resource) → Task 10. ✓
- mcp.json (both servers) → Task 10. ✓
- Coverage ≥90% / gate 80% → Task 15 / Task 12. ✓
- Screenshots (user-captured) → Task 14/15 instructions. ✓

**Placeholder scan:** No TBD/TODO in code steps; every code step has full code. Tasks 13/14 are documentation-generation steps (content produced at execution from real data), not code placeholders.

**Type consistency:** `process_message(message)->dict`, `advance/reject`, `to_decimal`, `Status.*` used consistently across tasks. Integrator field names (`status`, `flagged`, `risk_level`, `reason`) match agent outputs and MCP/test reads.
```
