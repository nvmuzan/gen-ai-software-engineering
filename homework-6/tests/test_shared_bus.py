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
