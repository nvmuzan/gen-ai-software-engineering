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
