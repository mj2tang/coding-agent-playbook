# Agent-team playbook — {{project}}

Instructions for running this repository's work with a team of coding agents (installed by
[coding-agent-playbook](https://github.com/mj2tang/coding-agent-playbook)). They add a workflow;
they don't replace this project's own conventions, commands, or AGENTS.md/CLAUDE.md.

## Commands
Use this project's own build, test, and lint commands (see its README, AGENTS.md, CLAUDE.md,
package.json, Makefile, or pyproject.toml). Wherever a playbook skill says `make check`, run the
project's equivalent full check; `make gate` means "the project's acceptance checks pass".

## Agent team
- Orchestrator (`claude --agent orchestrator`) plans tasks in `tasks/` and dispatches workers; each
  worker runs in its own git worktree on `task/<id>-<slug>`; the supervisor reviews every branch
  before merge. Skills: `orchestrate-team`, `worker-protocol`, `merge-train`.
- Parallelism is earned: `python3 scripts/agent-team/audit.py trust` (starts at 1 worker).
- Log decisions with `python3 scripts/agent-team/audit.py log ...` (`.audit/decisions.tsv`, local).
- Prove changes on the real thing, not proxies (`prove-it-works`), and turn repeated corrections into
  checks (`encode-lesson`).

## Needs human approval
- Pushing, deploying, deleting data, adding dependencies, and changing CI or release configuration.
