# Evaluation and gates

## What it is
`make eval` writes `metrics/current.json`; `make gate` compares it to `metrics/baseline.json` under `configs/gates.json`.

## How to reach it
- `make gate` (runs eval first)
- Model-type checks from the evaluator agent for `task_type` (see `model-evaluation` skill).

## Evidence that counts
- The gate table (baseline, candidate, delta, status) and `GATE: PASS`, from a run on this branch's HEAD.
- `metrics/current.json` with `git_sha` matching HEAD.

## What usually lies
- A stale `metrics/current.json` from another branch — rerun, don't reuse.
- "SUSPICIOUS GAIN" treated as success — it's a leakage alarm until explained.
