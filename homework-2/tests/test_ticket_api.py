"""Tests for ticket API endpoints — 11 tests."""
import pytest
from fastapi.testclient import TestClient


def test_create_ticket_success(client, sample_ticket_payload):
    resp = client.post("/tickets", json=sample_ticket_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_email"] == "test@example.com"
    assert "id" in data
    assert data["status"] == "new"


def test_create_ticket_auto_classify(client, sample_ticket_payload):
    payload = {**sample_ticket_payload, "auto_classify": True}
    resp = client.post("/tickets", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] is not None
    assert data["priority"] is not None


def test_create_ticket_invalid_email(client, sample_ticket_payload):
    payload = {**sample_ticket_payload, "customer_email": "not-an-email"}
    resp = client.post("/tickets", json=payload)
    assert resp.status_code == 422


def test_create_ticket_missing_required(client):
    resp = client.post("/tickets", json={"customer_id": "X"})
    assert resp.status_code == 422


def test_get_ticket_success(client, sample_ticket_payload):
    create_resp = client.post("/tickets", json=sample_ticket_payload)
    ticket_id = create_resp.json()["id"]
    resp = client.get(f"/tickets/{ticket_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ticket_id


def test_get_ticket_not_found(client):
    resp = client.get("/tickets/nonexistent-id")
    assert resp.status_code == 404


def test_list_tickets(client, sample_ticket_payload):
    client.post("/tickets", json=sample_ticket_payload)
    client.post("/tickets", json=sample_ticket_payload)
    resp = client.get("/tickets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["tickets"]) == 2


def test_list_tickets_filter_by_category(client, sample_ticket_payload):
    client.post("/tickets", json={**sample_ticket_payload, "category": "billing_question"})
    client.post("/tickets", json=sample_ticket_payload)
    resp = client.get("/tickets?category=billing_question")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_update_ticket_success(client, sample_ticket_payload):
    create_resp = client.post("/tickets", json=sample_ticket_payload)
    ticket_id = create_resp.json()["id"]
    resp = client.put(f"/tickets/{ticket_id}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_update_ticket_not_found(client):
    resp = client.put("/tickets/nonexistent", json={"status": "closed"})
    assert resp.status_code == 404


def test_delete_ticket(client, sample_ticket_payload):
    create_resp = client.post("/tickets", json=sample_ticket_payload)
    ticket_id = create_resp.json()["id"]
    del_resp = client.delete(f"/tickets/{ticket_id}")
    assert del_resp.status_code == 204
    get_resp = client.get(f"/tickets/{ticket_id}")
    assert get_resp.status_code == 404
