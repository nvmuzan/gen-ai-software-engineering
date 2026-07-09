"""Custom FastMCP server exposing pipeline results.

NOTE: this package is named `mcp/` per the assignment. fastmcp depends on the
installed `mcp` SDK, so importing fastmcp at module-import time collides with
this local package whenever the project root is on sys.path (e.g. under
pytest). We therefore import fastmcp lazily inside build_server(), which runs
only when the server is launched via `python mcp/server.py` (the script dir is
on sys.path then, so the real mcp SDK resolves). Unit tests import only the
pure helper functions below and never trigger the fastmcp import.
"""
from __future__ import annotations

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "shared" / "results"


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


def build_server():
    """Construct the FastMCP server. fastmcp is imported here (not at module
    top) to avoid the local `mcp/` package shadowing the installed mcp SDK."""
    from fastmcp import FastMCP

    mcp = FastMCP("pipeline-status")

    @mcp.tool(name="get_transaction_status")
    def get_transaction_status_tool(transaction_id: str) -> dict | None:
        """Return current status of a transaction from shared/results/."""
        return get_transaction_status(transaction_id)

    @mcp.tool(name="list_pipeline_results")
    def list_pipeline_results_tool() -> dict:
        """Return a summary of all processed transactions."""
        return list_pipeline_results()

    @mcp.resource("pipeline://summary")
    def pipeline_summary_resource() -> str:
        """Latest pipeline run summary as text."""
        return pipeline_summary_text()

    return mcp


if __name__ == "__main__":
    build_server().run()
