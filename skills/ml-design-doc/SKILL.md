---
name: ml-design-doc
description: Write a one-page-to-few-page ML design doc (decision, metrics, data, approach, validation, serving, risks) from the template in assets/, before an ML epic is decomposed into tasks. Use when starting a new ML system or a major model change, or when asked for a design doc or proposal. Not for small features inside an already-designed system.
---

# ML design doc

1. Copy `assets/ml-design-doc-template.md` to `docs/design/<slug>.md`.
2. Fill sections in this order — each one constrains the next: **Decision & motivation → Success metrics → Data → Baseline → Approach → Validation → Serving & monitoring → Risks**.
3. Keep it short: every sentence should change a decision or a task. Use tables for metrics and data sources.
4. Write "Open questions" for anything a human must decide (metric trade-offs, data access, launch criteria). Don't guess them.
5. End with milestones that map 1:1 to `tasks/EPIC.md` milestones, each with a command that proves it's done.

Review checklist before handing off:
- [ ] The decision the model supports and the cost of each error type are explicit.
- [ ] A non-ML or simple baseline is defined and measurable.
- [ ] Label definition, prediction time, and feature availability at prediction time are stated.
- [ ] Split strategy matches production (time-based / grouped).
- [ ] Offline metric target + online guardrails + latency/cost budget are numbers, not adjectives.
- [ ] Training/serving skew and feedback-loop risks are addressed.
