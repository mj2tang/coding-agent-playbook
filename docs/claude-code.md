# Claude Code

🟠 Tips specific to [Claude Code](https://docs.claude.com/en/docs/claude-code/overview).

## Memory files
- `CLAUDE.md` at repo root (shared, committed), `CLAUDE.local.md` (personal, gitignored), `~/.claude/CLAUDE.md` (all projects). Subdirectory `CLAUDE.md` files load when the agent works there.
- `/init` drafts a starting `CLAUDE.md` from the codebase — then trim it.
- Already have `AGENTS.md`? Point to it from `CLAUDE.md` (e.g. `@AGENTS.md`) so both tools share one source.

## Modes and session control
- **Plan mode** (Shift+Tab to cycle modes): read-only exploration and planning. Use for anything non-trivial.
- `/clear` between tasks; `/compact` to summarise a long session and keep going.
- `Esc` interrupts; double-`Esc` lets you rewind to an earlier message.
- `!command` runs a shell command and puts the output in context.

## Permissions
- Allow-list safe, frequent commands (test runner, linter, `git status`) in `.claude/settings.json` so you aren't approving them all day.
- Keep `git push`, deploys, and anything destructive behind a prompt.
- `/permissions` to inspect and edit rules.

## Extending it
| Mechanism | Use it for | Lives in |
|---|---|---|
| **Slash commands / skills** | Reusable workflows ("write release notes", "review this PR") | `.claude/skills/<name>/SKILL.md` |
| **Subagents** | Focused side tasks with their own context (search, review, test-writing) | `.claude/agents/*.md` |
| **Hooks** | Deterministic automation: format on edit, block edits to protected paths, notify on finish | `settings.json` → `hooks` |
| **MCP servers** | Tools and data: issue trackers, databases, browsers, docs | `claude mcp add …` / `.mcp.json` |

Rule of thumb: if it must *always* happen, use a hook; if it's judgement, use a skill.

## Parallel and headless
- Run several sessions in separate **git worktrees**, one task each.
- `claude -p "…"` runs non-interactively — useful in scripts and CI (pair with tight permissions).
- Have one session write code and a fresh session review it; a clean context catches more.

## Habits that pay off
- Ask it to write the failing test first, confirm it fails, then implement.
- For UI work, give it a way to see the result (screenshots, browser automation).
- End a session by asking "what should go into CLAUDE.md from this session?"
