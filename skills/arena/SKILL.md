---
name: arena
description: Run N parallel attempts at the same design-heavy task in separate worktrees (different models or prompts), judge them against a hidden rubric with a judge on a different model, pick the strongest as the base, graft the best ideas from the others, and verify the result. Use when one attempt would lock in the wrong shape - a new pipeline structure, feature-engineering approach, evaluation harness, or data model with no precedent. Not for routine tasks or when the right approach is already clear.
---

# Arena

1. **Frame.** State the artifact every candidate produces and write a rubric of 3-6 concrete, gradeable criteria (e.g. "train/serve feature code is shared, not duplicated"; "make gate passes"; "no new dependency"). The rubric is for the judge and you only - candidates see the task, not the rubric.
2. **Fan out.** Launch N (2-4) workers in the background with the *same* task prompt, each in its own worktree on `task/<id>-alt-<k>` (worker subagents with `isolation: worktree`, or headless runners). Vary the model (`model:` / `--model`) when the choice is judgment-heavy. Each candidate also writes a short rationale: alternatives considered and why rejected.
3. **Cross-judge.** After *all* candidates finish, run one read-only judge on a different model family than yours (e.g. `codex exec --sandbox read-only -` with the rubric and candidate branches by neutral label). It scores each criterion and recommends a base.
4. **Pick a base.** Read every candidate end to end and score them criterion by criterion yourself. Agreement with the judge confirms the pick; disagreement means a bias or an ambiguous rubric - reread both rationales. Prefer the one a future maintainer can extend most safely; when tied, the smaller surface.
5. **Graft.** Bring the strongest specific ideas from the other candidates into the base branch, one at a time, re-running the gates after each.
6. **Verify** the synthesised result with `prove-it-works`, then send it through the supervisor as usual. Delete the losing worktrees.
7. **Record** the pick, the grafts, and the judge's verdict in the task file and the decision log.

Adapted from the arena skill in Lauren Tan's pstack.
