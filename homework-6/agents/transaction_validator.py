"""Agent 1: validates required fields, amount, currency, account format."""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from agents.base import Agent
from models import Status, to_decimal

VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "UAH", "CHF", "CAD", "AUD", "SEK", "NOK"}
REQUIRED = ("transaction_id", "amount", "currency", "source_account", "destination_account")
ACCOUNT_RE = re.compile(r"^ACC-[A-Z0-9]{4,}$")


class TransactionValidator(Agent):
    def __init__(self):
        super().__init__("transaction_validator")

    def validate(self, data: dict) -> str | None:
        """Return a rejection reason, or None if valid."""
        for field in REQUIRED:
            if not data.get(field):
                return f"missing required field: {field}"
        try:
            amount = to_decimal(data["amount"])
        except (InvalidOperation, ValueError):
            return "amount is not a valid decimal"
        if not amount.is_finite():
            return "amount must be a finite number"
        if amount <= Decimal("0"):
            return "amount must be positive"
        if amount.as_tuple().exponent < -2:
            return "amount has more than 2 decimal places"
        if data["currency"] not in VALID_CURRENCIES:
            return f"invalid ISO 4217 currency: {data['currency']}"
        for acc in (data["source_account"], data["destination_account"]):
            if not ACCOUNT_RE.match(str(acc)):
                return f"invalid account format: {acc}"
        return None

    def process_message(self, message: dict) -> dict:
        reason = self.validate(message["data"])
        if reason:
            return self.reject(message, reason)
        return self.advance(message, "fraud_detector", {"status": Status.VALIDATED.value})


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in argv
    src = Path(__file__).resolve().parent.parent / "sample-transactions.json"
    txns = json.loads(src.read_text(encoding="utf-8"))
    validator = TransactionValidator()
    valid, invalid = [], []
    for t in txns:
        reason = validator.validate(t)
        (invalid if reason else valid).append((t["transaction_id"], reason))
    print(f"Total: {len(txns)} | Valid: {len(valid)} | Invalid: {len(invalid)}")
    print(f"{'TXN':<10}{'RESULT':<10}REASON")
    for tid, _ in valid:
        print(f"{tid:<10}{'VALID':<10}")
    for tid, reason in invalid:
        print(f"{tid:<10}{'INVALID':<10}{reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
