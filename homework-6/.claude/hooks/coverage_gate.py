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
