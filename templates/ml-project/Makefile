# Quality gates used by humans, agents, and CI. Keep target names stable:
# AGENTS.md, skills, and the supervisor agent refer to them.
PY ?= uv run
CONFIG ?= configs/base.yaml

.PHONY: setup check lint types test data-check eda select tune train eval gate promote rollback monitor runs mlflow-ui rebaseline clean

setup:
	uv sync

check: lint types test

lint:
	$(PY) ruff check src tests scripts
	$(PY) ruff format --check src tests scripts

types:
	$(PY) mypy

test:
	$(PY) pytest -m "not data and not slow"

data-check:
	$(PY) pytest -m data

eda:
	$(PY) python -m {{pkg}}.analysis.eda --config $(CONFIG)

select:
	$(PY) python -m {{pkg}}.features.select_report --config $(CONFIG)

tune:
	$(PY) python -m {{pkg}}.models.tune --config $(CONFIG)

# Trains, logs to MLflow, and registers a new model version (no alias change).
train:
	$(PY) python -m {{pkg}}.models.train --config $(CONFIG)

eval:
	$(PY) python -m {{pkg}}.evaluation.run --config $(CONFIG) --out metrics/current.json

gate: eval
	$(PY) python scripts/check_metrics.py --current metrics/current.json --baseline metrics/baseline.json --rules configs/gates.json

# Champion/challenger check; add APPROVE=1 (human decision) to move @champion.
promote:
	$(PY) python -m {{pkg}}.registry.promote --config $(CONFIG) $(if $(APPROVE),--approve,) $(if $(VERSION),--version $(VERSION),)

rollback:
	$(PY) python -m {{pkg}}.registry.promote --config $(CONFIG) --rollback

# Drift + retraining decision for a scoring batch: make monitor CURRENT=path/to/batch.csv (exit 3 = retrain)
monitor:
	$(PY) python -m {{pkg}}.monitoring.run --config $(CONFIG) --current $(CURRENT)

# Read-only: registered versions, aliases, source commit, valid metrics.
runs:
	$(PY) python -m {{pkg}}.tracking --config $(CONFIG)

mlflow-ui:
	$(PY) mlflow ui --backend-store-uri sqlite:///mlflow.db

# Human-approved only: commit separately with the reason in the message.
rebaseline: eval
	cp metrics/current.json metrics/baseline.json

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache metrics/current.json artifacts reports

# Platform-specific targets (present when scaffolded with --platform databricks).
-include Makefile.databricks
