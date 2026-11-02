---
name: mlflow-lifecycle
description: Track, register, promote, and roll back models with MLflow using the project's conventions - runs tagged with git SHA and config, one registered model, @challenger/@champion/@previous-champion aliases, champion-vs-challenger gates overall and per slice, human-approved promotion. Use when training, comparing, promoting, or rolling back models, or when querying past runs. Not for GenAI tracing/LLM evaluation (install the official mlflow/skills for that).
---

# MLflow lifecycle

## Conventions
- Tracking URI and experiment come from `configs/base.yaml → mlflow` (local default `sqlite:///mlflow.db`; use a shared server for teams). Never hard-code them.
- Every run goes through `tracking.start_run(...)`: tags `git_sha`, `config`, `stage` (train/tune/eval); params = flattened config.
- One registered model per project (`mlflow.registered_model`). Versions are immutable; **aliases** express state:
  - `@challenger` — passed the promotion gate, awaiting human approval
  - `@champion` — what serves; load with `models:/<name>@champion`
  - `@previous-champion` — rollback target
- Version tags record valid metrics and `promotion_check=pass|fail`.

## Commands
| Step | Command |
|---|---|
| Tune (train-split CV, logged) | `make tune` → `configs/experiments/tuned.yaml` |
| Train + register new version | `make train [CONFIG=...]` |
| Champion/challenger gate | `make promote [VERSION=N]` → sets `@challenger` on pass |
| Promote (human approval) | `make promote APPROVE=1` |
| Roll back | `make rollback` |
| Browse runs | `make mlflow-ui`, or the `mlflow-mcp` server in `.mcp.json` from your agent |

## Rules
- The gate compares candidate vs champion on the same validation split, overall **and per slice** (`promotion.slice_column`), using `configs/gates.json` tolerances. A failing candidate is never aliased.
- `APPROVE=1`, `rollback`, and changing gates are human decisions — ask first.
- To query runs from the agent, prefer the MLflow MCP server (`search` tools) or `mlflow.search_runs(...)` over reading the SQLite file.

## Further
Official MLflow skills (tracing, GenAI evaluation, trace analysis): `npx skills add mlflow/skills` or clone https://github.com/mlflow/skills into `.agents/skills/`.
