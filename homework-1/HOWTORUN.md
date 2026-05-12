# How to Run

## Requirements

- Python 3.10+
- pip

---

## Quick Start

1. Navigate to the `homework-1` directory:
   ```bash
   cd homework-1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the server:
   ```bash
   uvicorn src.app:app --reload --port 3000
   ```

4. Open the interactive docs in your browser:
   ```
   http://localhost:3000/docs
   ```

---

## Using Demo Scripts

**Windows:**
```bat
demo\run.bat
```

**Linux / macOS:**
```bash
bash demo/run.sh
```

---

## Testing with VS Code REST Client

Open `demo/sample-requests.http` in VS Code (requires the **REST Client** extension).
Click "Send Request" above any request block.

---

## Testing with curl

```bash
# Create a transfer
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'

# List all transactions
curl http://localhost:3000/transactions

# Get account balance
curl http://localhost:3000/accounts/ACC-67890/balance

# Export CSV
curl "http://localhost:3000/transactions/export?format=csv" -o transactions.csv
```
