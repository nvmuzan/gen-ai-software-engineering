# Banking Transactions API

> **Student Name**: Vladyslav Nahirych
> **Date Submitted**: 2026-05-12
> **AI Tools Used**: Claude Code

---

## Project Overview

A minimal REST API for banking transactions built with **FastAPI** (Python).
All data is stored in-memory — no database required.

---

## Features Implemented

| Task | Status | Description |
|------|--------|-------------|
| Task 1 | Done | Core CRUD endpoints + account balance |
| Task 2 | Done | Amount/account/currency validation |
| Task 3 | Done | Transaction filtering (account, type, date range) |
| Task 4-A | Done | Account summary endpoint |
| Task 4-B | Done | Simple interest calculation |
| Task 4-C | Done | CSV export |
| Task 4-D | Done | Rate limiting (100 req/min per IP) |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create a new transaction |
| `GET` | `/transactions` | List all transactions (supports filters) |
| `GET` | `/transactions/export?format=csv` | Export transactions as CSV |
| `GET` | `/transactions/{id}` | Get a specific transaction by ID |
| `GET` | `/accounts/{accountId}/balance` | Get account balance |
| `GET` | `/accounts/{accountId}/summary` | Get account summary (Task 4-A) |
| `GET` | `/accounts/{accountId}/interest?rate=0.05&days=30` | Calculate interest (Task 4-B) |

Interactive Swagger docs: `http://localhost:3000/docs`

---

## Transaction Filters (`GET /transactions`)

| Query Param | Example | Description |
|-------------|---------|-------------|
| `accountId` | `?accountId=ACC-12345` | Filter by account (from or to) |
| `type` | `?type=transfer` | Filter by type: deposit / withdrawal / transfer |
| `from` | `?from=2024-01-01` | Filter by start date (ISO 8601) |
| `to` | `?to=2024-01-31` | Filter by end date (ISO 8601) |

---

## Validation Rules

- **Amount**: positive number, max 2 decimal places
- **Account**: format `ACC-XXXXX` where X is uppercase alphanumeric (e.g. `ACC-12345`)
- **Currency**: valid ISO 4217 code (USD, EUR, GBP, JPY, UAH, etc.)
- **Rate limiting**: 100 requests per minute per IP — returns `429` when exceeded

---

## Architecture

```
homework-1/
├── src/
│   ├── app.py          # FastAPI app + rate limiting setup
│   ├── models.py       # Pydantic models (Transaction, enums)
│   ├── storage.py      # In-memory storage (module-level dict)
│   ├── validators.py   # Amount / account / currency validation
│   ├── limiter.py      # slowapi rate limiter
│   └── routes/
│       ├── transactions.py  # /transactions endpoints + CSV export
│       └── accounts.py      # /accounts endpoints (balance, summary, interest)
├── demo/
│   ├── run.bat              # Windows start script
│   ├── run.sh               # Unix start script
│   ├── sample-requests.http # VS Code REST Client test requests
│   └── sample-data.json     # Sample transaction payloads
├── requirements.txt
└── .gitignore
```

---

*This project was completed as part of the AI-Assisted Development course.*
