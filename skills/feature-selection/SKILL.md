---
name: feature-selection
description: Select features with leakage-safe screens on the train split (near-constant, leakage suspects, correlated pairs) and confirm with permutation importance on validation (make select), then adopt the selection through config and gates. Use when adding many features, when a model is slow or unstable from redundant inputs, or before a release. Not for creating new features (use tdd-loop + feature-worker).
---

# Feature selection

1. `make select` → `reports/feature_selection.md`:
   - **near-constant** (top value ≥ 99% of rows), **leakage suspects** (single-feature AUC ≥ 0.98), **correlated** pairs (|r| ≥ 0.95, keep the one more related to the target) — all fitted on **train only**.
   - Survivors ranked by **permutation importance on validation** (model fitted on train).
2. Treat importances as evidence, not truth: correlated features share importance; re-check after dropping.
3. **Adopt** via a task: set `features.keep` in a config, run `make gate` with the new config, and require no regression beyond `configs/gates.json` tolerances (fewer features at equal quality is a win).
4. Record every drop and its reason in the task's decision log. Thresholds live in `configs/base.yaml → feature_selection`.
5. Never select features using validation *labels* in any step other than the final importance check, and never using test data.
