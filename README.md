# Coding Agent Playbook

Auto-configure **machine learning projects for a team of coding agents**: an orchestrator that plans and dispatches, workers that build features in parallel git worktrees, and a supervisor that only lets work through when the quality gates pass. Works with **Claude Code** and **OpenAI Codex**.

```bash
# New ML project: skeleton + agent team + gates, green on first run
curl -fsSL https://raw.githubusercontent.com/mj2tang/coding-agent-playbook/main/scripts/init.sh \
  | bash -s -- new churn-model --name churn-model --description "Predict customer churn" --bootstrap

cd churn-model && claude --agent orchestrator
> Build the features in tasks/EPIC.md as a team.
```

Add the team to an **existing** repo: `... | bash -s -- init .` · Update later: `... | bash -s -- sync .`

## What you get

| Layer | Contents |
|---|---|
| **Agent team** | `orchestrator` (main session) · `feature-worker` · `data-worker` · `eval-worker` (each `isolation: worktree`) · `supervisor` (read-only gatekeeper) · `code-reviewer` |
| **ML specialists** | `ml-problem-framer` · `experiment-scientist` · `training-debugger` · `error-analyst` · `ranking-ctr-specialist` · `llm-eval-engineer` · `ml-production-auditor` · `ab-test-analyst` — grounded in Google's Rules of ML, ML Test Score & Tuning Playbook, Karpathy, Hamel Husain, Kohavi, and Facebook/Google CTR papers ([details](docs/ml-specialists.md)) |
| **Skills** (Claude Code + Codex) | Team: `orchestrate-team`, `feature-spec`, `worker-protocol`, `merge-train` · ML: `ml-design-doc`, `ml-quality-gates`, `data-contract`, `eval-regression`, `experiment-protocol` · Engineering: `plan-first`, `tdd-loop`, `verify-before-done`, `systematic-debugging`, `update-context-file` |
| **Guardrail hooks** | Block `git push`/`reset --hard`/remote-data ops; protect `.env`, `data/raw/`, gate thresholds, and metric baselines; auto-format edits |
| **ML project skeleton** | `src/<pkg>/{data,features,models,evaluation}`, data contracts, split-before-fit pipeline, known-answer metric tests, `configs/`, CI |
| **Quality gates** | `make check` (ruff, mypy, pytest) · `make data-check` (contracts) · `make gate` (metrics vs committed baseline with per-metric tolerance + leakage "suspicious gain" warning) |
| **Task board** | `tasks/EPIC.md` (frozen spec), `tasks/BOARD.md`, one `T-NNN-*.md` per task with owned files and command-checkable acceptance criteria |
| **Headless runner** | `scripts/agent-team/run-wave.sh T-001 T-002` — one `claude -p` or `codex exec` per task, each in its own worktree |
| **Context files** | `AGENTS.md` (shared, with Code Review Rules for leakage/reproducibility) + `CLAUDE.md` → `@AGENTS.md` |

How the team works: **[docs/agent-team.md](docs/agent-team.md)**.

## Install options

| Use case | Command |
|---|---|
| New ML project | `playbook.py new <dir> --name <name> [--bootstrap]` |
| Existing repo | `playbook.py init <dir>` — never overwrites; writes `AGENTS.playbook.md` if you already have `AGENTS.md`, merges `.claude/settings.json` |
| Update vendored files | `playbook.py sync <dir>` — updates untouched files, skips ones you edited (`--force` to overwrite) |
| Claude Code plugin only | `/plugin install agent-playbook --marketplace mj2tang/coding-agent-playbook` (or `/plugin marketplace add mj2tang/coding-agent-playbook` then `/plugin install agent-playbook@mj2tang`) |
| Codex marketplace | `codex plugin marketplace add mj2tang/coding-agent-playbook` |

`--mode vendor` (default) copies skills, agents, and hooks into the repo so the whole team gets them through git. `--mode plugin` enables the Claude Code plugin via project settings instead (skills are still copied to `.agents/skills/` for Codex).

## The 10 rules

1. **Write the context file first.** `AGENTS.md` with commands, layout, conventions, and what's allowed without asking.
2. **Plan before code.** Freeze the target in a spec; split into tasks with checkable acceptance criteria.
3. **Give agents a way to check their own work.** Tests, contracts, and metric gates they can run in seconds.
4. **Isolate parallel work.** One worktree and a disjoint set of files per agent.
5. **Separate author and reviewer.** A fresh, read-only reviewer catches what the author can't.
6. **Make gates non-negotiable.** Agents never edit thresholds, baselines, or tests to get green — enforce it with hooks.
7. **Keep humans on irreversible actions.** Push, deploy, raw data, rebaselines, new dependencies.
8. **Clear context between tasks.** State lives in files (task board, decision log), not in chat history.
9. **Turn repeated prompts into skills**, with descriptions that say when *and when not* to use them.
10. **Measure your setup.** Evaluate skill routing and agent outcomes; turn every manual fix into a test case.

## Guides

| Guide | What's inside |
|---|---|
| [Team of agents for ML](docs/agent-team.md) | Topology, lifecycle of a feature, running it, tuning, failure modes |
| [ML specialist agents](docs/ml-specialists.md) | 8 expert-method agents, when they're used, sources, and a review of ML agents in popular repos |
| [Foundations](docs/foundations.md) | Context files, prompt shape, plan → implement → verify |
| [Claude Code](docs/claude-code.md) | Subagents, `--agent`, worktree isolation, skills, hooks, permissions, plugins |
| [Codex](docs/codex.md) | AGENTS.md chain, skills, code review rules, long-horizon tasks, `codex exec` (from the OpenAI developers blog) |
| [Workflows](docs/workflows.md) | TDD, parallel worktrees, review, debugging, refactors |
| [Skills & harness engineering](docs/skills-and-harness.md) | Designing skills, tools, and feedback loops |
| [Evaluating agents](docs/evaluation.md) · [skill routing evals](evals/) | Measuring whether your setup got better |
| [Landscape](docs/landscape.md) | What we learned from superpowers, everything-claude-code, anthropics/skills, spec-kit, and others |
| [Resources](resources.md) | Curated links and papers |

## Repository layout

```
.claude-plugin/          Claude Code plugin + marketplace manifests
.codex-plugin/           Codex plugin manifest   ·   .agents/plugins/  Codex marketplace
skills/                  Agent Skills (shared by Claude Code and Codex)
agents/                  Subagent definitions (orchestrator, supervisor, workers, reviewer)
hooks/                   hooks.json + guard.py
templates/ml-project/    ML project skeleton (rendered by `new`)
templates/agent-config/  AGENTS.md, CLAUDE.md, task board, wave runner (rendered by `new`/`init`)
templates/prompts/       Copy-paste prompts and checklists
scripts/                 playbook.py (scaffolder) · init.sh (one-line installer)
tests/                   Tests for manifests, skills, hooks, and the scaffolder
evals/                   Skill-routing eval cases
```

## Develop

```bash
python3 -m unittest discover -s tests -v   # playbook tests
claude plugin validate .                   # plugin manifest
```
CI also scaffolds a fresh ML project and runs its gates end to end.

## Contributing

Tips and skills should be **specific, tested, and tool-labelled** (✅ both / 🟠 Claude Code / 🔵 Codex). Date anything version-specific. Add a routing eval case for every new skill.

MIT licensed. Inspired by the projects listed in [docs/landscape.md](docs/landscape.md); all content here is original.
