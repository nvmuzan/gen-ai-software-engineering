import csv
import io
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from src import storage
from src.limiter import limiter
from src.models import Transaction, TransactionCreate, TransactionStatus
from src.validators import is_valid_account, is_valid_amount_precision, is_valid_currency

router = APIRouter()


def _build_validation_errors(data: TransactionCreate) -> list:
    errors = []
    if data.amount <= 0:
        errors.append({"field": "amount", "message": "Amount must be a positive number"})
    elif not is_valid_amount_precision(data.amount):
        errors.append({"field": "amount", "message": "Amount must have at most 2 decimal places"})
    if not is_valid_account(data.fromAccount):
        errors.append({
            "field": "fromAccount",
            "message": "Account must follow format ACC-XXXXX (uppercase alphanumeric)",
        })
    if not is_valid_account(data.toAccount):
        errors.append({
            "field": "toAccount",
            "message": "Account must follow format ACC-XXXXX (uppercase alphanumeric)",
        })
    if not is_valid_currency(data.currency):
        errors.append({"field": "currency", "message": f"Invalid currency code: {data.currency}"})
    return errors


@router.post("/transactions", status_code=201)
@limiter.limit("100/minute")
async def create_transaction(request: Request, body: TransactionCreate):
    errors = _build_validation_errors(body)
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"error": "Validation failed", "details": errors},
        )
    transaction = Transaction(
        id=str(uuid.uuid4()),
        fromAccount=body.fromAccount,
        toAccount=body.toAccount,
        amount=body.amount,
        currency=body.currency.upper(),
        type=body.type,
        timestamp=datetime.utcnow(),
        status=TransactionStatus.completed,
    )
    storage.add_transaction(transaction)
    return transaction


# NOTE: /transactions/export must be registered before /transactions/{id}
# so FastAPI matches the literal path before the parameterized one.
@router.get("/transactions/export")
@limiter.limit("100/minute")
async def export_transactions(
    request: Request,
    format: str = Query("csv"),
):
    if format.lower() != "csv":
        raise HTTPException(
            status_code=400,
            detail={"error": "Unsupported format. Only format=csv is supported"},
        )
    transactions = storage.get_all()
    output = io.StringIO()
    fieldnames = ["id", "fromAccount", "toAccount", "amount", "currency", "type", "timestamp", "status"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for t in transactions:
        writer.writerow({
            "id": t.id,
            "fromAccount": t.fromAccount,
            "toAccount": t.toAccount,
            "amount": t.amount,
            "currency": t.currency,
            "type": t.type.value,
            "timestamp": t.timestamp.isoformat(),
            "status": t.status.value,
        })
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/transactions")
@limiter.limit("100/minute")
async def list_transactions(
    request: Request,
    accountId: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    transactions = storage.get_all()

    if accountId:
        transactions = [
            t for t in transactions
            if t.fromAccount == accountId or t.toAccount == accountId
        ]

    if type:
        transactions = [t for t in transactions if t.type.value == type]

    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            transactions = [t for t in transactions if t.timestamp >= from_dt]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid 'from' date. Use ISO 8601 format, e.g. 2024-01-01"},
            )

    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date).replace(hour=23, minute=59, second=59)
            transactions = [t for t in transactions if t.timestamp <= to_dt]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid 'to' date. Use ISO 8601 format, e.g. 2024-01-31"},
            )

    return transactions


@router.get("/transactions/{transaction_id}")
@limiter.limit("100/minute")
async def get_transaction(request: Request, transaction_id: str):
    transaction = storage.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Transaction '{transaction_id}' not found"},
        )
    return transaction
