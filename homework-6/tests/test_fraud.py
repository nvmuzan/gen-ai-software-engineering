from agents.fraud_detector import FraudDetector
from models import make_message

def _msg(**over):
    data = {"transaction_id": "T", "amount": "1500.00", "currency": "USD",
            "timestamp": "2026-03-16T09:00:00Z",
            "metadata": {"country": "US"}, "status": "validated"}
    data.update(over)
    return make_message("transaction_validator", "fraud_detector", data)

def test_low_value_low_risk():
    out = FraudDetector().process_message(_msg())
    assert out["data"]["risk_level"] == "low"
    assert out["target_agent"] == "compliance_checker"

def test_high_value_scored():
    out = FraudDetector().process_message(_msg(amount="75000.00"))
    assert out["data"]["risk_score"] >= 40
    assert "high-value" in " ".join(out["data"]["fraud_reasons"]).lower()

def test_off_hours_and_cross_border():
    out = FraudDetector().process_message(
        _msg(timestamp="2026-03-16T02:47:00Z", metadata={"country": "DE"}))
    reasons = " ".join(out["data"]["fraud_reasons"]).lower()
    assert "off-hours" in reasons and "cross-border" in reasons
