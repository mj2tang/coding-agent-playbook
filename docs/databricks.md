# Databricks

Three ways to use the playbook on Databricks, from lightest to fullest. They combine: most teams use all three.

| | What runs | Where the playbook plugs in |
|---|---|---|
| **1. Agents through Unity Gateway (`ug`)** | Claude Code / Codex on your machine, with models, rate limits, and usage governed by Databricks Unity AI Gateway | `ug claude --agent orchestrator`; `RUNNER=ug-claude` / `ug-codex` in `run-wave.sh`; MCP servers and Unity Catalog skills via `ug mcp add` / `ug skills add` |
| **2. Genie Code** | Databricks' built-in agent, in notebooks (Agent mode) | `playbook.py init <dir> --target genie-code` → skills for `.assistant/skills/` + `AGENTS.md` for the Git folder |
| **3. Databricks ML template** | Training, promotion, and monitoring as Databricks jobs on Unity Catalog data and models | `playbook.py new <dir> --name <project> --platform databricks --catalog <c> --schema <s>` |

`ug` is the Unity Gateway CLI (the earlier `ucode` commands still work). Install it with
`uv tool install git+https://github.com/databricks/unity-gateway` (Python 3.12+, `uv`).

## 1. Agent team through Unity Gateway

```bash
ug claude --agent orchestrator                          # interactive team lead, through AI Gateway
RUNNER=ug-claude scripts/agent-team/run-wave.sh T-001 T-002   # headless workers: ug claude -p ...
RUNNER=ug-codex  scripts/agent-team/run-wave.sh T-003         # headless Codex: ug codex exec ...
ug usage                                                 # 7-day usage summary
```

- `ug` forwards extra arguments to the agent, so `-p`, `--agent`, `--permission-mode`, and `codex exec` flags work unchanged. You can also set `"headless_runner": "ug-claude"` in `configs/team.json`.
- The project's `.claude/` agents, skills, settings, and guard hooks still apply — it's the same Claude Code.
- **Check managed settings:** `ug` writes system-level managed settings (`/etc/claude-code/managed-settings.json`, `/etc/codex/managed_config.toml`). Managed settings outrank project settings; confirm the playbook's permissions and hooks still apply (`/permissions`, `/hooks` in Claude Code).
- **Platform skills:** install Databricks' official skills (bundles, jobs, Unity Catalog, MLflow, model serving) with `databricks aitools install`. They complement the playbook: the playbook brings team process and ML method, the official skills bring Databricks API know-how. Uninstall AI Dev Kit skills first to avoid conflicts.
- **MCP and shared skills:** `scripts/databricks/setup-agents.sh` (template) runs `ug mcp add` for Databricks SQL and the schema's UC functions, and `ug skills add --location <catalog>.<schema> --path $PWD` to pull team skills published in Unity Catalog.

## 2. Genie Code

```bash
python3 scripts/playbook.py init ./my-repo --target genie-code --name my-project
cd my-repo/genie-code && ./upload.sh user        # or: ./upload.sh workspace (admins; shared)
```

The bundle contains:
- `.assistant/skills/` — every playbook skill except the team-only ones (`orchestrate-team`, `worker-protocol`, `merge-train`). Skills that mention `make` get a table of notebook (`%sh`) and job equivalents.
- `AGENTS.md` — put it at the root of the Git folder Genie Code works in (Genie Code auto-discovers `AGENTS.md`/`CLAUDE.md`), with a note that the agent-team sections don't apply.
- `upload.sh` — `databricks workspace import-dir` into `/Users/<you>/.assistant/skills` or `Workspace/.assistant/skills`; or set `DEST=` for a custom folder registered in Genie Code settings.

**What doesn't transfer:** Genie Code is a single agent in the workspace — no subagents, git worktrees, or Claude hooks. Run team work from Claude Code or Codex via `ug`. Guardrails come from Unity Catalog and job permissions plus the "Needs human approval" list. Skill edits apply in new chats.

## 3. Databricks ML template

