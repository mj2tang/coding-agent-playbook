---
name: feature-spec
description: Write a task file on the agent task board (tasks/T-NNN-slug.md) with objective, owned files, acceptance criteria including metric thresholds, and dependencies, so a worker agent can execute it without further questions. Use when decomposing work for parallel agents or before starting any non-trivial ML feature. Not for one-line fixes or pure questions.
---

# Feature spec (task file)

Create `tasks/T-<NNN>-<slug>.md` from `tasks/_TEMPLATE.md` and add a row to `tasks/BOARD.md`.

## Quality bar for a task
- **Independent:** a worker can finish it without talking to other workers.
- **Owned files are explicit** and don't overlap with any other `todo`/`in_progress` task.
- **Acceptance criteria are checkable by a command**, e.g.
  - `pytest tests/features/test_lags.py` passes with new tests for edge cases X, Y
  - `make gate` passes; `roc_auc` on `valid` ≥ baseline − 0.002
  - `make data-check` passes with the new `orders` contract
- **Size:** ~1–4 hours of human work. Bigger → split. Smaller → merge with a neighbour.
- **Out of scope** list prevents drive-by refactors.

## Decomposition order for ML work
1. Data contracts and fixtures (data-worker) — unblock everything else.
2. Evaluation harness + baseline (eval-worker) — you can't judge features without it.
3. Features / models (feature-workers) — now parallel and measurable.
4. Integration + rebaseline (orchestrator, human-approved).
