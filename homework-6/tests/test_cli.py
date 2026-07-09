"""Coverage for CLI entry points and MCP helper edge branches."""
import io
from contextlib import redirect_stdout

from mcp.server import list_pipeline_results, get_transaction_status


def test_validator_main_dry_run_reports():
    from agents import transaction_validator as tv
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = tv.main(["--dry-run"])
    out = buf.getvalue()
    assert rc == 0
    assert "Total: 8" in out
    assert "TXN006" in out and "TXN007" in out


def test_validator_main_no_args_still_reports():
    from agents import transaction_validator as tv
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = tv.main([])
    assert rc == 0
    assert "Total: 8" in buf.getvalue()


def test_integrator_main_runs_end_to_end():
    import integrator
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = integrator.main()
    out = buf.getvalue()
    assert rc == 0
    assert "Processed 8" in out
    assert "TXN006" in out and "TXN007" in out


def test_list_pipeline_results_without_summary_file(tmp_path):
    (tmp_path / "a.json").write_text(
        '{"data": {"transaction_id": "T1", "status": "settled"}}', encoding="utf-8")
    out = list_pipeline_results(tmp_path)
    assert out["total"] == 1
    assert out["results"][0]["transaction_id"] == "T1"


def test_iter_results_missing_dir_is_empty(tmp_path):
    out = list_pipeline_results(tmp_path / "does-not-exist")
    assert out["total"] == 0
    assert get_transaction_status("T1", tmp_path / "does-not-exist") is None
