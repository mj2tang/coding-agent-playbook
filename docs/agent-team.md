# Team of agents for ML projects

A setup for running **parallel feature development** on an ML codebase with an orchestrator, a supervisor, and specialised workers — without giving up engineering quality.

```
                 ┌──────────────────────────── you ────────────────────────────┐
                 │ goal, approvals (push, rebaseline, thresholds, new deps)     │
                 └──────────────────────────────┬──────────────────────────────┘
                                                ▼
                              ┌──────── orchestrator ────────┐  main session
                              │ tasks/ board · waves · merges│  claude --agent orchestrator
                              └──┬─────────┬──────────┬──────┘
               worktree task/T-1 │         │ T-2      │ T-3      (parallel, isolated)
                       ┌─────────▼──┐ ┌────▼──────┐ ┌─▼─────────┐
                       │feature-    │ │data-      │ │eval-      │  write code + tests,
                       │worker      │ │worker     │ │worker     │  run gates, commit
                       └─────┬──────┘ └────┬──────┘ └─┬─────────┘
                             └──────┬──────┴──────────┘
                                    ▼
                          ┌──── supervisor ────┐  read-only, independent
                          │ gates + ML review  │  APPROVE / CHANGES_REQUESTED
                          └─────────┬──────────┘
                                    ▼
                       merge-train → main (make gate after every merge)
```

## Trust before parallelism

Adapted from Lauren Tan's ("poteto") approach in [pstack](https://github.com/poteto/plugins): throughput comes from trust, not from the number of agents.

- **Earned parallelism.** `python3 scripts/agent-team/audit.py trust` replays the decision trail: the team starts at `trust.start_workers` (1), gains a worker after `trust.promote_after` (3) consecutive first-round approvals, and loses one after a revert or human rework - capped at `max_parallel_workers`. `run-wave.sh` refuses larger waves unless `FORCE=1`.
- **Proof on the real artifact.** `docs/pipeline-map/` lists every way the system is used (data, training, evaluation, promotion, batch scoring, monitoring), how to drive each, the evidence that counts, and what usually lies. Workers cover every entry point their change can affect (`prove-it-works`) and return an EVIDENCE line; the supervisor checks the artifacts, not the summary.
- **Decision trail.** One TSV row per dispatch, verdict, merge, revert, pivot, or blocker (`decision-log`), local in `.audit/` by default; commit a copy for large unattended runs.
- **Lessons become mechanisms.** A correction becomes a type/contract, test, lint, hook rule, or helper before it becomes `AGENTS.md` text (`encode-lesson`).
- **Autonomous runs have a finish line.** A checkable exit condition up front, stop after two no-progress waves, never relax the condition; `pause-and-resume` leaves `tasks/RESUME.md` for a clean handoff.
- **Settle forks by evidence.** Observable questions (which feature set scores better?) get a probe, not a question to the human.

## Specialists
Eight advisory agents bring expert ML method into the loop — `ml-problem-framer`, `experiment-scientist`, `training-debugger`, `error-analyst`, `ranking-ctr-specialist`, `llm-eval-engineer`, `ml-production-auditor`, `ab-test-analyst`. The orchestrator calls them at set moments (see `configs/team.json` → `specialists`). Details and sources: [ml-specialists.md](ml-specialists.md).

## Why this shape
- **Isolation beats coordination.** Each worker gets its own git worktree and a disjoint set of owned files, so agents never edit the same checkout.
- **Separate author and reviewer.** The supervisor didn't write the code, runs every gate itself, and only reports evidence-backed findings.
- **Gates are code, not vibes.** `make check`, `make data-check`, and `make gate` (metrics vs a committed baseline) decide what merges. Agents can't edit thresholds or baselines — the guard hook blocks it.
- **A file-based board.** `tasks/*.md` is readable by every tool (Claude Code, Codex, humans) and survives context resets.
- **Humans keep the irreversible decisions:** push, deploy, raw data, thresholds, rebaselines, new dependencies.

## Lifecycle of a feature
1. You describe a goal (or fill `tasks/EPIC.md`).
2. Orchestrator writes task files (`feature-spec` skill): objective, owned files, command-checkable acceptance criteria, dependencies.
3. A **wave** = tasks whose dependencies are done and whose files don't overlap. Orchestrator dispatches up to `max_parallel_workers` (default 3).
4. Each worker (`worker-protocol`): branch `task/<id>`, tests first, implement, run gates, commit, return a fixed summary.
5. Supervisor reviews the branch → verdict with gate results and metric deltas.
6. Orchestrator merges approved branches one at a time (`merge-train`), re-running `make gate` after each; reverts anything that breaks it.
7. Board updated; next wave.

## Running it
**Claude Code (interactive):**
```bash
claude --agent orchestrator
> Build the features in tasks/EPIC.md as a team.
```
Workers run as subagents with `isolation: worktree`; the supervisor is a read-only subagent.

**Headless, any tool** (CI, overnight, or Codex):
```bash
scripts/agent-team/run-wave.sh T-001 T-002 T-003          # claude -p per task
RUNNER=codex scripts/agent-team/run-wave.sh T-001 T-002   # codex exec per task
```
Then review each branch with the supervisor and merge with the merge-train skill.

## Tuning
| Knob | Where | Guidance |
|---|---|---|
| Parallel workers | `configs/team.json` → `max_parallel_workers` | 2–4. Beyond that, merge conflicts and review load dominate. |
| Review rounds | `configs/team.json` → `max_review_rounds` | 2, then escalate to a human. |
| Metric tolerances | `configs/gates.json` | Set from seed-to-seed noise (run eval with 3–5 seeds). |
| Suspicious gain | `configs/gates.json` → `suspicious_gain` | Flags too-good-to-be-true jumps (often leakage). |
| Models per role | agent frontmatter `model:` | Orchestrator/supervisor on the strongest model; workers can be cheaper. |

## Failure modes and the guardrail for each
| Failure | Guardrail |
|---|---|
| Two agents edit the same file | Owned-files in task spec; worktrees; orchestrator checks overlap before dispatch |
| Agent "fixes" a failing test by weakening it | Supervisor checklist; Code Review Rules in `AGENTS.md` |
| Metric goes up because of leakage | `suspicious_gain` warning; leakage checklist; split-before-fit in template |
| Agent lowers a threshold to pass | Guard hook blocks edits to `configs/gates.json` and `metrics/baseline.json` |
| Silent bad data | Data contracts validated at load; `make data-check` in CI |
| Context drift on long epics | `tasks/EPIC.md` (frozen spec), decision log + status log in files, small tasks |
| Irreversible actions | Guard hook blocks push/reset/remote data ops; settings `ask` list |
