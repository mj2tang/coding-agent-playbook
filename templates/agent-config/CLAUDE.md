@AGENTS.md

## Claude Code
- Team mode: start with `claude --agent orchestrator`. Workers (`feature-worker`, `data-worker`, `eval-worker`) run in isolated worktrees; `supervisor` gates merges.
- Solo mode: use plan mode for anything non-trivial, then the `verify-before-done` skill before finishing.
- Guard hooks block pushes, edits to `data/raw/`, secrets, and gate files; ask the user instead of working around them.
