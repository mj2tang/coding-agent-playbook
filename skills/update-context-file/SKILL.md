---
name: update-context-file
description: Capture durable lessons from a session into AGENTS.md (shared by Codex and Claude Code via CLAUDE.md) - commands, conventions, and gotchas the next agent would otherwise rediscover. Use at the end of a session, after an agent repeats a mistake, or when project commands change. Not for task-specific notes - those go in the task file.
---

# Update the context file

1. List what the next agent would need that it can't learn quickly from the code: commands, conventions, gotchas, decisions.
2. Drop anything session-specific, obvious from code, or already enforced by a linter/hook.
3. Edit `AGENTS.md` in the right section, one line per fact, imperative voice.
4. Keep the file under ~200 lines; prune stale lines when adding new ones.
5. Show the diff to the user; it's shared team config.
