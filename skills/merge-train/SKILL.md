---
name: merge-train
description: Integrate supervisor-approved worker branches one at a time with a full quality gate after each merge, reverting any merge that breaks the gate and logging each merge or revert to the decision trail. Use when the orchestrator has approved branches to land. Not for branches without a supervisor APPROVE.
---

# Merge train

One command per step (compound commands stall headless runs). For each approved branch, in dependency order:

1. `git switch main`
2. `git merge --no-ff task/T-012-slug -m "Merge T-012: <title>"`
3. `make check`
4. `make gate`

Then:
- **Green:** mark the task `done` in its file and `tasks/BOARD.md`; `git worktree remove <path>`; log it:
  `python3 scripts/agent-team/audit.py log merge T-012 orchestrator "merged task/T-012-slug" "approved and gates green" "<merge commit>" merged`
- **Conflict:** `git merge --abort`, set the task back to `in_progress`, and send it to a worker to rebase on `main`. Don't hand-resolve conflicts in files you don't own.
- **Red after merge:** `git revert -m 1 HEAD --no-edit`, mark the task `blocked` with the failing output, log `reverted` (this lowers the trust level), and continue with the next branch.

After the train: run `make gate` once more and report metric deltas vs `metrics/baseline.json`. Updating the baseline (`make rebaseline`) is a human decision.
