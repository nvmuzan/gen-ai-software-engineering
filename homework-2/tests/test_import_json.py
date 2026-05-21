"""Tests for JSON import — 5 tests."""
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from importers import import_json

VALID_RECORD = {
    "customer_id": "CUST-1",
    "customer_email": "alice@example.com",
    "customer_name": "Alice",
    "subject": "Login not working",
    "description": "I cannot login for the past two days no matter what I try.",
    "category": "account_access",
    "priority": "high",
    "status": "new",
    "metadata": {"source": "api"},
}


def test_json_valid_import():
    content = json.dumps([VALID_RECORD]).encode()
    tickets, errors = import_json(content)
    assert len(tickets) == 1
    assert len(errors) == 0
    assert tickets[0].customer_email == "alice@example.com"


def test_json_invalid_email():
    bad = {**VALID_RECORD, "customer_email": "not-an-email"}
    content = json.dumps([bad]).encode()
    tickets, errors = import_json(content)
    assert len(errors) == 1
    assert len(tickets) == 0


def test_json_malformed():
    content = b"{not valid json"
    tickets, errors = import_json(content)
    assert len(tickets) == 0
    assert len(errors) == 1
    assert "Invalid JSON" in errors[0]["error"]


def test_json_not_array():
    content = json.dumps(VALID_RECORD).encode()
    tickets, errors = import_json(content)
    assert len(tickets) == 0
    assert "array" in errors[0]["error"]


def test_json_fixture_file():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "sample_tickets.json")
    if not os.path.exists(fixture_path):
        return
    with open(fixture_path, "rb") as f:
        content = f.read()
    tickets, errors = import_json(content)
    assert len(tickets) > 0
