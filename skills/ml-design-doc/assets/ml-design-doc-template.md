# <System name>: ML design doc

Status: draft | review | approved · Owner: <name> · Last updated: <date>

## 1. Decision & motivation
- What decision or action uses the prediction? Who/what acts on it, how often, with what latency?
- What happens today without ML (the current heuristic or manual process)?
- Why now, and what is the expected impact?

## 2. Success metrics
| Type | Metric | Split / population | Baseline | Target |
|---|---|---|---|---|
| Offline (primary) | | valid (time-based) | | |
| Online (OEC) | | A/B test | | |
| Guardrails | latency p99, cost per 1k predictions, ... | | | must not regress |

Cost of errors: false positive = <...>; false negative = <...>; abstain/fallback = <...>.

## 3. Scope
- In scope:
- Out of scope / non-goals:

## 4. Data
| Source | Grain | Freshness | Owner | Contract |
|---|---|---|---|---|

- Label definition and label delay:
- Prediction time and features available at that time:
- Split strategy (time / group) and why:
- Known biases, PII/sensitive fields, retention:

## 5. Baseline
The simplest thing that could ship (rule, heuristic, linear model) and its measured performance.

## 6. Approach
- Candidate models and why; features (and which are reused heuristics):
- Training: objective, sampling (and correction), cadence/freshness:

## 7. Validation
- Offline evaluation protocol, seeds/noise floor, slices that must not regress:
- Error analysis plan:
- Online experiment plan (randomisation unit, duration, power):

## 8. Serving & monitoring
- Batch vs online; latency/throughput budget; fallback behaviour:
- Training/serving parity (shared feature code, logged serving features):
- Monitoring: data invariants, skew, staleness, prediction quality, alert owners; rollback plan:

## 9. Risks & open questions
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|

Open questions for decision-makers:
-

## 10. Milestones
1. <milestone> — done when: `<command>` shows <result>

## References
- Structure adapted from Eugene Yan's ml-design-docs template and Google design-doc practice.
