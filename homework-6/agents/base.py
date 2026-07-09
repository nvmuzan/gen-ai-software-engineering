"""Base agent: shared contract, audit logging, PII masking."""
from __future__ import annotations

import copy

from models import Status, iso_now, make_message


def mask_account(acc: str) -> str:
    """ACC-1001 -> ACC-****1001-tail; never expose the full number in logs."""
    if not acc or "-" not in acc:
        return "ACC-****"
    tail = acc.split("-", 1)[1]
    return f"ACC-****{tail[-4:]}"


class Agent:
    def __init__(self, name: str):
        self.name = name

    def process_message(self, message: dict) -> dict:
        raise NotImplementedError

    def audit(self, txn_id: str, outcome: str) -> str:
        return f"{iso_now()} | {self.name} | {txn_id} | {outcome}"

    def reject(self, message: dict, reason: str) -> dict:
        data = copy.deepcopy(message["data"])
        data["status"] = Status.REJECTED.value
        data["reason"] = reason
        return make_message(self.name, "results", data)

    def advance(self, message: dict, target: str, updates: dict) -> dict:
        data = copy.deepcopy(message["data"])
        data.update(updates)
        return make_message(self.name, target, data)
