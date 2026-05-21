from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from models import Category, Priority, Status, Ticket


class TicketStorage:
    def __init__(self):
        self._tickets: Dict[str, Ticket] = {}

    def create(self, ticket: Ticket) -> Ticket:
        self._tickets[ticket.id] = ticket
        return ticket

    def get(self, ticket_id: str) -> Optional[Ticket]:
        return self._tickets.get(ticket_id)

    def list(
        self,
        category: Optional[Category] = None,
        priority: Optional[Priority] = None,
        status: Optional[Status] = None,
        assigned_to: Optional[str] = None,
    ) -> List[Ticket]:
        tickets = list(self._tickets.values())
        if category:
            tickets = [t for t in tickets if t.category == category]
        if priority:
            tickets = [t for t in tickets if t.priority == priority]
        if status:
            tickets = [t for t in tickets if t.status == status]
        if assigned_to:
            tickets = [t for t in tickets if t.assigned_to == assigned_to]
        return tickets

    def update(self, ticket_id: str, updates: dict) -> Optional[Ticket]:
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return None
        data = ticket.model_dump()
        for key, value in updates.items():
            if value is not None:
                data[key] = value
        data["updated_at"] = datetime.utcnow()
        if updates.get("status") in ("resolved", "closed") and not data.get("resolved_at"):
            data["resolved_at"] = datetime.utcnow()
        updated = Ticket(**data)
        self._tickets[ticket_id] = updated
        return updated

    def delete(self, ticket_id: str) -> bool:
        if ticket_id not in self._tickets:
            return False
        del self._tickets[ticket_id]
        return True

    def count(self) -> int:
        return len(self._tickets)

    def clear(self):
        self._tickets.clear()


storage = TicketStorage()
