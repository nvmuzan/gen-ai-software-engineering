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
