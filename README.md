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
| **MLOps team** | `mlops-engineer` (worker: tracking, registry, CI/CT, monitoring) · `eda-analyst` · `monitoring-analyst` |
| **Model evaluators** | `regression-evaluator` · `classification-evaluator` · `forecasting-evaluator` · `bayesian-mmm-evaluator` · `survival-evaluator` (+ `ranking-ctr-specialist`), routed by `task_type` via the `model-evaluation` skill — `new --task-type forecasting` etc. ([details](docs/ml-specialists.md#model-type-evaluators)) |
| **ML specialists** | `ml-problem-framer` · `experiment-scientist` · `training-debugger` · `error-analyst` · `ranking-ctr-specialist` · `llm-eval-engineer` · `ml-production-auditor` · `ab-test-analyst` — grounded in Google's Rules of ML, ML Test Score & Tuning Playbook, Karpathy, Hamel Husain, Kohavi, and Facebook/Google CTR papers ([details](docs/ml-specialists.md)) |
| **Skills** (Claude Code + Codex) | Team: `orchestrate-team`, `feature-spec`, `worker-protocol`, `merge-train`, `decision-log`, `pause-and-resume` · Trust: `prove-it-works`, `encode-lesson` · ML: `ml-design-doc`, `ml-quality-gates`, `data-contract`, `eval-regression`, `experiment-protocol` · Evaluation: `model-evaluation` · MLOps: `eda-workflow`, `feature-selection`, `mlflow-lifecycle`, `production-monitoring` · Engineering: `plan-first`, `tdd-loop`, `verify-before-done`, `systematic-debugging`, `encode-lesson` |
| **Guardrail hooks** | Block `git push`/`reset --hard`/remote-data ops; protect `.env`, `data/raw/`, gate thresholds, and metric baselines; auto-format edits |
| **ML project skeleton** | `src/<pkg>/{data,analysis,features,models,evaluation,registry,monitoring}`, data contracts, split-before-fit pipeline, known-answer metric tests, `configs/`, CI |
| **MLOps lifecycle** (MLflow) | `make eda` → `select` → `tune` → `train` (MLflow run + registered version) → `gate` → `promote` (champion vs challenger, overall + per slice; `APPROVE=1` by a human) → `monitor` (KS/χ² or Wasserstein/JS drift + PSI, retrain policy, exit 3) → `rollback`; MLflow MCP server in `.mcp.json`; scheduled `monitor.yml` ([details](docs/ml-lifecycle.md)) |
| **Quality gates** | `make check` (ruff, mypy, pytest) · `make data-check` (contracts) · `make gate` (metrics vs committed baseline with per-metric tolerance + leakage "suspicious gain" warning) |
| **Trust before parallelism** | Workers start at 1 and earn more (`scripts/agent-team/audit.py trust`): clean first-round approvals raise the limit, reverts and human rework lower it. Proof runs through a **pipeline map** (`docs/pipeline-map/`: every entry point - data, training, evaluation, promotion, scoring, monitoring - with the evidence that counts), and every decision lands in a TSV trail (`.audit/decisions.tsv`). After Lauren Tan's pstack ([details](docs/agent-team.md#trust-before-parallelism)) |
| **Task board** | `tasks/EPIC.md` (frozen spec), `tasks/BOARD.md`, one `T-NNN-*.md` per task with owned files and command-checkable acceptance criteria |
| **Headless runner** | `scripts/agent-team/run-wave.sh T-001 T-002` — one `claude -p` or `codex exec` per task, each in its own worktree |
| **Context files** | `AGENTS.md` (shared, with Code Review Rules for leakage/reproducibility) + `CLAUDE.md` → `@AGENTS.md` |

How the team works: **[docs/agent-team.md](docs/agent-team.md)**.

## Install options

| Use case | Command |
|---|---|
| New ML project | `playbook.py new <dir> --name <name> [--bootstrap]` |
| Databricks ML project | `playbook.py new <dir> --name <name> --platform databricks [--catalog c --schema s]` |
| Genie Code skills bundle | `playbook.py init <dir> --target genie-code` |
| Existing repo | `playbook.py init <dir>` — never overwrites; writes `AGENTS.playbook.md` if you already have `AGENTS.md`, merges `.claude/settings.json` |
| Update vendored files | `playbook.py sync <dir>` — updates untouched files, skips ones you edited (`--force` to overwrite) |
| Claude Code plugin only | `/plugin install agent-playbook --marketplace mj2tang/coding-agent-playbook` (or `/plugin marketplace add mj2tang/coding-agent-playbook` then `/plugin install agent-playbook@mj2tang`) |
| Codex marketplace | `codex plugin marketplace add mj2tang/coding-agent-playbook` |

`--mode vendor` (default) copies skills, agents, and hooks into the repo so the whole team gets them through git. `--mode plugin` enables the Claude Code plugin via project settings instead (skills are still copied to `.agents/skills/` for Codex).

## Use it in a Claude Code project

1. **Scaffold** a new project (or add the team to an existing repo):
   ```bash
   curl -fsSL https://raw.githubusercontent.com/mj2tang/coding-agent-playbook/main/scripts/init.sh \
     | bash -s -- new churn-model --name churn-model --bootstrap     # new
   curl -fsSL .../scripts/init.sh | bash -s -- init .                 # existing repo
   ```
   This writes `CLAUDE.md` (→ `@AGENTS.md`), `.claude/agents/` (team + specialists), `.claude/skills/` (symlink to `.agents/skills/`), `.claude/settings.json` (permissions + guard hooks), `.mcp.json` (MLflow MCP), `tasks/`, and `configs/team.json`.
   *Plugin alternative:* `init . --mode plugin` enables the `agent-playbook` plugin via project settings instead of copying agents and hooks; teammates are prompted to install it when they trust the folder.
2. **Open the project** and trust the folder: `cd churn-model && claude`. Approve the `mlflow-mcp` server when prompted (`/mcp` to check).
3. **Frame the work** (optional but recommended): `> Use the ml-problem-framer agent to write a design doc for <goal>`, then fill `tasks/EPIC.md` from it.
4. **Run the team**: `claude --agent orchestrator` → `> Build tasks/EPIC.md as a team.` The orchestrator writes task files, dispatches workers (each in its own worktree), sends each branch to the supervisor, and merges with the merge train.
5. **Trust the folder once, then go headless**: headless runs (`claude -p`, `run-wave.sh`) ignore the project's allow rules until you've opened `claude` interactively in the project and accepted the trust dialog.
   **Headless / overnight**: `scripts/agent-team/run-wave.sh T-001 T-002 T-003` (one `claude -p` per task), then review with the supervisor.
6. **Promote and monitor**: `make promote` → review → `make promote APPROVE=1`; `make monitor CURRENT=batch.csv`; set `MONITOR_BATCH_PATH` for the scheduled workflow.
7. **Keep up to date**: `scripts/init.sh` … `sync .` updates vendored skills/agents/hooks without overwriting your edits.

## Use it in a Codex project

1. **Scaffold** exactly as above (`new` or `init`). Codex reads the same files: `AGENTS.md` (instructions + Code Review Rules) and `.agents/skills/` (all playbook skills, discovered automatically).
2. **Trust the project** and start Codex in it: `cd churn-model && codex`. Type `$` or `/skills` to see the skills; name a skill explicitly for fixed workflows, e.g. `$orchestrate-team build tasks/EPIC.md`.
3. **Connect MLflow** (optional):
   ```bash
   codex mcp add mlflow-mcp --env MLFLOW_TRACKING_URI=sqlite:///mlflow.db --env MLFLOW_MCP_TOOLS=all \
     -- uv run --with "mlflow[mcp]>=3.5.1" mlflow mcp run
   ```
4. **Parallel workers**: `RUNNER=codex scripts/agent-team/run-wave.sh T-001 T-002` runs one `codex exec --sandbox workspace-write` per task, each in its own worktree. Role prompts live in `.claude/agents/*.md` — they're plain markdown, so you can hand them to Codex directly, e.g. supervisor review:
   ```bash
   codex exec --sandbox read-only "Act as the supervisor defined in .claude/agents/supervisor.md. Review branch task/T-001-<slug> against tasks/T-001-<slug>.md."
   ```
5. **Code review**: Codex review (`@codex review` on GitHub) applies the `## Code Review Rules` in `AGENTS.md` (leakage, reproducibility, evaluation integrity, data boundaries).
6. **Plugin alternative**: `codex plugin marketplace add mj2tang/coding-agent-playbook` registers this repo's Codex marketplace (skills only; install from the Codex app).
7. **Guardrails**: Codex doesn't run the Claude hooks; rely on `--sandbox` modes, keep network off unless needed, and keep the "Needs human approval" list in `AGENTS.md`.

## Use it on Databricks

- **Agent team through Unity Gateway:** `ug claude --agent orchestrator`; headless workers with `RUNNER=ug-claude` (or `ug-codex`) `scripts/agent-team/run-wave.sh T-001 T-002` — models, limits, and usage governed by Databricks AI Gateway.
- **Genie Code:** `playbook.py init <dir> --target genie-code` → skills for `.assistant/skills/` (team-only skills left out, `make` steps translated to notebook/job equivalents) + `AGENTS.md`; upload with `genie-code/upload.sh`.
- **Databricks ML template:** `playbook.py new <dir> --name <project> --platform databricks --catalog <c> --schema <s>` → Unity Catalog data and models (`catalog.schema.model`, same aliases), MLflow on Databricks, an asset bundle with `train` / `monitor` / `promote_approve` / `rollback` jobs, and `ug` setup for MCP servers and UC skills.

Details, prerequisites, and limits: **[docs/databricks.md](docs/databricks.md)**.

## Keeping the playbook current

`.github/workflows/watch-sources.yml` checks the OpenAI developers blog (official RSS) and MLflow releases every Monday, opens an issue listing new posts, and — if an `ANTHROPIC_API_KEY` secret is set — has Claude draft a PR updating `docs/codex.md`, skills, and `resources.md` for human review. Add feeds in `watch/sources.json`.

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
| [Databricks](docs/databricks.md) | Unity Gateway (`ug`) runners, Genie Code bundle, Databricks ML template (Unity Catalog, asset bundle jobs) |
| [ML lifecycle (MLOps)](docs/ml-lifecycle.md) | EDA → features → selection → tuning → training → validation → promotion → monitoring → retraining; MLflow conventions; maturity levels |
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
templates/platforms/     Databricks overlay (bundle, UC config, ug setup) and Genie Code bundle files
templates/prompts/       Copy-paste prompts and checklists
scripts/                 playbook.py (scaffolder) · init.sh (one-line installer) · watch_sources.py (feed watcher)
watch/                   Feeds to watch + seen-items state
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
