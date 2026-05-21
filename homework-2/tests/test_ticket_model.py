"""Tests for Ticket Pydantic models — 9 tests."""
import pytest
from pydantic import ValidationError

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import Ticket, TicketCreate, TicketUpdate, Category, Priority, Status


def test_ticket_create_valid():
    tc = TicketCreate(
        customer_id="C1",
        customer_email="user@example.com",
        customer_name="Alice",
        subject="Issue with login",
        description="Cannot login for three days now. Very frustrating.",
    )
    assert tc.customer_id == "C1"
    assert tc.status == Status.new


def test_ticket_create_invalid_email():
    with pytest.raises(ValidationError):
        TicketCreate(
            customer_id="C1",
            customer_email="bad-email",
            customer_name="Alice",
            subject="Subject",
            description="Description that is long enough to pass validation",
        )


def test_ticket_subject_too_long():
    with pytest.raises(ValidationError):
        TicketCreate(
            customer_id="C1",
            customer_email="a@b.com",
            customer_name="Alice",
            subject="x" * 201,
            description="Description that is long enough",
        )


def test_ticket_description_too_short():
    with pytest.raises(ValidationError):
        TicketCreate(
            customer_id="C1",
            customer_email="a@b.com",
            customer_name="Alice",
            subject="Subject",
            description="short",
        )


def test_ticket_description_too_long():
    with pytest.raises(ValidationError):
        TicketCreate(
            customer_id="C1",
            customer_email="a@b.com",
            customer_name="Alice",
            subject="Subject",
            description="x" * 2001,
        )


def test_ticket_invalid_category():
    with pytest.raises(ValidationError):
        TicketCreate(
            customer_id="C1",
            customer_email="a@b.com",
            customer_name="Alice",
            subject="Subject",
            description="Long enough description here",
            category="invalid_category",
        )


def test_ticket_has_uuid_id():
    t = Ticket(
        customer_id="C1",
        customer_email="a@b.com",
        customer_name="Alice",
        subject="Subject",
        description="Long enough description",
    )
    import uuid
    uuid.UUID(t.id)  # raises if not valid UUID


def test_ticket_update_partial():
    update = TicketUpdate(status=Status.resolved)
    data = update.model_dump(exclude_none=True)
    assert data == {"status": Status.resolved}


def test_ticket_defaults():
    tc = TicketCreate(
        customer_id="C1",
        customer_email="a@b.com",
        customer_name="Alice",
        subject="Subject",
        description="Long enough description here",
    )
    assert tc.tags == []
    assert tc.auto_classify is False
    assert tc.status == Status.new
