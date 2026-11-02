# Workflows

## TDD with an agent ✅
1. "Write tests for <behaviour>. Don't implement. Run them and confirm they fail."
2. Review the tests — they *are* the spec.
3. "Make the tests pass without changing them."
4. "Refactor for clarity; tests must stay green."

## Parallel agents ✅
- One worktree (or cloud task) per agent: `git worktree add ../app-feature-x -b feature-x`.
- Split by independent units (different modules, different bugs); avoid two agents on the same files.
- Merge one at a time and rerun tests after each.

## Code review ✅
- Review with a fresh session/agent, not the one that wrote the code.
- Give it a checklist (see [`templates/review-checklist.md`](../templates/prompts/review-checklist.md)).
- Ask for findings ranked by severity with a concrete failure scenario each — filters out style noise.

## Debugging ✅
- Reproduce first: failing test or exact command + output.
- Ask for hypotheses with evidence before any fix.
- Add logging, run, read logs, then fix. Remove the logging after.

## Large refactors / migrations ✅
- Have the agent write a migration plan + checklist file in the repo, then work through it across sessions.
- Do one mechanical pattern first, review it, then let the agent apply it everywhere.
- Lean on the type-checker and tests as the safety net.

## Learning a new codebase ✅
- "Give me a tour: entry points, request lifecycle, data model, where tests live."
- "Trace what happens when a user does X, citing file:line."
