---
name: pause-and-resume
description: Stop long or team work at a safe boundary and leave a resume note a fresh agent can pick up from (tasks/RESUME.md + wip commit), and resume from such a note without redoing finished work. Use when asked to pause, before going offline, when context is about to be compacted, or when taking over someone else's run ("pick up where X left off"). Not when told to keep going - "don't stop" means continue.
---

# Pause and resume

## Pause
1. **Stop at a safe boundary.** Finish or back out of the current step; never stop mid-edit in a known-broken state. Start nothing new; let running workers finish or stop them cleanly.
2. **Don't cross an irreversible line to pause.** No push, no promotion, no deploy.
3. **Make work durable.** Commit uncommitted edits on the current branch as `wip: <what>`; say in the body if the tree is broken. For each worker worktree, note its branch and state instead of merging it.
4. **Write `tasks/RESUME.md`** (overwrite) with: goal and exit condition, what's done and verified (with evidence pointers), what's in flight (task, branch, worktree, state), next steps in order, key files, gotchas, and a pointer to `.audit/decisions.tsv` instead of repeating it.
5. **Log it:** `python3 scripts/agent-team/audit.py log pause <task> <actor> "paused at <step>" "<why>" tasks/RESUME.md paused`.

Reply with: where you stopped, what's on disk vs only in your head, commits made, and the first action on resume.

## Resume (pickup)
A pickup is inheritance - the previous agent already paid for the reading and repros. Read, don't redo.
1. Read `tasks/RESUME.md`, then `python3 scripts/agent-team/audit.py show --last 40`, `tasks/BOARD.md`, and `git log --oneline -20` on the integration branch and in-flight task branches.
2. Reconstruct state: what merged, which branches/worktrees exist, which tasks are `in_progress`/`review`.
3. Diff done vs planned; name the resume point. Do not re-run finished work.
4. **Verify inherited claims** on the real artifact before building on them (`prove-it-works`): rerun the gates on the integration branch; a prior "all green" is not proof.
5. Continue with the matching skill (`orchestrate-team`, `worker-protocol`, ...), and log `resume` with the resume point.

Adapted from the pause-safely and session-pickup playbooks in Lauren Tan's pstack.
