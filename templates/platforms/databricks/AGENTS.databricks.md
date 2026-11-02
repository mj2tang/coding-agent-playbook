
## Databricks
- Platform config: `configs/databricks.yaml` (extends `base.yaml`): data from Unity Catalog table `data.table`, MLflow tracking `databricks`, registry `databricks-uc`, model `catalog.schema.<model>` with the same `@challenger`/`@champion`/`@previous-champion` aliases.
- Jobs live in the asset bundle (`databricks.yml`, `resources/*.yml`): `train` (train → promote gate), `monitor` (weekly drift; exit 3 = retrain), `promote_approve` and `rollback` (human-run only).
- Commands: `make bundle-validate`, `make bundle-deploy TARGET=dev`, `make bundle-train`, `make bundle-monitor`. Local runs against Databricks: `make train CONFIG=configs/databricks.yaml` (needs `uv sync --extra databricks` + Databricks Connect).
- Needs human approval: `make bundle-deploy TARGET=prod`, `make bundle-promote-approve`, `make bundle-rollback`, granting UC permissions.
- Agents via Unity Gateway: `ug claude --agent orchestrator`; `RUNNER=ug-claude scripts/agent-team/run-wave.sh ...`; MCP servers and UC skills via `make agents-setup`.
- Never hard-code workspace hosts, tokens, or catalog names in code; they come from bundle variables and `--set` overrides.
