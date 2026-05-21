from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, status
from fastapi.responses import JSONResponse

from classifier import classify_ticket
from importers import import_csv, import_json, import_xml
from models import (
    Category,
    ClassificationResult,
    ImportSummary,
    Priority,
    Status,
    Ticket,
    TicketCreate,
    TicketListResponse,
    TicketUpdate,
)
from storage import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Customer Support Ticket System",
    description="REST API for managing customer support tickets with auto-classification",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Tickets CRUD
# ---------------------------------------------------------------------------

@app.post("/tickets", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate):
    ticket = Ticket(**payload.model_dump(exclude={"auto_classify"}))
    if payload.auto_classify:
        result = classify_ticket(ticket)
        ticket.category = result.category
        ticket.priority = result.priority
        ticket.classification_confidence = result.confidence
    storage.create(ticket)
    return ticket


@app.get("/tickets", response_model=TicketListResponse)
def list_tickets(
    category: Optional[Category] = Query(None),
    priority: Optional[Priority] = Query(None),
    status_filter: Optional[Status] = Query(None, alias="status"),
    assigned_to: Optional[str] = Query(None),
):
    tickets = storage.list(
        category=category,
        priority=priority,
        status=status_filter,
        assigned_to=assigned_to,
    )
    return TicketListResponse(total=len(tickets), tickets=tickets)


@app.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str):
    ticket = storage.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@app.put("/tickets/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: str, payload: TicketUpdate):
    updates = payload.model_dump(exclude_none=True)
    ticket = storage.update(ticket_id, updates)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: str):
    deleted = storage.delete(ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")


# ---------------------------------------------------------------------------
# Auto-classification
# ---------------------------------------------------------------------------

@app.post("/tickets/{ticket_id}/auto-classify", response_model=ClassificationResult)
def auto_classify(ticket_id: str, override: bool = Query(False)):
    ticket = storage.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    result = classify_ticket(ticket)

    # Apply to ticket (always update unless there's already a manual category and override=False)
    if override or ticket.classification_confidence is None:
        storage.update(ticket_id, {
            "category": result.category,
            "priority": result.priority,
            "classification_confidence": result.confidence,
        })

    return result


# ---------------------------------------------------------------------------
# Bulk import
# ---------------------------------------------------------------------------

@app.post("/tickets/import", response_model=ImportSummary, status_code=status.HTTP_200_OK)
async def import_tickets(file: UploadFile = File(...)):
    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".csv"):
        tickets, errors = import_csv(content)
    elif filename.endswith(".json"):
        tickets, errors = import_json(content)
    elif filename.endswith(".xml"):
        tickets, errors = import_xml(content)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Use CSV, JSON, or XML.",
        )

    for ticket in tickets:
        storage.create(ticket)

    return ImportSummary(
        total=len(tickets) + len(errors),
        successful=len(tickets),
        failed=len(errors),
        errors=errors,
        tickets=tickets,
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "tickets_count": storage.count()}
