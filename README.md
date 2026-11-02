# Coding Agent Playbook

Practical, battle-tested habits for getting real work out of coding agents — **Claude Code**, **OpenAI Codex**, and friends. Collected from daily use, vendor docs, and papers, and kept short enough to actually read.

## The 10 rules

1. **Write the context file first.** `CLAUDE.md` / `AGENTS.md` with build, test, lint commands and the conventions a new hire would need. Keep it short; agents read every line every session.
2. **Plan before code.** For anything over ~30 lines, ask for a plan, edit the plan, *then* let it implement.
3. **Give it a way to check its own work.** Tests, type-checker, linter, a script that screenshots the UI. An agent that can verify is 10× more reliable than one that can't.
4. **Small, reviewable diffs.** One concern per session/branch. Commit often so every step is revertible.
5. **Clear context between tasks.** Stale context causes drift. New task → new session (or `/clear`).
6. **Be specific about the target.** File paths, function names, the failing test, the exact error. Vague asks get vague code.
7. **Parallelise with isolation.** Multiple agents → separate git worktrees or sandboxes, never the same checkout.
8. **Constrain permissions, not creativity.** Allow-list safe commands, sandbox the rest, and keep humans on irreversible actions (push, deploy, delete, publish).
9. **Turn repeated prompts into skills/commands.** If you've typed it three times, make it a reusable skill, slash command, or hook.
10. **Review like it's a junior's PR.** Read the diff. Run it. Agents are confidently wrong in exactly the places you don't check.

## Guides

| Guide | What's inside |
|---|---|
| [Foundations](docs/foundations.md) | Context files, prompting patterns, plan → implement → verify loop |
| [Claude Code](docs/claude-code.md) | CLAUDE.md hierarchy, plan mode, subagents, skills, hooks, permissions, headless mode |
| [Codex](docs/codex.md) | AGENTS.md, approval & sandbox modes, cloud tasks, review flow |
| [Workflows](docs/workflows.md) | TDD with agents, parallel worktrees, code review, debugging, refactors |
| [Skills & harness engineering](docs/skills-and-harness.md) | Designing skills, MCP tools, and the harness around the model |
| [Evaluating agents](docs/evaluation.md) | Measuring whether your setup actually got better |
| [Resources](resources.md) | Curated links and papers |

## Templates

- [`templates/AGENTS.md`](templates/AGENTS.md) — drop-in context file (works for Codex; symlink or copy to `CLAUDE.md` for Claude Code)
- [`templates/plan-prompt.md`](templates/plan-prompt.md) — plan-first prompt
- [`templates/review-checklist.md`](templates/review-checklist.md) — what to check in agent-written diffs

## Contributing

Tips should be **specific, tested, and tool-labelled** (✅ both / 🟠 Claude Code / 🔵 Codex). Link a source or describe how you verified it. Features move fast — date anything version-specific.
