# End-to-end ML lifecycle (MLOps)

How a scaffolded project automates the path from first look at the data to monitored production, and which command, skill, and agent own each stage.

```
 EDA ─► framing ─► features ─► selection ─► tuning ─► training ─► validation ─► promotion ─► serving ─► monitoring
  │                                                     │  MLflow run + version  │  @challenger   @champion      │
  └──────────────────────────── retraining triggers (drift · staleness · performance drop) ◄──────────────────────┘
```

| Stage | Command | Output | Skill | Agent |
|---|---|---|---|---|
| EDA | `make eda` | `reports/eda.md` (missingness, cardinality, duplicates, target balance, single-feature AUC, leakage/ID flags) | `eda-workflow` | `eda-analyst` |
| Framing | — | `docs/design/<slug>.md` | `ml-design-doc` | `ml-problem-framer` |
| Data contracts | `make data-check` | contract tests | `data-contract` | `data-worker` |
| Feature development | `make check` | tested transforms | `tdd-loop` | `feature-worker` |
| Feature selection | `make select` | `reports/feature_selection.md` (near-constant, leakage, correlated, permutation importance) | `feature-selection` | `eda-analyst`, `experiment-scientist` |
| Tuning | `make tune` | `configs/experiments/tuned.yaml` + MLflow run with CV results | `experiment-protocol` | `experiment-scientist` |
| Training | `make train` | MLflow run + new registered model version | `mlflow-lifecycle` | `feature-worker`, `mlops-engineer` |
| Validation | `make gate` | metrics vs committed baseline, exit 1 on regression | `eval-regression` | `eval-worker`, `supervisor` |
| Promotion | `make promote` → `make promote APPROVE=1` | candidate vs `@champion` overall + per slice → `@challenger` → human-approved `@champion` | `mlflow-lifecycle` | `mlops-engineer`, human |
| Rollback | `make rollback` | `@champion` → `@previous-champion` | `mlflow-lifecycle` | human |
| Monitoring | `make monitor CURRENT=batch.csv` | `reports/monitoring.json`, exit 3 = retrain | `production-monitoring` | `monitoring-analyst` |
| Scheduled checks | `.github/workflows/monitor.yml` | weekly drift check → issue when retraining is recommended | `production-monitoring` | `mlops-engineer` |
| Readiness audit | — | ML Test Score report | `ml-quality-gates` | `ml-production-auditor` |

## Design choices

- **MLflow as the system of record.** Every train/tune run logs params (flattened config), metrics, the model with a signature, and tags (`git_sha`, `config`, `stage`). One registered model per project; state is expressed with **aliases** (`@challenger`, `@champion`, `@previous-champion`), the registry's current recommended mechanism.
- **Two gates, two purposes.** `make gate` protects the *code* (no regression vs the committed baseline on every PR). `make promote` protects *production* (candidate vs the live champion, overall and per slice).
- **Humans approve irreversible state changes.** Agents can register versions and set `@challenger`; moving `@champion`, rolling back, and changing thresholds need a person (`ask` permissions + guard hooks).
- **Drift defaults you can defend.** KS / chi-squared (p ≤ 0.05) for small reference sets, normalised Wasserstein / Jensen-Shannon (≥ 0.1) for large ones, dataset drift at ≥ 50% of features — the same defaults Evidently uses — with PSI alongside. Swap in Evidently, whylogs, or alibi-detect when you need richer reports; keep the exit-code contract.
- **Retraining is a recommendation, not a reflex.** The policy records *why* (drift, age, performance); the monitoring analyst separates pipeline bugs from real change before anyone retrains.
- **Agents can query MLflow directly.** `.mcp.json` registers the official MLflow MCP server (`mlflow mcp run`, `MLFLOW_MCP_TOOLS=all`) so Claude Code can search runs and traces without reading the database file.

## Maturity path (Google's MLOps levels)

| Level | What it means | In the scaffold |
|---|---|---|
| 0 — manual | Notebooks, hand-offs, no monitoring | Avoided from day one: everything is a make target |
| 1 — pipeline automation / continuous training | Automated, reproducible training with data validation, model validation vs production, metadata, retraining triggers | ✅ contracts, `train`/`promote` gates, MLflow metadata, `monitor` + retrain policy, scheduled monitoring workflow |
| 2 — CI/CD for the pipeline | Pipeline code itself built, tested, and deployed automatically | Partly: CI runs check/data-check/gate on every PR. Add deployment of the training pipeline to your orchestrator (Airflow, Kubeflow, Metaflow, ZenML, Databricks Jobs) when you need it |

## Extending

| Need | Swap in | Keep |
|---|---|---|
| Shared tracking | MLflow tracking server / Databricks / SageMaker MLflow (`mlflow.tracking_uri`) | `tracking.start_run` conventions |
| Hyperparameter search | Optuna (log trials to MLflow) | train-split-only CV, write a tuned config |
| Data validation | pandera / Great Expectations | `make data-check` exit code |
| Monitoring reports | Evidently / whylogs / alibi-detect | `make monitor` exit 3 contract |
| Pipelines | Kedro, Metaflow, ZenML, DVC pipelines | make targets as the step interface |
| Feature store | Feast | shared feature code for training and serving |
| GenAI components | Official [mlflow/skills](https://github.com/mlflow/skills) (tracing, evaluation, trace analysis) | `llm-eval-engineer` agent |

## Sources
- MLflow docs: [model registry](https://mlflow.org/docs/latest/ml/model-registry/), [classic evaluation & validation](https://mlflow.org/docs/latest/ml/evaluation/), [MCP server](https://mlflow.org/docs/latest/genai/mcp/); [mlflow/skills](https://github.com/mlflow/skills).
- Google Cloud, [*MLOps: Continuous delivery and automation pipelines in machine learning*](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning).
- Evidently, [data drift method defaults](https://docs.evidentlyai.com/metrics/explainer_drift).
- G. Mohandas, [Made With ML](https://github.com/GokuMohandas/Made-With-ML); DrivenData, [cookiecutter-data-science](https://github.com/drivendataorg/cookiecutter-data-science); Breck et al., *The ML Test Score* (Google).
