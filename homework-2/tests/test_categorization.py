"""Tests for auto-classification — 10 tests."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from models import Category, Priority, Ticket
from classifier import classify_ticket


def make_ticket(subject: str, description: str) -> Ticket:
    return Ticket(
        customer_id="C1",
        customer_email="a@b.com",
        customer_name="Alice",
        subject=subject,
        description=description,
    )


def test_classify_account_access():
    t = make_ticket("Login issue", "I cannot login, password reset is not working, access denied.")
    result = classify_ticket(t)
    assert result.category == Category.account_access


def test_classify_billing():
    t = make_ticket("Invoice missing", "I haven't received my invoice for the payment I made last month.")
    result = classify_ticket(t)
    assert result.category == Category.billing_question


def test_classify_feature_request():
    t = make_ticket("Feature suggestion", "It would be nice to have dark mode. I'd love this enhancement.")
    result = classify_ticket(t)
    assert result.category == Category.feature_request


def test_classify_bug_report():
    t = make_ticket("Bug found", "Steps to reproduce: click save. Expected: saved. Actual: stack trace shown.")
    result = classify_ticket(t)
    assert result.category == Category.bug_report


def test_classify_technical_issue():
    t = make_ticket("App crashes", "The application crashes every time I open it. Error 500 appears.")
    result = classify_ticket(t)
    assert result.category == Category.technical_issue


def test_classify_other_no_keywords():
    t = make_ticket("Hello there", "I just wanted to say hello to your team today.")
    result = classify_ticket(t)
    assert result.category == Category.other
    assert result.confidence == 0.3


def test_priority_urgent():
    t = make_ticket("Critical problem", "Production down! This is a critical security breach affecting all users.")
    result = classify_ticket(t)
    assert result.priority == Priority.urgent


def test_priority_high():
    t = make_ticket("Important blocker", "This is blocking our team, please handle ASAP.")
    result = classify_ticket(t)
    assert result.priority == Priority.high


def test_priority_low():
    t = make_ticket("Minor suggestion", "This is a minor cosmetic suggestion about button colors.")
    result = classify_ticket(t)
    assert result.priority == Priority.low


def test_confidence_score_range():
    t = make_ticket("Login issue", "Cannot login to my account, password reset not working, credentials invalid.")
    result = classify_ticket(t)
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.keywords_found) > 0


def test_auto_classify_endpoint(client, sample_ticket_payload):
    create_resp = client.post("/tickets", json=sample_ticket_payload)
    ticket_id = create_resp.json()["id"]
    resp = client.post(f"/tickets/{ticket_id}/auto-classify")
    assert resp.status_code == 200
    data = resp.json()
    assert "category" in data
    assert "confidence" in data
    assert "keywords_found" in data
    assert "reasoning" in data
