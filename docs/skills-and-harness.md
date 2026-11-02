# Skills & harness engineering

The model is only part of the system. The **harness** — context files, tools, skills, permissions, feedback loops — often matters as much as the model choice.

## Skills
- A skill = instructions + optional scripts/resources, loaded only when relevant. Keeps the base context small.
- Write the **description** carefully: it's what decides whether the skill triggers.
- One job per skill. Include: when to use it, step-by-step procedure, how to verify, common failure modes.
- Put deterministic steps in scripts the skill calls, not in prose the model must follow.
- Test skills on real tasks and iterate; treat them like code.

## Tools / MCP
- Fewer, well-described tools beat many overlapping ones.
- Tool outputs should be concise and structured; truncate or paginate big results.
- Return actionable errors ("file not found: did you mean src/x.ts?") — the agent will use them.

## Feedback loops
- Fast, cheap verification (unit tests, type-check) the agent can run constantly.
- Hooks to enforce invariants automatically (format, lint, block protected paths).
- Visual verification for UI (screenshots, browser automation).

## Further reading
See the harness and skills papers in [resources.md](../resources.md#papers).
