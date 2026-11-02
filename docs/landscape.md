# Landscape: what we learned from popular agent-config repos

Surveyed November 2026. This playbook is original work; these projects shaped its structure. Stars are approximate.

| Repo | ★ | What it does well | What we adopted |
|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | 310k | A *methodology* as skills: brainstorm → plan → TDD → verify → finish branch; subagent-driven development; ships both Claude and Codex plugin manifests | Process skills (plan-first, tdd-loop, verify-before-done, systematic-debugging); dual `.claude-plugin` + `.codex-plugin` packaging |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) (everything-claude-code) | 295k | Huge catalogue: ~70 agents, ~300 skills, per-language rules, hook profiles, installers for Claude/Codex/Cursor/OpenCode | Role agents with read-only reviewers; confidence-filtered review output; guardrail hooks; selective install (we keep the catalogue small and ML-focused instead) |
| [anthropics/skills](https://github.com/anthropics/skills) | 187k | Reference Agent Skills + spec + `skill-creator` | `SKILL.md` format and description-as-trigger discipline |
| [github/spec-kit](https://github.com/github/spec-kit) | 145k | Spec-driven development: spec → plan → tasks → implement | Frozen `EPIC.md` spec and task files with checkable acceptance criteria |
| [openai/codex](https://github.com/openai/codex) | 133k | AGENTS.md chain, skills in `.agents/skills`, `codex exec`, plugins | Shared `AGENTS.md`; skills in `.agents/skills` for both tools; Codex headless runner |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 57k | Curated index of commands, hooks, workflows | Resource links |
| [wshobson/agents](https://github.com/wshobson/agents) | 42k | Multi-harness plugin marketplace of focused plugins | One repo = marketplace + plugin; small composable units |
| [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 33k | CLI installer for agents/commands/settings | One-command scaffolding (`scripts/init.sh`) |
| [openai/skills](https://github.com/openai/skills) | 28k | Curated Codex skills catalogue | Skills as the portable unit across tools |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 26k | 100+ specialised subagents | Narrow, role-specific agent prompts |
| [agentsmd/agents.md](https://github.com/agentsmd/agents.md) | 25k | The open AGENTS.md format | AGENTS.md as the single source of truth |

## ML practitioner sources
The ML specialist agents draw on published method rather than agent repos: Google (Rules of ML, ML Test Score, Hidden Technical Debt, Deep Learning Tuning Playbook), Karpathy's training recipe, Hamel Husain on evals, Kohavi et al. on online experiments, Eugene Yan's design docs, and Facebook/Google/Criteo CTR papers. See [ml-specialists.md](ml-specialists.md).

## MLOps sources
The MLOps layer follows the official MLflow docs (registry aliases, classic evaluation + `validate_evaluation_results`, MCP server) and ships alongside — not instead of — the official [mlflow/skills](https://github.com/mlflow/skills) (GenAI tracing and evaluation). Pipeline staging and checks follow Google's MLOps levels, Evidently's drift defaults, Made With ML, and cookiecutter-data-science. See [ml-lifecycle.md](ml-lifecycle.md).

## Common patterns across the best repos
1. **Skills are the portable unit.** Same `SKILL.md` works in Claude Code and Codex; agents/hooks are tool-specific wrappers.
2. **Process over prompts.** The most-starred repos encode a workflow (plan → test → verify → review), not clever wording.
3. **Separate author and reviewer** with read-only reviewer agents and confidence thresholds to cut noise.
4. **Deterministic guardrails in hooks**, judgement in skills.
5. **Distribution as plugins/marketplaces**, with selective install so projects don't load hundreds of irrelevant skills.

## Where this playbook differs
- **ML-specific gates**: data contracts, leakage checks, metric regression vs a committed baseline.
- **A team topology** (orchestrator / supervisor / workers) with worktree isolation and a file-based task board both tools can read.
- **Small on purpose**: ~19 skills and 22 agents you can read in an afternoon.
