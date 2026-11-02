---
name: encode-lesson
description: Turn a correction, repeated mistake, or failure into the strongest mechanism that prevents it - a type or schema, a test, a lint/CI check, a guard-hook rule, a helper or script - and add AGENTS.md text only for judgment calls that can't be enforced. Use when the human corrects an agent, the same instruction is needed twice, a gate failure reveals a recurring mistake, or at the end of a session. Not for one-off task notes (those go in the task file).
---

# Encode lessons in structure

Agents skip text; they can't skip a failing check. Every correction is a signal - capture it, route it to the strongest layer, and close the loop now.

## 1. Classify
- **One-off** (specific to this task) → task file "Decision log". Stop.
- **Recurring** (seen twice, or will clearly recur) → step 2.
- **Systemic** (shapes how the team should work) → step 2, then propose a principle/skill change.

## 2. Pick the strongest rung that works
1. **Make it unrepresentable**: a type, enum, or data-contract rule (`data/contracts.py`) so the bad state can't be built.
2. **A failing test or gate**: a unit/known-answer test, a `make data-check` contract, a `configs/gates.json` metric.
3. **A lint or CI check**: a ruff rule, a grep check in CI, a schema validation.
4. **A guard-hook rule**: block the action itself (`.claude/hooks/guard.py` patterns: dangerous commands, protected paths).
5. **A canonical helper or script**: one blessed way to do the thing, so agents copy it.
6. **Text in `AGENTS.md`** (or a skill): only when it genuinely needs judgment. Add the failure example next to the rule.

Agents copy whatever the surrounding code does, so a weak guard becomes the next template. Prefer the higher rung even if it's a bit more work.

## 3. Apply it now
Implement the mechanism in this session (or create a task file for it). "I'll keep that in mind" doesn't persist; a note that a lint rule should exist is wasted until the rule exists.

## 4. Record and prune
Log it: `python3 scripts/agent-team/audit.py log lesson <task> <actor> "<mechanism added>" "<the mistake it prevents>" "<file or rule>" encoded`. If an `AGENTS.md` line is now enforced by a mechanism, delete the line. Keep `AGENTS.md` under ~200 lines; show the human any change to shared config.

Adapted from the "encode lessons in structure" principle in Lauren Tan's pstack.