```bash
python3 scripts/playbook.py new churn --name churn --platform databricks --catalog ml --schema churn --bootstrap
```

Adds to the standard template:

| File | Purpose |
|---|---|
| `configs/databricks.yaml` | `extends: base.yaml`; data from Unity Catalog table `data.table` (contracts still validated); MLflow tracking `databricks`, registry `databricks-uc`; model `catalog.schema.<pkg>` |
| `databricks.yml`, `resources/*.yml` | Asset bundle: serverless wheel jobs `train` (train → promote gate, weekly), `monitor` (weekly drift on a scoring table; exit 3 fails the task → notification), `promote_approve` and `rollback` (human-run only). Dev target uses your own schema and pauses schedules |
| `pyproject.toml` | Console-script entry points (`<pkg>-train`, `-promote`, `-monitor`, ...) used by the wheel tasks; `databricks` extra (Databricks Connect, SDK) |
| `Makefile.databricks` | `make bundle-validate`, `bundle-deploy TARGET=dev`, `bundle-train`, `bundle-monitor`, `bundle-promote-approve`, `bundle-rollback`, `agents-setup` |
| `.mcp.json` | MLflow MCP server against the Databricks tracking server (`DATABRICKS_CONFIG_PROFILE`) |
| `scripts/databricks/setup-agents.sh` | Official skills, managed MCP servers, and UC-published skills via `ug` |
| `AGENTS.md` → `## Databricks` | Platform conventions and the human-approval list |

How names flow: bundle variables (`catalog`, `schema`, `training_table`, `scoring_table`) are passed to every entrypoint as `--set mlflow.registered_model=...` and `--set data.table=...`, so the same code runs locally (`configs/base.yaml`, SQLite MLflow) and on Databricks without edits. Unity Catalog models use the same `@challenger` / `@champion` / `@previous-champion` aliases and require a signature, which training already logs.

**First deploy:**
1. Set `workspace.host` for `dev` (and `prod`) in `databricks.yml`; `databricks auth login`.
2. Create the training and scoring tables in `<catalog>.<schema>` and adapt `data/contracts.py` to your columns.
3. `make bundle-validate && make bundle-deploy TARGET=dev && make bundle-train`.
4. Promote with `make bundle-promote-approve TARGET=dev` once the challenger looks right.

Local runs against Databricks data: `uv sync --extra databricks`, configure Databricks Connect, then `make train CONFIG=configs/databricks.yaml`.

## Prerequisites and limits (November 2026)
- Unity AI preview, UC Skills (beta), and Managed MCP Servers must be enabled by an admin; UC skills need a standard catalog with managed storage.
- Workspace MCP endpoints for AI Search, UC functions, and Genie bypass AI Gateway tracing, grants, and guardrails.
- The bundle follows Databricks' current serverless wheel-task examples but was validated structurally only; run `databricks bundle validate` against your workspace before deploying.
- Publishing playbook skills to the Unity Catalog skill registry happens through an agent calling `create_skill` on the `databricks-skill-registry` MCP server (`ug configure skills`), then sharing with READ VOLUME grants.

## Sources
- [Unity Gateway (`ug`)](https://github.com/databricks/unity-gateway) · [Coding agent MCP and skills](https://docs.databricks.com/gcp/en/ai-gateway/coding-agent-mcp-skills) · [Integrate with coding agents](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-integration-model-services)
- [Genie Code skills](https://docs.databricks.com/aws/en/genie-code/skills) · [Personalizing Genie Code](https://www.databricks.com/blog/personalizing-genie-code-instructions-skills-memory-and-mcp)
- [Unity Catalog Skills](https://docs.databricks.com/aws/en/agents/uc-skills/) · [Govern skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills) · [Agent skills for coding assistants](https://docs.databricks.com/aws/en/agent-skills/)
- [Databricks bundle examples](https://github.com/databricks/bundle-examples) · [MLflow model registry](https://mlflow.org/docs/latest/ml/model-registry/)
