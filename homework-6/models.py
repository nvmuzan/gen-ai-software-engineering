"""Shared domain models and message helpers for the banking pipeline."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class Status(str, Enum):
    VALIDATED = "validated"
    FLAGGED = "flagged"
    CLEARED = "cleared"
    SETTLED = "settled"
    REJECTED = "rejected"


def iso_now() -> str:
    """Current UTC time as ISO 8601 with trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_decimal(value) -> Decimal:
    """Convert a string/int amount to Decimal without float imprecision."""
    return Decimal(str(value))


def make_message(source: str, target: str, data: dict, message_type: str = "transaction") -> dict:
    """Build a standard pipeline message envelope."""
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": iso_now(),
        "source_agent": source,
        "target_agent": target,
        "message_type": message_type,
        "data": data,
    }
