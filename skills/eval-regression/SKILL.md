---
name: eval-regression
description: Evaluate a model reproducibly and compare metrics against a committed baseline with per-metric tolerances, failing the gate on regressions. Use when changing models, features, or training code, or when adding new metrics. Not for exploratory experiments - use experiment-protocol.
---

# Evaluation regression gate

- `make eval` runs the evaluation entrypoint and writes `metrics/current.json`:
  `{"metrics": {"roc_auc": 0.873, ...}, "split": "valid", "n": 2000, "seed": 42, "git_sha": "..."}`
- `make gate` runs `scripts/check_metrics.py`, comparing `metrics/current.json` to `metrics/baseline.json` with rules from `configs/gates.json`:
  `{"metrics": {"roc_auc": {"direction": "higher", "tolerance": 0.002}, "log_loss": {"direction": "lower", "tolerance": 0.005}}}`
- **Regression** = worse than baseline by more than tolerance → non-zero exit.
- **Suspicious gain** = better than baseline by more than `suspicious_gain` (if set) → warning: check for leakage before celebrating.
- **Rebaseline** (`make rebaseline`) copies current → baseline. Only with explicit human approval, in its own commit, with the reason in the message.
- Known-answer tests for each metric function live in `tests/evaluation/`.
