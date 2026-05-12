from fastapi import APIRouter, HTTPException, Query, Request

from src import storage
from src.limiter import limiter
from src.models import TransactionStatus, TransactionType

router = APIRouter()


def _compute_balance(account_id: str) -> float:
    balance = 0.0
    for t in storage.get_all():
        if t.status != TransactionStatus.completed:
            continue
        if t.type == TransactionType.deposit and t.toAccount == account_id:
            balance += t.amount
        elif t.type == TransactionType.withdrawal and t.fromAccount == account_id:
            balance -= t.amount
        elif t.type == TransactionType.transfer:
            if t.toAccount == account_id:
                balance += t.amount
            if t.fromAccount == account_id:
                balance -= t.amount
    return round(balance, 2)


@router.get("/accounts/{account_id}/balance")
@limiter.limit("100/minute")
async def get_balance(request: Request, account_id: str):
    balance = _compute_balance(account_id)
    return {"accountId": account_id, "balance": balance}


@router.get("/accounts/{account_id}/summary")
@limiter.limit("100/minute")
async def get_summary(request: Request, account_id: str):
    transactions = [
        t for t in storage.get_all()
        if t.fromAccount == account_id or t.toAccount == account_id
    ]
    if not transactions:
        return {
            "accountId": account_id,
            "totalDeposits": 0.0,
            "totalWithdrawals": 0.0,
            "transactionCount": 0,
            "lastTransactionDate": None,
        }

    total_deposits = sum(
        t.amount for t in transactions
        if t.type == TransactionType.deposit
        and t.toAccount == account_id
        and t.status == TransactionStatus.completed
    )
    total_withdrawals = sum(
        t.amount for t in transactions
        if t.type == TransactionType.withdrawal
        and t.fromAccount == account_id
        and t.status == TransactionStatus.completed
    )
    last_date = max(t.timestamp for t in transactions)

    return {
        "accountId": account_id,
        "totalDeposits": round(total_deposits, 2),
        "totalWithdrawals": round(total_withdrawals, 2),
        "transactionCount": len(transactions),
        "lastTransactionDate": last_date.isoformat(),
    }


@router.get("/accounts/{account_id}/interest")
@limiter.limit("100/minute")
async def get_interest(
    request: Request,
    account_id: str,
    rate: float = Query(..., gt=0, le=1, description="Annual interest rate (e.g. 0.05 for 5%)"),
    days: int = Query(..., gt=0, description="Number of days to calculate interest for"),
):
    balance = _compute_balance(account_id)
    interest = round(balance * rate * days / 365, 2)
    return {
        "accountId": account_id,
        "balance": balance,
        "rate": rate,
        "days": days,
        "interest": interest,
        "projectedBalance": round(balance + interest, 2),
    }
