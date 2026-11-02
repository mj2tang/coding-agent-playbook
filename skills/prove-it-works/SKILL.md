---
name: prove-it-works
description: Prove a change works on the real artifact before calling it done - exercise every pipeline-map entry point the change can affect (data, training, evaluation, promotion, scoring, monitoring), capture evidence a skeptical reviewer would accept, and verify delegated work from artifacts, never from the delegate's summary. Use before marking any task done or approving a worker's branch. Not for read-only questions or pure planning.
---

# Prove it works

Passing unit tests and "it compiles" are proxies. Proof means running the real path and reading the real result.

## 1. Pick the coverage set
Read `docs/pipeline-map/README.md`, then every entry-point file your change can affect. Feature or transform code usually touches **training, evaluation, batch scoring, and monitoring** - not just the module under test. Data code adds **data**. Anything touching models adds **promotion**.

## 2. Exercise each entry point
Run the commands in each file's "How to reach it" on this branch's HEAD. Cover the paths the change can affect: success, empty input, bad input (contract violation), and the comparison against the baseline/champion.

## 3. Capture evidence
For each entry point, record what the file's "Evidence that counts" names: the gate table, the MLflow run ID and version, the predictions' row count and score range, the monitoring JSON and exit code. Log one row per entry point:

```
python3 scripts/agent-team/audit.py log verify T-012 feature-worker "ran make gate on HEAD" "covers evaluation" "metrics/current.json" "GATE: PASS"
```

## 4. Check "what usually lies"
Each pipeline-map file lists known false positives (stale `metrics/current.json`, a run from another commit, a monitor that never fires). Rule each one out explicitly.

## 5. Unreachable paths
If an entry point needs production data, credentials, or a deployed endpoint, name it, say what blocks it, and cover the closest real path. Never claim coverage you didn't run.

## Verifying someone else's work
Agents report what they intended, not always what happened. Re-run the gates yourself, open the evidence files, and compare `git_sha`/run IDs to the branch HEAD. A summary without matching artifacts is not proof.

## When the proof can be scripted
Prefer a deterministic script that re-runs the comparison (old vs new predictions, before/after metrics) over a one-time look; the script is the artifact a reviewer re-runs.

Adapted from Lauren Tan's "prove it works" principle and feature-map verification in pstack.
