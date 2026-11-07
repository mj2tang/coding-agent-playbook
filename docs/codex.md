# OpenAI Codex

🔵 Practices for [Codex](https://openai.com/codex/), drawn from the [OpenAI developers blog](https://developers.openai.com/blog/) and Codex docs, plus daily use. Dated November 2026 — check the docs for changes.

## AGENTS.md
- Codex builds an instruction chain once per run: `~/.codex/AGENTS.md` (or `AGENTS.override.md`), then one file per directory from the repo root down to the working directory. Closer files come later and win. Combined size is capped (`project_doc_max_bytes`, 32 KiB default).
- **Prune regularly.** Remove instructions that newer models follow anyway (e.g. "always run tests") — they cause over-testing and bloat.
- **Tie docs to situations**: "when changing a schema, read `docs/schema.md`" beats "read all docs before every edit".
- **Explicitly allow known-safe workflows** (local test suite, disposable data) so the agent doesn't stop to ask at every step; reserve "ask first" for genuinely irreversible actions.
- **Code review rules** go in a `## Code Review Rules` section (root or nested `AGENTS.md`). Good rules protect a consequential, non-obvious invariant, state the risk and a safe alternative, and describe outcomes rather than file names. Leave formatting to linters. Test a new rule on a PR with one violating change, one safe counterexample, and one unrelated change. Trigger with `@codex review`.

## Skills
- Codex discovers skills in `.agents/skills/` (from the working directory up to the repo root), `~/.agents/skills/`, and `/etc/codex/skills`. Invoke explicitly with `$skill-name` or `/skills`; otherwise Codex picks by description.
- **Descriptions are routing rules:** say when to use, when *not* to, and what success looks like. Add near-miss negatives — teams have seen ~20% routing gains from this.
- Keep `SKILL.md` a lean router; put templates, examples, and scripts in `references/`, `assets/`, `scripts/` so they load only when needed.
- Prefer goals and guidance over rigid step lists for strong models; keep fixed contracts (output formats, gate commands) explicit.
- For production workflows with a fixed contract, **name the skill in the prompt** rather than relying on implicit routing.
- Optional `agents/openai.yaml`: UI metadata, `policy.allow_implicit_invocation: false` for explicit-only skills, and `dependencies.tools`.

## Long-horizon tasks
- **Freeze the target** in a spec file: goals, non-goals, constraints, "done when" checks. (`tasks/EPIC.md` in this playbook.)
- **Milestones in a plan file**, each small enough for one loop, with validation commands.
- **Stop-and-fix:** if validation fails, repair before the next milestone.
- **Decision log + status log** in files so the agent doesn't reverse earlier choices and you can audit after stepping away.
- Use `/plan` to align before edits; steer mid-run instead of restarting.
- **Parallelise across threads, isolate with git worktrees** (`codex exec --worktree` or your own worktrees).

## Headless and CI
- `codex exec "<prompt>"` runs non-interactively; `--sandbox workspace-write` for implementation and for reviews that run gates (`read-only` only for diff-reading judges; `.git` is read-only in both, so headless Codex can't commit — `run-wave.sh` commits for it); `--add-dir` makes extra paths writable (worktrees, `uv cache dir`); `--json` emits an event trace you can assert on; `-C <dir>` sets the working root; `--output-schema` enforces structured output.
- This playbook's `scripts/agent-team/run-wave.sh` with `RUNNER=codex` runs one `codex exec` per task in its own worktree.

## Approvals and sandbox
- Least privilege that keeps you flowing: read-only to explore, workspace-write to implement, full access only inside an externally sandboxed environment.
- Keep network off unless a task needs it; allowlist the minimum domains.

## Plugins
- A Codex plugin bundles skills (and optionally MCP servers/hooks) with a `.codex-plugin/plugin.json`; a repo marketplace lives at `.agents/plugins/marketplace.json`.
- `codex plugin marketplace add mj2tang/coding-agent-playbook` registers this repo's marketplace.
- Plugin hooks run only after the user trusts them.

## Evaluating skills
- Start with 10–20 prompts per skill: explicit (names the skill), implicit (describes the task), noisy, and **negative** look-alikes that must not trigger it.
- Capture `codex exec --json` traces and write deterministic checks (did command X run, does file Y exist); add a model-graded rubric only for qualitative conventions.
- Turn every manual correction into a new eval case. See [`evals/skill-routing.jsonl`](../evals/skill-routing.jsonl).
