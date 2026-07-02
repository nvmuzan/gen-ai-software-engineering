"""Agent 4: settlement — computes fee/net and finalizes the transaction."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from agents.base import Agent
from models import Status, to_decimal

FEE_RATE = Decimal("0.001")  # 10 bps
CENTS = Decimal("0.01")


class SettlementProcessor(Agent):
    def __init__(self):
        super().__init__("settlement_processor")

    def fee(self, amount: Decimal) -> Decimal:
        return (amount * FEE_RATE).quantize(CENTS, rounding=ROUND_HALF_UP)

    def process_message(self, message: dict) -> dict:
        data = message["data"]
        amount = to_decimal(data["amount"])
        fee = self.fee(amount)
        net = (amount - fee).quantize(CENTS, rounding=ROUND_HALF_UP)
        was_flagged = data.get("status") == Status.FLAGGED.value
        return self.advance(message, "results", {
            "fee": str(fee),
            "net_amount": str(net),
            "flagged": was_flagged,
            "status": Status.SETTLED.value,
        })
