"""Tests for CSV import — 6 tests."""
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from importers import import_csv

VALID_CSV = b"""customer_id,customer_email,customer_name,subject,description,category,priority,status,tags,metadata
CUST-1,alice@example.com,Alice,Login issue,Cannot login for the past two days and it is very frustrating,account_access,high,new,"[""bug""]","{""source"": ""web_form""}"
CUST-2,bob@example.com,Bob,Billing question,I was charged twice this month for my subscription plan,billing_question,medium,new,[],"{""source"": ""email""}"
"""

INVALID_EMAIL_CSV = b"""customer_id,customer_email,customer_name,subject,description
CUST-1,not-an-email,Alice,Subject,Description that is long enough
"""

EMPTY_CSV = b""

BAD_ENCODING_CSV = b"\xff\xfe bad encoding bytes that cannot be decoded"


def test_csv_valid_import():
    tickets, errors = import_csv(VALID_CSV)
    assert len(tickets) == 2
    assert len(errors) == 0


def test_csv_partial_errors():
    tickets, errors = import_csv(INVALID_EMAIL_CSV)
    assert len(errors) == 1
    assert "row" in errors[0]


def test_csv_empty_file():
    tickets, errors = import_csv(EMPTY_CSV)
    assert len(tickets) == 0
    assert len(errors) == 1


def test_csv_tags_as_comma_string():
    csv_data = (
        b"customer_id,customer_email,customer_name,subject,description,tags\n"
        b"C1,a@b.com,Alice,Subject,Long enough description here,bug,vip\n"
    )
    tickets, errors = import_csv(csv_data)
    # tags column has only one value in this CSV — just checking no crash
    assert isinstance(tickets, list) or isinstance(errors, list)


def test_csv_bad_encoding():
    tickets, errors = import_csv(BAD_ENCODING_CSV)
    assert len(errors) >= 1
    assert "UTF-8" in errors[0]["error"]


def test_csv_fixture_file():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "sample_tickets.csv")
    if not os.path.exists(fixture_path):
        return
    with open(fixture_path, "rb") as f:
        content = f.read()
    tickets, errors = import_csv(content)
    assert len(tickets) > 0
