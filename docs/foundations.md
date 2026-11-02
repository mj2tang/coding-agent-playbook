# Foundations

Applies to every coding agent.

## 1. The context file

Both tools load a markdown file from the repo automatically: Claude Code reads `CLAUDE.md`, Codex reads `AGENTS.md`. Treat it as onboarding for a smart new hire who has amnesia every morning.

**Put in:**
- Exact commands: install, build, test (single test + full suite), lint, format, run locally
- Architecture in 5–10 lines: where things live, what talks to what
- Conventions that aren't obvious from the code (error handling, naming, "never edit generated files in `gen/`")
- Gotchas that have burned you before

**Leave out:** anything the agent can learn by reading code, long prose, style rules your linter already enforces.

**Maintain it:** when the agent makes the same mistake twice, add one line to the file. Prune lines that no longer matter.

## 2. Prompt shape

```
Goal:      what "done" looks like (behaviour, not implementation)
Context:   files, functions, error messages, links
Constraints: what not to touch, libraries to use/avoid, perf/security needs
Verify:    how to prove it works (test command, URL, expected output)
```

The **Verify** line is the most skipped and the most valuable.

## 3. Plan → implement → verify

1. **Explore:** "Read X and Y, explain how Z works. Don't change anything."
2. **Plan:** "Propose a plan with the files you'll touch." Edit it yourself.
3. **Implement:** one plan step at a time for risky work, all at once for routine work.
4. **Verify:** agent runs tests/linters; you read the diff.
5. **Commit:** small, descriptive commits so you can bisect agent mistakes.

## 4. Context hygiene

- One task per session. Start fresh when switching topics.
- Long sessions degrade: when the agent starts repeating itself or forgetting constraints, summarise and restart.
- Prefer pointing at files ("see `src/auth/session.ts`") over pasting large blobs.
- Large logs: save to a file and let the agent `grep` it.

## 5. When the agent is stuck

- After 2 failed attempts at the same fix, stop it. Ask for a diagnosis (hypotheses + evidence), not another patch.
- Give it a reproduction: a failing test beats a description every time.
- Check if it's fighting the environment (wrong Node/Python version, missing env var) rather than the code.
