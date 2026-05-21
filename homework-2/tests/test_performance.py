"""Performance and concurrency tests — 5 tests."""
import io
import json
import time
import threading
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from fastapi.testclient import TestClient
from main import app
from storage import storage


def _make_payload(i: int) -> dict:
    return {
        "customer_id": f"CUST-{i}",
        "customer_email": f"user{i}@example.com",
        "customer_name": f"User {i}",
        "subject": f"Issue number {i}",
        "description": "This is a test description that is long enough to pass validation.",
    }


def test_bulk_create_100_tickets():
    storage.clear()
    client = TestClient(app)
    start = time.time()
    for i in range(100):
        resp = client.post("/tickets", json=_make_payload(i))
        assert resp.status_code == 201
    elapsed = time.time() - start
    assert elapsed < 10, f"100 ticket creates took {elapsed:.2f}s — too slow"
    assert storage.count() == 100
    storage.clear()


def test_concurrent_creates_20_threads():
    storage.clear()
    client = TestClient(app)
    errors = []

    def create(i):
        try:
            resp = client.post("/tickets", json=_make_payload(i))
            if resp.status_code != 201:
                errors.append(resp.status_code)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=create, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent errors: {errors}"
    assert storage.count() == 20
    storage.clear()


def test_bulk_json_import_50_records():
    storage.clear()
    client = TestClient(app)
    records = [_make_payload(i) for i in range(50)]
    json_bytes = json.dumps(records).encode()

    start = time.time()
    resp = client.post(
        "/tickets/import",
        files={"file": ("bulk.json", io.BytesIO(json_bytes), "application/json")},
    )
    elapsed = time.time() - start

    assert resp.status_code == 200
    assert resp.json()["successful"] == 50
    assert elapsed < 5, f"Bulk import of 50 took {elapsed:.2f}s"
    storage.clear()


def test_list_tickets_performance_with_1000():
    storage.clear()
    client = TestClient(app)
    # Bulk-create 1000 tickets via import
    records = [_make_payload(i) for i in range(1000)]
    json_bytes = json.dumps(records).encode()
    client.post(
        "/tickets/import",
        files={"file": ("big.json", io.BytesIO(json_bytes), "application/json")},
    )

    start = time.time()
    resp = client.get("/tickets")
    elapsed = time.time() - start

    assert resp.status_code == 200
    assert resp.json()["total"] == 1000
    assert elapsed < 2, f"List 1000 tickets took {elapsed:.2f}s"
    storage.clear()


def test_classify_performance():
    storage.clear()
    client = TestClient(app)
    payload = _make_payload(0)
    payload["subject"] = "Cannot login to account — production down and critical"
    payload["description"] = "This is a critical security issue. Production is completely down and all users are affected."
    create_resp = client.post("/tickets", json=payload)
    ticket_id = create_resp.json()["id"]

    start = time.time()
    for _ in range(50):
        resp = client.post(f"/tickets/{ticket_id}/auto-classify")
        assert resp.status_code == 200
    elapsed = time.time() - start
    assert elapsed < 3, f"50 classify calls took {elapsed:.2f}s"
    storage.clear()
