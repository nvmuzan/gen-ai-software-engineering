from agents.compliance_checker import ComplianceChecker
from models import make_message, Status

def _msg(**over):
    data = {"transaction_id": "T", "amount": "1500.00", "currency": "USD",
            "metadata": {"country": "US"}, "status": "validated"}
    data.update(over)
    return make_message("fraud_detector", "compliance_checker", data)

def test_clean_advances_to_settlement():
    out = ComplianceChecker().process_message(_msg())
    assert out["target_agent"] == "settlement_processor"
    assert out["data"]["compliance_status"] == "cleared"
    assert out["data"]["requires_ctr"] is False

def test_large_amount_requires_ctr():
    out = ComplianceChecker().process_message(_msg(amount="25000.00"))
    assert out["data"]["requires_ctr"] is True

def test_sanctioned_country_rejected():
    out = ComplianceChecker().process_message(_msg(metadata={"country": "KP"}))
    assert out["data"]["status"] == Status.REJECTED.value
    assert "sanction" in out["data"]["reason"].lower()
