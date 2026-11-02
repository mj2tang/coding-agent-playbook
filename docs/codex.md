# OpenAI Codex

🔵 Tips specific to [Codex](https://openai.com/codex/) (CLI, IDE extension, and cloud).

## AGENTS.md
- Codex reads `AGENTS.md` files from the repo (root and nested); closer files take precedence for their subtree. Personal defaults can live in your Codex home directory.
- Same content rules as any context file: commands, layout, conventions, gotchas. Spell out the exact test command — cloud tasks rely on it to verify work.

## Approval and sandboxing
- Pick the least-privileged mode that lets you flow: read-only for exploration, workspace-write for implementation, full access only in throwaway environments.
- Keep network access off unless the task needs it.

## Local vs cloud
- **Local (CLI/IDE):** interactive, tight feedback loop, great for exploratory or UI work.
- **Cloud tasks:** fire off several well-scoped tasks in parallel and review the resulting diffs/PRs. Works best when the repo's setup and tests run headlessly.
- Make the environment reproducible (setup script, pinned versions) so cloud runs match yours.

## Prompting
- Codex follows instructions literally: state scope ("only modify `src/billing/`") and stopping conditions ("stop after tests pass; don't refactor unrelated code").
- Ask for a plan first on large changes, then implement step by step.
- Use it as a reviewer too: ask it to review a diff against your checklist.

## Using Codex and Claude Code together
- Keep one shared `AGENTS.md`; reference it from `CLAUDE.md`.
- Cross-review: let one tool implement and the other review — different models catch different mistakes.
