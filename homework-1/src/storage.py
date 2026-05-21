from typing import Dict, List, Optional

from src.models import Transaction

_store: Dict[str, Transaction] = {}


def add_transaction(transaction: Transaction) -> Transaction:
    _store[transaction.id] = transaction
    return transaction


def get_all() -> List[Transaction]:
    return list(_store.values())


def get_by_id(tid: str) -> Optional[Transaction]:
    return _store.get(tid)
