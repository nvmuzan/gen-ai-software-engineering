from decimal import Decimal
from models import make_message, to_decimal, Status

def test_make_message_has_required_fields():
    msg = make_message("integrator", "transaction_validator", {"transaction_id": "TXN001"})
    for key in ("message_id", "timestamp", "source_agent", "target_agent", "message_type", "data"):
        assert key in msg
    assert msg["source_agent"] == "integrator"
    assert msg["data"]["transaction_id"] == "TXN001"

def test_to_decimal_rejects_float_noise():
    assert to_decimal("1500.00") == Decimal("1500.00")
    assert to_decimal("0.1") + to_decimal("0.2") == Decimal("0.3")

def test_status_values():
    assert Status.REJECTED.value == "rejected"
