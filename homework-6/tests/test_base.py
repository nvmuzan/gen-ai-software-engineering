from agents.base import Agent, mask_account
from models import make_message, Status

def test_mask_account():
    m = mask_account("ACC-1001")
    assert m.startswith("ACC-") and m.endswith("1001") and "*" in m
    assert m != "ACC-1001"
    m2 = mask_account("ACC-987654321")
    assert m2 == "ACC-****4321"
    assert "98765" not in m2

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
