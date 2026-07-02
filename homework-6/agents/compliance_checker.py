"""Agent 3: AML compliance — sanctions screening + CTR threshold."""
from __future__ import annotations

from decimal import Decimal

from agents.base import Agent
from models import Status, to_decimal

SANCTIONED = {"IR", "KP", "SY", "CU"}
CTR_THRESHOLD = Decimal("10000")


class ComplianceChecker(Agent):
    def __init__(self):
        super().__init__("compliance_checker")

    def process_message(self, message: dict) -> dict:
        data = message["data"]
        country = (data.get("metadata") or {}).get("country", "US")
        if country in SANCTIONED:
            return self.reject(message, f"sanctioned country: {country}")
        requires_ctr = to_decimal(data.get("amount", "0")) >= CTR_THRESHOLD
        status = data.get("status", Status.VALIDATED.value)
        if status != Status.FLAGGED.value:
            status = Status.CLEARED.value
        return self.advance(message, "settlement_processor", {
            "compliance_status": "cleared",
            "requires_ctr": requires_ctr,
            "status": status,
        })
