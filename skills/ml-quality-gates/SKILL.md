---
name: ml-quality-gates
description: Quality checklist and gate commands for ML code - leakage, reproducibility, data validation, test coverage of transforms, and metric regression against a baseline. Use before declaring any ML change done, when reviewing ML code, or when setting up CI for an ML project. Not for docs-only or tooling-only changes.
---

# ML quality gates

## Commands (from the project Makefile)
| Gate | Command | Fails when |
|---|---|---|
| Static + unit | `make check` | lint, type, or unit test failure |
| Data | `make data-check` | a data contract is violated |
| Model | `make gate` | eval metric worse than baseline beyond tolerance in `configs/gates.json` |

## Review checklist
**Leakage**
- [ ] Train/valid/test split happens *before* any fit (scalers, encoders, imputers, feature selection).
- [ ] No target, label-derived, or post-outcome columns in features; time-series features use only past data.
- [ ] Group/entity leakage handled (same user/customer not across splits when it matters).

**Reproducibility**
- [ ] Seeds set for Python, NumPy, and the ML framework; passed explicitly, not global-only.
- [ ] Hyperparameters and paths in `configs/`, not hard-coded.
- [ ] Same command + config + data → same metrics (within tolerance).

**Correctness**
- [ ] Shapes, dtypes, and value ranges asserted at module boundaries.
- [ ] Metrics computed on the intended split, with the right averaging (macro/micro/weighted).
- [ ] NaN/inf handled explicitly, never silently dropped without a count.

**Tests**
- [ ] Every transform has a tiny-data unit test with a hand-checked expected output.
- [ ] A smoke test trains end-to-end on fixtures in seconds.
- [ ] No tests skipped, xfailed, or loosened in this change.

**Hygiene**
- [ ] No large data, model binaries, secrets, or notebook outputs committed.
- [ ] Notebooks are exploration only; logic lives in `src/`.
