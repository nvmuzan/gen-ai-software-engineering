"""Agent 2: risk-scores transactions (high-value, off-hours, cross-border)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from agents.base import Agent
from models import Status, to_decimal

HIGH_VALUE = Decimal("10000")
HOME_COUNTRY = "US"


class FraudDetector(Agent):
    def __init__(self):
        super().__init__("fraud_detector")

    def score(self, data: dict) -> tuple[int, list[str]]:
        score, reasons = 0, []
        amount = to_decimal(data.get("amount", "0"))
        if amount >= HIGH_VALUE:
            score += 40
            reasons.append("high-value transaction (>= 10000)")
        ts = data.get("timestamp", "")
        try:
            hour = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").hour
            if hour < 6:
                score += 30
                reasons.append("off-hours activity")
        except ValueError:
            pass
        country = (data.get("metadata") or {}).get("country", HOME_COUNTRY)
        if country != HOME_COUNTRY:
            score += 30
            reasons.append("cross-border transfer")
        return min(score, 100), reasons

    def process_message(self, message: dict) -> dict:
        score, reasons = self.score(message["data"])
        level = "high" if score >= 70 else "medium" if score >= 40 else "low"
        status = Status.FLAGGED.value if score >= 40 else message["data"].get("status", Status.VALIDATED.value)
        return self.advance(message, "compliance_checker", {
            "risk_score": score, "risk_level": level,
            "fraud_reasons": reasons, "status": status,
        })
