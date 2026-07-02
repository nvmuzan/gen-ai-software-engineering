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
