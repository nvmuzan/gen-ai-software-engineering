from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import List, Tuple

from pydantic import ValidationError

from models import Ticket, TicketCreate


def _build_ticket(data: dict) -> Tuple[Ticket | None, str | None]:
    try:
        tc = TicketCreate(**data)
        ticket = Ticket(**tc.model_dump(exclude={"auto_classify"}))
        return ticket, None
    except (ValidationError, Exception) as exc:
        return None, str(exc)


def import_json(content: bytes) -> Tuple[List[Ticket], List[dict]]:
    tickets, errors = [], []
    try:
        records = json.loads(content)
    except json.JSONDecodeError as exc:
        return [], [{"row": "N/A", "error": f"Invalid JSON: {exc}"}]

    if not isinstance(records, list):
        return [], [{"row": "N/A", "error": "JSON root must be an array"}]

    for idx, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append({"row": idx, "error": "Each record must be a JSON object"})
            continue
        ticket, err = _build_ticket(record)
        if ticket:
            tickets.append(ticket)
        else:
            errors.append({"row": idx, "error": err})

    return tickets, errors


def import_csv(content: bytes) -> Tuple[List[Ticket], List[dict]]:
    tickets, errors = [], []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return [], [{"row": "N/A", "error": "File must be UTF-8 encoded"}]

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return [], [{"row": "N/A", "error": "CSV file is empty or has no header"}]

    for idx, row in enumerate(reader, start=2):
        data = {k: (v.strip() if v else v) for k, v in row.items() if k}
        # CSV has no nested structures; handle tags and metadata as JSON strings
        if "tags" in data and data["tags"]:
            try:
                data["tags"] = json.loads(data["tags"])
            except (json.JSONDecodeError, TypeError):
                data["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]
        if "metadata" in data and data["metadata"]:
            try:
                data["metadata"] = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        ticket, err = _build_ticket(data)
        if ticket:
            tickets.append(ticket)
        else:
            errors.append({"row": idx, "error": err})

    return tickets, errors


def import_xml(content: bytes) -> Tuple[List[Ticket], List[dict]]:
    tickets, errors = [], []
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return [], [{"row": "N/A", "error": f"Invalid XML: {exc}"}]

    ticket_elements = root.findall("ticket") or (
        [root] if root.tag == "ticket" else []
    )

    for idx, elem in enumerate(ticket_elements, start=1):
        data: dict = {}
        for child in elem:
            if len(child):
                # nested element (metadata, tags)
                if child.tag == "tags":
                    data["tags"] = [t.text for t in child if t.text]
                elif child.tag == "metadata":
                    data["metadata"] = {c.tag: c.text for c in child}
            else:
                data[child.tag] = child.text
        ticket, err = _build_ticket(data)
        if ticket:
            tickets.append(ticket)
        else:
            errors.append({"row": idx, "error": err})

    return tickets, errors
