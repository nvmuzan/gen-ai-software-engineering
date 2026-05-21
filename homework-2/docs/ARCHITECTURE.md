# Architecture

## High-Level Overview

```mermaid
graph TD
    subgraph Client
        C[HTTP Client / curl / frontend]
    end

    subgraph FastAPI App
        R[Route Handlers<br/>main.py]
        V[Pydantic Validation<br/>models.py]
        CL[Classifier<br/>classifier.py]
        IMP[Importers<br/>importers.py]
    end

    subgraph Storage
        S[In-Memory Dict<br/>storage.py]
    end

    C -->|JSON / multipart| R
    R --> V
    R --> S
    R --> CL
    R --> IMP
    IMP --> V
    IMP --> S
    CL --> S
```

## Component Descriptions

| Component | File | Responsibility |
|-----------|------|----------------|
| Route Handlers | `main.py` | HTTP routing, request parsing, response shaping |
| Models | `models.py` | Pydantic schemas, enum validation, field constraints |
| Storage | `storage.py` | In-memory dict CRUD, filtering |
| Classifier | `classifier.py` | Keyword-based category and priority scoring |
| Importers | `importers.py` | CSV / JSON / XML parsing into Ticket objects |

## Data Flow — Ticket Creation with Auto-Classify

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API (main.py)
    participant V as Validator (models.py)
    participant CL as Classifier
    participant S as Storage

    C->>A: POST /tickets {auto_classify: true}
    A->>V: TicketCreate(**payload)
    V-->>A: validated TicketCreate
    A->>A: Ticket(**tc.model_dump())
    A->>CL: classify_ticket(ticket)
    CL-->>A: ClassificationResult
    A->>A: ticket.category = result.category
    A->>S: storage.create(ticket)
    S-->>A: stored Ticket
    A-->>C: 201 Ticket JSON
```

## Data Flow — Bulk Import

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant I as Importer
    participant V as Validator
    participant S as Storage

    C->>A: POST /tickets/import (file)
    A->>I: import_csv/json/xml(content)
    loop per record
        I->>V: TicketCreate(**record)
        V-->>I: valid or error
    end
    I-->>A: (tickets[], errors[])
    loop per valid ticket
        A->>S: storage.create(ticket)
    end
    A-->>C: ImportSummary {total, successful, failed, errors}
```

## Design Decisions

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Storage | In-memory dict | SQLite / PostgreSQL | Simplicity for HW; swap by replacing storage.py |
| Validation | Pydantic v2 | marshmallow | Native FastAPI integration, fast |
| Classification | Keyword rules | LLM / scikit-learn | Zero latency, no external dependencies, deterministic |
| Framework | FastAPI | Flask | Auto-docs, async support, Pydantic-native |

## Security Considerations

- Email validated via Pydantic `EmailStr` — prevents invalid data
- File size not bounded by the API (should add in production via nginx/reverse proxy)
- No authentication — add OAuth2/API keys for production
- XML parser uses `xml.etree.ElementTree` (safe, not vulnerable to XXE by default in Python)

## Performance Characteristics

- All storage operations are O(1) for create/get/delete, O(n) for list/filter
- Classification is O(k) where k = total keyword count (~60 keywords) — effectively constant
- CSV/JSON/XML parsing is O(n) per file
- 1000-ticket list operation completes in <2s (verified by performance tests)
