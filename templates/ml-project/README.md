# {{project}}

{{description}}

Scaffolded with [coding-agent-playbook](https://github.com/mj2tang/coding-agent-playbook): an ML project skeleton with quality gates and an agent team (orchestrator, supervisor, workers).

## Quick start
```bash
make setup        # uv sync
make check        # lint + types + unit tests
make data-check   # data contracts
make gate         # evaluate and compare against metrics/baseline.json
```

## Working with agents
```bash
claude --agent orchestrator     # Claude Code: main session plans + dispatches workers
codex                           # Codex: reads AGENTS.md and .agents/skills
```
Tasks live in `tasks/` (see `tasks/BOARD.md`). Gate thresholds are in `configs/gates.json`.
