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
