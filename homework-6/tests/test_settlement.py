from decimal import Decimal
from agents.settlement_processor import SettlementProcessor
from models import make_message, Status

def _msg(**over):
    data = {"transaction_id": "T", "amount": "1500.00", "currency": "USD", "status": "cleared"}
    data.update(over)
    return make_message("compliance_checker", "settlement_processor", data)

def test_fee_rounding_half_up():
    assert SettlementProcessor().fee(Decimal("12345.67")) == Decimal("12.35")

def test_settlement_sets_net_and_status():
    out = SettlementProcessor().process_message(_msg(amount="1000.00"))
    assert out["data"]["fee"] == "1.00"
    assert out["data"]["net_amount"] == "999.00"
    assert out["data"]["status"] == Status.SETTLED.value
    assert out["target_agent"] == "results"

def test_flagged_preserved():
    out = SettlementProcessor().process_message(_msg(amount="75000.00", status="flagged"))
    assert out["data"]["flagged"] is True
