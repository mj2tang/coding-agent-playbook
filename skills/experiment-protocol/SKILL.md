---
name: experiment-protocol
description: Run ML experiments so results are comparable and reproducible - hypothesis, fixed config and seed, one change at a time, logged metrics, and a short write-up. Use when trying a new model, feature, or hyperparameter setting rather than shipping a known change. Not for shipping a known change - use the task board and gates.
---

# Experiment protocol

1. **Hypothesis:** one sentence — "Adding 7-day lag features improves valid ROC-AUC by ≥ 0.005."
2. **Config:** copy the base config to `configs/experiments/<date>-<slug>.yaml`; change one thing.
3. **Run** with a fixed seed (and 3 seeds if the expected effect is small); log params + metrics (MLflow or `experiments/log.jsonl`).
4. **Compare** to the baseline on the *validation* split only. Never peek at test until the final decision.
5. **Write up** in `experiments/<date>-<slug>.md`: hypothesis, change, results table, decision (adopt / reject / follow-up).
6. **Adopt** by turning the winning experiment into a normal task with tests and gates — experiment code is not production code.
