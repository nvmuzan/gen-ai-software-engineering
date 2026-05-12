from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TransactionType(str, Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    transfer = "transfer"


class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class TransactionCreate(BaseModel):
    fromAccount: str
    toAccount: str
    amount: float
    currency: str
    type: TransactionType


class Transaction(BaseModel):
    id: str
    fromAccount: str
    toAccount: str
    amount: float
    currency: str
    type: TransactionType
    timestamp: datetime
    status: TransactionStatus
