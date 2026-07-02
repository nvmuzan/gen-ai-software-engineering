from agents.transaction_validator import TransactionValidator
from models import make_message, Status

def _msg(**over):
    data = {"transaction_id": "TXN001", "amount": "1500.00", "currency": "USD",
            "source_account": "ACC-1001", "destination_account": "ACC-2001"}
    data.update(over)
    return make_message("integrator", "transaction_validator", data)

def test_valid_transaction_advances():
    out = TransactionValidator().process_message(_msg())
    assert out["data"]["status"] == Status.VALIDATED.value
    assert out["target_agent"] == "fraud_detector"

def test_invalid_currency_rejected():
    out = TransactionValidator().process_message(_msg(currency="XYZ"))
    assert out["data"]["status"] == Status.REJECTED.value
    assert "currency" in out["data"]["reason"].lower()

def test_negative_amount_rejected():
    out = TransactionValidator().process_message(_msg(amount="-100.00"))
    assert out["data"]["status"] == Status.REJECTED.value
    assert "amount" in out["data"]["reason"].lower()

def test_bad_account_rejected():
    out = TransactionValidator().process_message(_msg(source_account="BAD1"))
    assert out["data"]["status"] == Status.REJECTED.value

def test_missing_field_rejected():
    m = make_message("i", "transaction_validator", {"transaction_id": "T", "amount": "1.00"})
    out = TransactionValidator().process_message(m)
    assert out["data"]["status"] == Status.REJECTED.value
