---
name: orchestrate-team
description: Run a team of coding agents on an ML project - decompose a goal into parallel feature tasks, dispatch feature/data/eval workers in isolated git worktrees, route each result through the supervisor, and merge only gated work. Use when asked to build several features at once, run an epic, or work "as a team". Not for a single small change - just do it directly.
---

# Orchestrate a team of agents

## Roles
| Role | Runs as | Writes code? | Owns |
|---|---|---|---|
| Orchestrator | main session (`claude --agent orchestrator`) | rarely | `tasks/`, integration, merges |
| Feature / data / eval workers | subagents, `isolation: worktree` | yes | the files listed in their task |
| Supervisor | subagent, read-only | no | verdicts |

## Procedure
1. **Load state:** `AGENTS.md`, `tasks/BOARD.md`, every `tasks/T-*.md`, `configs/team.json`, `configs/gates.json`.
2. **Plan:** write/refresh task files with the `feature-spec` skill. Build the dependency graph; a "wave" is the set of `todo` tasks whose dependencies are `done` and whose owned files don't overlap.
3. **Dispatch a wave:** up to `max_parallel_workers` tasks. For each, mark `in_progress`, then launch the matching worker subagent in the background with:
   > Task file: `tasks/T-012-<slug>.md`. Branch: `task/T-012-<slug>`. Follow worker-protocol. Gate: `make check && make gate`. Return the summary block only.
4. **Collect:** as each worker returns, set the task to `review` and launch the `supervisor` on its branch.
5. **Decide:** `APPROVE` → queue for merge. `CHANGES_REQUESTED` → resume/relaunch the worker with the findings (max 2 rounds; then `blocked` + ask the user).
6. **Merge:** use `merge-train` for the queue, one branch at a time.
7. **Next wave:** repeat from step 2 until the board is done or only blocked tasks remain.
8. **Report** to the user: a table of tasks (status, branch, metric deltas) and decisions needed.

## Parallelism rules
- Parallel only when owned files are disjoint. Shared files (e.g. `configs/`, `pyproject.toml`) → one task owns them, others depend on it.
- Prefer 2–4 workers. More workers = more merge conflicts and review load, not more throughput.
- Headless alternative (any tool): `scripts/agent-team/run-wave.sh T-011 T-012 T-013` runs each task with `claude -p` or `codex exec` in its own worktree.

## Never
- Merge without a supervisor `APPROVE` and a green `make gate` on the integration branch.
- Lower gate thresholds, rebaseline metrics, or skip tests to get green.
- Push, deploy, or modify `data/raw/` without explicit human approval.
