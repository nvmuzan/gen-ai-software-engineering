# Research Notes — context7 Queries

> Author: Vladyslav Nahirych · Homework 6

Documentation lookups made with the **context7 MCP server** while building the
pipeline (Agent 2 / code generation). Each entry records the search, the library
ID context7 returned, and the insight applied.

---

## Query 1: Decimal / monetary rounding

- **Search:** "decimal module: quantize with ROUND_HALF_UP to round monetary
  amounts to two decimal places"
- **context7 library ID:** `/python/cpython`
  (resolved from `libraryName: CPython`; High reputation, 47.9k snippets)
- **What context7 returned:** the `decimal.rst` docs for `Decimal.quantize(exp,
  rounding=None, context=None)` and the `ROUND_HALF_UP` rounding mode
  ("round to nearest with ties going away from zero"), including the pattern of
  quantizing to a fixed exponent for monetary use, e.g.
  `Decimal('7.325').quantize(Decimal('.01'), rounding=ROUND_DOWN)`.
- **Applied:** in `agents/settlement_processor.py` the fee and net amount are
  computed as `Decimal` and rounded to cents with
  `(amount * FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
  This gives banker-safe, deterministic two-place rounding and avoids the
  imprecision of `float`. The same `quantize`-to-exponent idea also backs the
  validator's "≤ 2 decimal places" check (`amount.as_tuple().exponent >= -2`).

---

## Query 2: FastMCP tools, resources, and running the server

- **Search:** "define a tool with @mcp.tool() decorator, a resource with
  @mcp.resource() URI, and run the server"
- **context7 library ID:** `/prefecthq/fastmcp`
  (resolved from `libraryName: FastMCP`; High reputation, benchmark 85.5)
- **What context7 returned:** the FastMCP server docs showing
  `mcp = FastMCP("MyServer")`, tool registration via `@mcp.tool`, resource
  registration via `@mcp.resource("resource://greeting")`, and running the
  server under an `if __name__ == "__main__": mcp.run()` guard ("ensures
  compatibility when launched as a subprocess").
- **Applied:** `mcp/server.py` builds a `FastMCP("pipeline-status")` server and
  registers `get_transaction_status` and `list_pipeline_results` as tools plus
  a `pipeline://summary` resource, then exposes `mcp.run()` under the
  `__main__` guard — matching the subprocess-launch pattern used by the
  `pipeline-status` entry in `mcp.json`. (Implementation note: fastmcp depends
  on the installed `mcp` SDK, which the local `mcp/` package would shadow under
  pytest, so the `from fastmcp import FastMCP` import is deferred into
  `build_server()` — the pure result-reading helpers stay import-safe for the
  unit tests.)
