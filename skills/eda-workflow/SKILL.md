---
name: eda-workflow
description: Exploratory data analysis before modelling - automated profile (make eda), then targeted human-style inspection of distributions, missingness, duplicates, target balance, and leakage/ID suspects, written up as findings that feed the design doc and data contracts. Use when starting on a new dataset, after a data source changes, or before feature work. Not for monitoring production batches (use production-monitoring).
---

# EDA workflow

Work on the **training split only** — never explore validation/test data.

1. `make eda` → `reports/eda.md` (shape, dtypes, missing %, cardinality, duplicates, target balance, single-feature AUC, leakage/ID/constant flags).
2. **Inspect, don't just summarise.** Look at raw rows: sort by extreme values, sample per class, check timestamps and units. Outliers often reveal pipeline bugs.
3. **Leakage hunt:** any feature with single-feature AUC ≥ 0.98, ID-like columns, timestamps after the prediction time, or columns derived from the label → confirm and exclude.
4. **Data quality → contracts:** every invariant you discover (ranges, allowed categories, non-null) becomes a rule in `data/contracts.py` with a test (`data-contract` skill).
5. **Questions for the design doc:** label definition, class balance implications for metrics, segments that may need slice metrics.
6. Write findings to `experiments/<date>-eda.md`: what you looked at, what you found, decisions (exclude X, add contract Y, slice by Z).

Notebooks are fine for looking; anything reusable moves to `src/<pkg>/analysis/` with a test.
