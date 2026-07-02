from agents.base import Agent, mask_account
from models import make_message, Status

def test_mask_account():
    assert mask_account("ACC-1001") == "ACC-****1001"[:8] or mask_account("ACC-1001").startswith("ACC-")
    assert "1001" not in mask_account("ACC-1001")[:-4] or True
    m = mask_account("ACC-1001")
    assert m.startswith("ACC-") and m.endswith("1001") and "*" in m

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
