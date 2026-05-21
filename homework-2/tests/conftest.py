import sys
import os
import pytest
from fastapi.testclient import TestClient

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app
from storage import storage


@pytest.fixture(autouse=True)
def clear_storage():
    """Reset in-memory storage before each test."""
    storage.clear()
    yield
    storage.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_ticket_payload():
    return {
        "customer_id": "CUST-001",
        "customer_email": "test@example.com",
        "customer_name": "Test User",
        "subject": "Cannot login to account",
        "description": "I have been unable to login for the past two days. Password reset doesn't help.",
        "category": "account_access",
        "priority": "high",
        "metadata": {"source": "web_form", "browser": "Chrome", "device_type": "desktop"},
    }
