---
id: T-000
title: <short imperative title>
type: feature | data | eval
worker: feature-worker | data-worker | eval-worker
status: todo
depends_on: []
branch: task/T-000-<slug>
owned_files:
  - src/{{pkg}}/...
  - tests/...
---

## Objective
<What should be true when this is done, in one or two sentences.>

## Acceptance criteria (each checkable by a command)
- [ ] `uv run pytest tests/...` passes, including new tests for: <cases>
- [ ] `make check` passes
- [ ] `make gate` passes; <metric> on valid ≥ baseline − <tolerance>

## Out of scope
- <things the worker must not change>

## Context
<Links, prior experiments, relevant files.>

## Decision log
- <date> — <decision> — <why>

## Worker notes
<Filled by the worker: what changed, gate output summary, risks.>

## Supervisor verdict
<APPROVE | CHANGES_REQUESTED + findings>
