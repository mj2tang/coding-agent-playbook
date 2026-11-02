# Quality gates used by humans, agents, and CI. Keep target names stable:
# AGENTS.md, skills, and the supervisor agent refer to them.
PY ?= uv run
CONFIG ?= configs/base.yaml

.PHONY: setup check lint types test data-check train eval gate rebaseline clean

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

train:
	$(PY) python -m {{pkg}}.models.train --config $(CONFIG)

eval:
	$(PY) python -m {{pkg}}.evaluation.run --config $(CONFIG) --out metrics/current.json

gate: eval
	$(PY) python scripts/check_metrics.py --current metrics/current.json --baseline metrics/baseline.json --rules configs/gates.json

# Human-approved only: commit separately with the reason in the message.
rebaseline: eval
	cp metrics/current.json metrics/baseline.json

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache metrics/current.json artifacts
