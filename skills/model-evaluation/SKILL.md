---
name: model-evaluation
description: Route a model evaluation to the right model-type evaluator (regression, classification, time series forecasting, Bayesian MMM, survival/time-to-event, ranking/CTR) using configs/team.json and the project's task_type, and apply the evaluation rules every type shares - correct split, baselines, champion comparison, slices, and uncertainty. Use when asked to evaluate, compare, or sign off a model. Not for writing metric code (eval-worker) or monitoring production batches (production-monitoring).
---

# Model evaluation

## 1. Route by model type
Read `task_type` in `configs/base.yaml` (or infer it from the target and design doc), then use `configs/team.json → evaluators`:

| task_type | Evaluator agent | Signature checks |
|---|---|---|
| `regression` | `regression-evaluator` | loss consistent with mean/median/quantile target, residual diagnostics, interval coverage |
| `binary_classification` / `multiclass_classification` | `classification-evaluator` | ROC-AUC + PR-AUC, calibration, cost-based threshold |
| `forecasting` | `forecasting-evaluator` | rolling-origin CV, MASE/RMSSE vs seasonal naive, per-horizon and probabilistic scores |
| `bayesian_mmm` | `bayesian-mmm-evaluator` | R-hat/ESS/divergences, predictive checks, baseline + ROI plausibility, lift-test calibration |
| `survival` | `survival-evaluator` | censoring review, Uno's C, time-dependent AUC, IPCW Brier/IBS vs Kaplan–Meier, horizon calibration (ICI), PH checks |
| `ranking` / `ctr` | `ranking-ctr-specialist` | normalized entropy, calibration, position bias, freshness |

## 2. Rules every evaluation follows
- **Split mirrors production:** time-based for anything temporal, grouped when entities repeat; test data touched once.
- **Baselines + champion:** always report a naive baseline and the current `@champion` on the same data.
- **Uncertainty:** bootstrap (or posterior) intervals for the primary metric and for the candidate-minus-champion difference; seed-to-seed spread for training noise.
- **Slices:** segments named in the design doc, plus the tails of the target/score distribution.
- **Read errors:** the worst cases, not just the averages (`error-analyst` for deep dives).
- **Verdict:** PASS / CONCERNS / FAIL (READY / CAVEATS / NOT READY for MMM) with the top three actions, written to `experiments/<date>-eval-<type>.md`.

## 3. Hand-off
The evaluator's verdict goes into the task file's supervisor section; `make gate` and `make promote` still decide merges and promotions mechanically.
