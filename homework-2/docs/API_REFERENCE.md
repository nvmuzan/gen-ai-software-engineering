# API Reference

Base URL: `http://localhost:8000`

---

## Data Models

### Ticket

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID string | Auto-generated |
| `customer_id` | string | Required |
| `customer_email` | email | Required, validated |
| `customer_name` | string | Required |
| `subject` | string 1–200 | Required |
| `description` | string 10–2000 | Required |
| `category` | enum | `account_access`, `technical_issue`, `billing_question`, `feature_request`, `bug_report`, `other` |
| `priority` | enum | `urgent`, `high`, `medium`, `low` |
| `status` | enum | `new`, `in_progress`, `waiting_customer`, `resolved`, `closed` |
| `created_at` | datetime | Auto-set |
| `updated_at` | datetime | Auto-updated |
| `resolved_at` | datetime \| null | Set on resolve/close |
| `assigned_to` | string \| null | Agent name |
| `tags` | string[] | Array of tags |
| `metadata.source` | enum | `web_form`, `email`, `api`, `chat`, `phone` |
| `metadata.browser` | string \| null | Browser name |
| `metadata.device_type` | enum \| null | `desktop`, `mobile`, `tablet` |
| `classification_confidence` | float \| null | 0–1 after auto-classify |

---

## Endpoints

### POST /tickets

Create a new ticket.

**Request body:**
```json
{
  "customer_id": "CUST-001",
  "customer_email": "alice@example.com",
  "customer_name": "Alice",
  "subject": "Cannot login to account",
  "description": "I have been unable to login for the past two days. Password reset does not work.",
  "category": "account_access",
  "priority": "high",
  "auto_classify": false,
  "metadata": {"source": "web_form", "browser": "Chrome", "device_type": "desktop"}
}
```

**Response `201`:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "customer_id": "CUST-001",
  "customer_email": "alice@example.com",
  ...
  "status": "new",
  "created_at": "2024-01-15T10:00:00"
}
```

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"C1","customer_email":"a@b.com","customer_name":"Alice","subject":"Login issue","description":"Cannot login for three days, very frustrating."}'
```

---

### GET /tickets

List all tickets with optional filters.

**Query parameters:** `category`, `priority`, `status`, `assigned_to`

**Response `200`:**
```json
{"total": 2, "tickets": [...]}
```

```bash
curl "http://localhost:8000/tickets?category=billing_question&priority=urgent"
```

---

### GET /tickets/{id}

Get a single ticket.

**Response `200`:** Ticket object  
**Response `404`:** `{"detail": "Ticket {id} not found"}`

```bash
curl http://localhost:8000/tickets/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

---

### PUT /tickets/{id}

Update ticket fields (partial update — only send fields to change).

**Request body (any subset):**
```json
{"status": "resolved", "assigned_to": "agent1"}
```

**Response `200`:** Updated ticket  
**Response `404`:** Not found

```bash
curl -X PUT http://localhost:8000/tickets/{id} \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

---

### DELETE /tickets/{id}

Delete a ticket.

**Response `204`:** No content  
**Response `404`:** Not found

```bash
curl -X DELETE http://localhost:8000/tickets/{id}
```

---

### POST /tickets/import

Bulk import from file. Supported formats: `.csv`, `.json`, `.xml`.

**Request:** `multipart/form-data` with field `file`

**Response `200`:**
```json
{
  "total": 52,
  "successful": 50,
  "failed": 2,
  "errors": [
    {"row": 3, "error": "value is not a valid email address"},
    {"row": 17, "error": "String should have at least 10 characters"}
  ],
  "tickets": [...]
}
```

```bash
curl -X POST http://localhost:8000/tickets/import \
  -F "file=@sample_tickets.json"
```

---

### POST /tickets/{id}/auto-classify

Run classification on a ticket and optionally apply the result.

**Query:** `override=true` — force overwrite even if already classified

**Response `200`:**
```json
{
  "ticket_id": "3fa85f64-...",
  "category": "account_access",
  "priority": "urgent",
  "confidence": 0.87,
  "reasoning": "Category 'account_access' matched keywords: login, password. Priority 'urgent' matched keywords: can't access.",
  "keywords_found": ["login", "password", "can't access"]
}
```

```bash
curl -X POST "http://localhost:8000/tickets/{id}/auto-classify?override=true"
```

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Bad request (unsupported file format) |
| 404 | Ticket not found |
| 422 | Validation error (body) |

**422 Example:**
```json
{
  "detail": [
    {"loc": ["body", "customer_email"], "msg": "value is not a valid email address", "type": "value_error.email"}
  ]
}
```
