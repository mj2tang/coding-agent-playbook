---
name: production-monitoring
description: Monitor a deployed model's inputs and quality - per-feature drift (KS/chi-squared or Wasserstein/Jensen-Shannon by sample size, plus PSI), dataset drift share, staleness, and performance drop - and turn them into an explicit retrain/rollback recommendation (make monitor, exit 3 = retrain). Use when checking a scoring batch, investigating a production metric drop, or setting up continuous training. Not for offline model comparison (use mlflow-lifecycle) or first-pass EDA.
---

# Production monitoring and retraining

1. **Check a batch:** `make monitor CURRENT=path/to/batch.csv` → `reports/monitoring.json`, exit code 3 when retraining is recommended.
   - Small reference (≤ 1000 rows): KS (numeric) / chi-squared (categorical), drift if p ≤ 0.05.
   - Large reference: normalised Wasserstein / Jensen-Shannon, drift if distance ≥ 0.1.
   - Dataset drift when ≥ 50% of features drift; PSI reported (0.1 watch, 0.25 act).
   - Thresholds: `configs/base.yaml → monitoring`.
2. **Triage before retraining:** is it a pipeline bug (new nulls, unit change, schema change) or real-world change? Bugs → fix data and contracts; don't retrain on broken data.
3. **Retrain policy** (`monitoring/retrain.py`): dataset drift, model older than `max_model_age_days`, or primary metric drop > `max_metric_drop` once labels arrive. Each trigger records a reason.
4. **Continuous training loop:** retrain (`make train`) → gate (`make promote`) → human approval (`APPROVE=1`) → watch the next batches. If quality drops after promotion → `make rollback` (human).
5. **Write up** each incident in `experiments/<date>-monitoring.md`: signal, root cause, action, follow-up tasks (new contract, new slice metric, feature fix).

Scheduled checks: `.github/workflows/monitor.yml` runs `make monitor` on a schedule and opens an issue when retraining is recommended.
