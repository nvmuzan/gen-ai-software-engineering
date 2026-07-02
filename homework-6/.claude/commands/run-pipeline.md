Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `sample-transactions.json` exists in the `homework-6/` directory.
2. Clear the `shared/` directories (input, processing, output, results).
3. Run the pipeline: `.venv/Scripts/python integrator.py`
   (on Unix: `.venv/bin/python integrator.py`).
4. Show a summary of results from `shared/results/` — read
   `shared/results/pipeline_summary.json` and report total / settled / rejected /
   flagged counts.
5. Report any transactions that were rejected and the reason for each.
