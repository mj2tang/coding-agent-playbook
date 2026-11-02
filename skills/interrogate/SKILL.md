---
name: interrogate
description: Adversarial multi-model review - send the same intent, diff, and rubric to reviewers on different model families (Claude, Codex, ...) via scripts/agent-team/panel_review.py, then synthesise - findings raised by two or more models are high-confidence, single-model findings lower confidence. Use for contested designs, high-stakes merges (data pipelines, promotion logic, anything touching gates), "challenge this", or "find blind spots". Not for routine small changes - the supervisor alone is enough.
---

# Interrogate

Diversity of models, not assigned personas, is what surfaces blind spots: models differ in priors and failure modes, so agreement across them is strong signal.

1. **State the intent** in one paragraph (from the task file, commits, or the user). Reviewers judge whether the change achieves the intent, not whether the intent is right. If the intent is unclear, ask first.
2. **Run the panel** (one command):
   `python3 scripts/agent-team/panel_review.py task/T-012-slug tasks/T-012-slug.md`
   Reviewers come from `configs/team.json → review_panel` (defaults: Claude Code in plan mode, Codex with a read-only sandbox). Each reads the diff itself; reviews land in `.audit/reviews/T-012-slug/`. Missing CLIs are skipped - with fewer than two reviewers the agreement signal is weak, say so.
3. **Read every review end to end**, then synthesise:
   - Group findings that point at the same problem (same file:line or same failure scenario).
   - **2+ models** → high confidence; **1 model** → read it, verify it yourself before acting.
   - Dismiss non-issues with a concrete reason; don't churn code for nitpicks.
4. **Verify before acting:** reproduce each high-confidence finding (a failing test, a command output) before asking a worker to fix it.
5. **Deliver a verdict**, not auto-applied changes: findings table (finding, models agreeing, severity, verified?), recommendation, and log it (`decision-log`, phase `review`, actor `panel`).

Adapted from the interrogate skill in Lauren Tan's pstack.
