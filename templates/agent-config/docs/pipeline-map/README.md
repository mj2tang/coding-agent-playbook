# Pipeline map — {{project}}

Behaviour-level inventory of every way this ML system is used. Agents use it to decide **what to run** and **what evidence counts** when proving a change works (`prove-it-works` skill); humans use it as the regression checklist. One short file per entry point; keep entries runnable without reading source.

Each file answers the same four questions:
1. **What it is** — the entry point and who/what consumes it.
2. **How to reach it** — commands, jobs, or calls a real user/system makes.
3. **Evidence that counts** — the artifact a skeptical reviewer would accept.
4. **What usually lies** — known ways it looks fine but isn't.

## Baseline preconditions
- `make setup` done; `uv.lock` unchanged unless the task adds a dependency.
- Run from a clean worktree for the task's branch; never against a stale `metrics/current.json` or an old MLflow run.
- Fixed seed from `configs/base.yaml`; same config for baseline and candidate.

## Proof rules
- A change must be exercised through **every entry point it can affect**, not just the one its unit test covers. Changing feature code touches training, evaluation, batch scoring, and monitoring.
- Record each command and its artifact in the decision trail (`scripts/agent-team/audit.py log ...`).
- When an entry point can't be exercised here (needs production data, a deployed endpoint, credentials), name it, say what blocks it, and cover the closest real path.

## Full sweep (broad regression, top to bottom)
1. [data](data.md) — loading + contracts
2. [training](training.md) — fit + registration
3. [evaluation](evaluation.md) — metrics + gates
4. [promotion](promotion.md) — champion/challenger
5. [batch-scoring](batch-scoring.md) — predictions for consumers
6. [monitoring](monitoring.md) — drift + retrain decision

Add files as the system grows (online serving, feature store, dashboards). Fix drift in the same PR as the change that caused it.
