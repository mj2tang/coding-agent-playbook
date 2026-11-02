---
name: worker-protocol
description: The contract every worker agent follows - claim one task file, stay inside its owned files in an isolated worktree, work test-first, run the gates, commit, and return a fixed summary. Use whenever you are executing a task from tasks/ as a worker. Not for the orchestrator or supervisor roles.
---

# Worker protocol

1. **Read** the task file, `AGENTS.md`, and the code you'll touch. If the task is ambiguous or conflicts with the code, stop and return `STATUS: blocked` with the question — don't guess.
2. **Branch:** you are in your own worktree. Create/checkout `task/<id>-<slug>` if you're not already on it.
3. **Stay in scope:** edit only the task's owned files (plus new test files). Need another file? Return `blocked` and say why.
4. **Test first** (`tdd-loop`): write failing tests from the acceptance criteria, then implement.
5. **Gates:** run `make check`, plus `make data-check` / `make gate` when the task touches data or models. Fix until green. Never weaken a test, threshold, or baseline.
6. **Commit** small logical commits: `T-<id>: <what>`. Do not push or merge.
7. **Update** the task file's `status: review` and fill the "Worker notes" section.
8. **Return exactly:**
```
STATUS: done | blocked
TASK: T-<id>  BRANCH: task/T-<id>-<slug>
CHANGED: <files>
GATES: check=pass data-check=<pass|n.a.> gate=<pass|n.a.>
METRICS: <metric>: <baseline> → <current>
NOTES: <risks, follow-ups, questions — 3 lines max>
```
