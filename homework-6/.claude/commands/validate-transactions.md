Validate all transactions in `sample-transactions.json` without processing them
through the full pipeline.

Steps:
1. Run the validator in dry-run mode:
   `.venv/Scripts/python -m agents.transaction_validator --dry-run`
   (on Unix: `.venv/bin/python -m agents.transaction_validator --dry-run`).
2. Report: total count, valid count, invalid count, and the reason for each
   rejection.
3. Show the results as a table (transaction id, result, reason).
