"""Integration (end-to-end) tests — 5 tests."""
import io
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_full_ticket_lifecycle(client, sample_ticket_payload):
    # Create
    resp = client.post("/tickets", json=sample_ticket_payload)
    assert resp.status_code == 201
    ticket_id = resp.json()["id"]

    # Read
    resp = client.get(f"/tickets/{ticket_id}")
    assert resp.status_code == 200

    # Classify
    resp = client.post(f"/tickets/{ticket_id}/auto-classify")
    assert resp.status_code == 200

    # Update status
    resp = client.put(f"/tickets/{ticket_id}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # Resolve
    resp = client.put(f"/tickets/{ticket_id}", json={"status": "resolved"})
    assert resp.status_code == 200

    # Delete
    resp = client.delete(f"/tickets/{ticket_id}")
    assert resp.status_code == 204

    # Confirm deleted
    resp = client.get(f"/tickets/{ticket_id}")
    assert resp.status_code == 404


def test_bulk_json_import_with_autoclassify(client):
    records = [
        {
            "customer_id": f"CUST-{i}",
            "customer_email": f"user{i}@example.com",
            "customer_name": f"User {i}",
            "subject": "Cannot login to account",
            "description": "I cannot login for the past two days no matter what I try.",
            "auto_classify": True,
        }
        for i in range(5)
    ]
    json_bytes = json.dumps(records).encode()
    resp = client.post(
        "/tickets/import",
        files={"file": ("tickets.json", io.BytesIO(json_bytes), "application/json")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["successful"] == 5
    assert data["failed"] == 0


def test_combined_filter_by_category_and_priority(client, sample_ticket_payload):
    client.post("/tickets", json={**sample_ticket_payload, "category": "billing_question", "priority": "urgent"})
    client.post("/tickets", json={**sample_ticket_payload, "category": "billing_question", "priority": "low"})
    client.post("/tickets", json={**sample_ticket_payload, "category": "technical_issue", "priority": "urgent"})

    resp = client.get("/tickets?category=billing_question&priority=urgent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1


def test_bulk_csv_import(client):
    csv_content = (
        b"customer_id,customer_email,customer_name,subject,description,category,priority,status\n"
        b"C1,a@example.com,Alice,Login issue,Cannot login for the past two days and it is so frustrating,account_access,high,new\n"
        b"C2,b@example.com,Bob,Crash issue,App crashes every time I open it on my desktop computer,technical_issue,urgent,new\n"
    )
    resp = client.post(
        "/tickets/import",
        files={"file": ("tickets.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["successful"] == 2


def test_unsupported_file_format(client):
    resp = client.post(
        "/tickets/import",
        files={"file": ("tickets.txt", io.BytesIO(b"some text"), "text/plain")},
    )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]
