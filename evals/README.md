# Skill routing evals

`skill-routing.jsonl` holds prompts with the skill that should trigger (`expect`), or `null` when no playbook skill should load. Include explicit, implicit, and near-miss negative cases; add a case every time routing goes wrong in real use.

Run one case headless and inspect which skill loaded:

```bash
# Claude Code: stream-json shows Skill tool calls
claude -p "<prompt>" --output-format stream-json --verbose | grep -o '"skill":"[^"]*"'
# Codex: the --json event trace shows which SKILL.md was read
codex exec --json "<prompt>" | grep -o 'skills/[a-z-]*/SKILL.md' | sort -u
```
Score = fraction of cases where the loaded skill matches `expect` (and nothing loads for `null`). Re-run after editing any skill description.
