---
name: merge-train
description: Integrate supervisor-approved worker branches one at a time with a full quality gate after each merge, reverting any merge that breaks the gate. Use when the orchestrator has approved branches to land. Not for branches without a supervisor APPROVE.
---

# Merge train

For each approved branch, in dependency order:

```bash
git checkout main && git pull --ff-only 2>/dev/null || true   # local integration branch
git merge --no-ff task/T-012-slug -m "Merge T-012: <title>"
make check && make gate
```

- **Green:** mark the task `done` in its file and `tasks/BOARD.md`; remove the worktree (`git worktree remove <path>`) once merged.
- **Conflict:** abort (`git merge --abort`), set the task back to `in_progress`, and send it to a worker to rebase on `main`. Don't hand-resolve conflicts in files you don't own.
- **Red after merge:** `git revert -m 1 HEAD`, mark the task `blocked` with the failing output, and continue with the next branch.

After the train: run `make gate` once more and report metric deltas vs `metrics/baseline.json`. Updating the baseline (`make rebaseline`) is a human decision.
