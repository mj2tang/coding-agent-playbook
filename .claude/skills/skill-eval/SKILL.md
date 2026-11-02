---
name: skill-eval
description: Test whether a change to a skill or agent prompt actually improves agent behaviour with a blinded A/B eval - organic task prompts, sanitized project names, candidates unaware they are evaluated, a blind judge scoring anonymised submissions against a hidden rubric, and grading from what agents did (diffs, files touched) rather than what they claim. Use before promoting any edit to skills/, agents/, or AGENTS.md templates in this playbook (this skill lives in the playbook repo only, so it never appears inside candidate projects). Not for checking which skill gets triggered (use evals/skill-routing.jsonl).
---

# Skill eval (blinded A/B)

An agent that knows it is being evaluated behaves differently, so the candidates must not be able to tell.

## Blinding rules
- Nothing a candidate sees may say it is being tested: no "this is an eval/test", "you're being graded", "show me you follow...", "rubric", "judge", "variant A/B", or "which skills did you use". `scripts/skill_eval.py` refuses prompts with such phrases. Normal ML words (score, evaluation, experiment, benchmark, candidate model) are fine - they're part of real tasks.
- The prompt is what a real user would type ("add a Brier score to the evaluation"), not "show me you follow the worker protocol".
- Don't ask candidates to list the skills or rules they applied - that inflates citation behaviour. Grade from the diff and the files they actually touched.
- The judge sees submissions only by shuffled neutral labels and the rubric, never the variant or model.
- Compare both variants in one judge pass on one scale.

## Run it
```
python3 scripts/skill_eval.py --skill worker-protocol \
  --variant-a skills/worker-protocol --variant-b /path/to/edited/worker-protocol \
  --prompt-file evals/prompts/add-brier.txt --rubric evals/rubrics/worker-protocol.md --runs 3
```
Each run scaffolds a fresh project with a neutral name, installs the variant, runs the task with the configured runner (default `claude -p`), and saves the diff. The judge (default `claude -p --model opus`; prefer a different family than the runner, e.g. Codex) scores all submissions blind; `report.md` un-blinds and averages per variant.

## Decide
- Promote the edit only if variant B scores higher on the criteria it targets **and** doesn't regress others, across runs (look at per-run spread, not just the mean).
- Read the actual diffs of the best and worst submissions yourself; disagreement with the judge means a biased judge or an ambiguous rubric.
- Add the prompt and rubric to `evals/` so the next change to the same skill is measured the same way.

Adapted from the eval playbook in Lauren Tan's pstack and OpenAI's "Testing Agent Skills Systematically with Evals".
