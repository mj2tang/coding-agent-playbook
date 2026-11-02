---
name: orchestrate-team
description: Run a team of coding agents on an ML project - decompose a goal into parallel feature tasks, dispatch feature/data/eval workers in isolated git worktrees within the parallelism the team has earned (trust ladder), route each result through the supervisor, merge only proven and gated work, and drive autonomous runs to a checkable exit condition. Use when asked to build several features at once, run an epic, or work "as a team". Not for a single small change - just do it directly.
---

# Orchestrate a team of agents

Throughput comes from trust, not from the number of agents. Earn trust in one worker's output through verification, then widen the wave.

## Roles
| Role | Runs as | Writes code? | Owns |
|---|---|---|---|
| Orchestrator | main session (`claude --agent orchestrator`) | rarely | `tasks/`, integration, merges, the decision trail |
| Feature / data / eval / MLOps workers | subagents, `isolation: worktree` | yes | the files listed in their task |
| Supervisor | subagent, read-only | no | verdicts |

## Procedure
1. **Load state:** `AGENTS.md`, `tasks/BOARD.md`, every `tasks/T-*.md`, `configs/team.json`, `configs/gates.json`, `docs/pipeline-map/README.md`. If `tasks/RESUME.md` exists, follow `pause-and-resume` (Resume) first.
2. **Set the exit condition** for the run as a checkable predicate before dispatching anything: e.g. "T-001..T-004 merged and `make gate` passes on main". Write it in `tasks/EPIC.md` (or the reply) and log it (`decision-log`, phase `plan`).
3. **Plan:** write/refresh task files with `feature-spec`. A "wave" = `todo` tasks whose dependencies are `done` and whose owned files don't overlap.
4. **Size the wave by trust:** `python3 scripts/agent-team/audit.py trust` prints how many workers the team has earned (starts at 1; rises after clean approvals; drops after a revert or human rework). Never dispatch more. `--explain` shows why.
5. **Dispatch:** for each task in the wave, mark `in_progress`, log a `dispatch` row, and launch the matching worker in the background with:
   > Task file: `tasks/T-012-<slug>.md`. Branch: `task/T-012-<slug>`. Follow worker-protocol and prove-it-works. Return the summary block only.
6. **Collect:** as each worker returns, check its EVIDENCE line exists, set `review`, and launch the `supervisor` on its branch.
7. **Decide:** `APPROVE` → queue for merge. `CHANGES_REQUESTED` → relaunch the worker with the findings (max 2 rounds; then `blocked`, log it, and ask the user).
8. **Merge** with `merge-train`, one branch at a time.
9. **Next wave:** recompute trust (step 4) and repeat from step 3.
10. **Report:** exit-condition state, a table of tasks (status, branch, evidence, metric deltas), the trust level, and decisions needed.

## Autonomous runs ("run until done", overnight, `/loop`)
- Each wave must move the exit condition; log `progress` or `no_progress` per wave.
- **Stop after two consecutive `no_progress` waves.** You're stuck - surface it with the evidence; don't spin.
- **Never relax the exit condition, a gate, or a threshold to declare victory.**
- Keep going on reversible work. Pause only for irreversible steps (push, deploy, promotion, raw data) - those wait for a human regardless of autonomy.
- Before context runs low or when asked to stop, use `pause-and-resume` (Pause).

## Settle forks by evidence, not by asking
Before asking the user "which approach?", check whether the answer is observable: which feature set scores better, which model is faster, whether a config change moves a metric. If it is, run a cheap probe (an `experiment-scientist` experiment or a throwaway worktree) and let the result decide. Ask only for genuine preferences, product trade-offs, and irreversible actions.

## When the user corrects merged work
Log `human_rework` for the task (this lowers the trust level) and run `encode-lesson` so the mistake becomes a test, contract, lint, or hook rule.

## Parallelism rules
- Parallel only when owned files are disjoint. Shared files (`configs/`, `pyproject.toml`) → one task owns them, others depend on it.
- Headless alternative: `scripts/agent-team/run-wave.sh T-011 T-012` (enforces the trust limit; `FORCE=1` overrides, log why).

## Never
- Merge without proof (`prove-it-works` evidence), a supervisor `APPROVE`, and a green `make gate` on the integration branch.
- Lower gate thresholds, rebaseline metrics, or skip tests to get green.
- Push, deploy, promote, or modify `data/raw/` without explicit human approval.
