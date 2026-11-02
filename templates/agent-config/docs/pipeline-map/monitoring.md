# Monitoring and retraining decision

## What it is
`make monitor CURRENT=<batch>` checks drift against the training reference and applies the retrain policy (exit 3 = retrain recommended).

## How to reach it
- `make monitor CURRENT=batch.csv` · scheduled `monitor` workflow/job.

## Evidence that counts
- `reports/monitoring.json` for a real or realistic batch, plus the exit code; for a drift change, one batch that should drift and one that shouldn't.

## What usually lies
- Drift driven by a pipeline bug (unit change, new nulls) reported as real-world change — check drifted columns first.
- Testing only the clean batch — a monitor that never fires looks identical to one that works.
