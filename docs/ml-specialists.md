# ML specialist agents

Eight advisory agents that bring practitioner methods from Google, Meta, Microsoft, Amazon, and leading ML engineers into the agent team. They **advise and write reports** (design docs, audits, experiment and error-analysis write-ups); workers still own the code, and the supervisor still gates merges.

| Agent | When the orchestrator calls it | Method it encodes | Primary sources |
|---|---|---|---|
| `ml-problem-framer` | New system/epic; unclear objective | Decision → error costs → heuristic baseline → observable proxy objective → data/label/split definitions → design doc | Zinkevich *Rules of ML* (Google); Eugene Yan *ml-design-docs* (Amazon); Chip Huyen *Designing ML Systems* |
| `experiment-scientist` | Choosing models, features, hyperparameters | Scientific vs nuisance vs fixed hyperparameters; quasi-random search; boundary and curve checks; isolation plots; seed noise floor | Google *Deep Learning Tuning Playbook* (Godbole, Dahl, Gilmer, Shallue, Nado) |
| `training-debugger` | Training fails, is unstable, or underperforms | Inspect data → init-loss check → dumb baselines → overfit a tiny batch → dependency check → one change at a time → regularise | Karpathy *A Recipe for Training Neural Networks*; Tuning Playbook instability FAQ |
| `error-analyst` | Metrics plateau; planning the next wave | Read mistakes → open coding → failure taxonomy → quantify by category/slice → root cause → next task | Hamel Husain *Your AI Product Needs Evals*; Andrew Ng error analysis; *Rules of ML* #26, #41 |
| `ranking-ctr-specialist` | Ads, ranking, recommenders, CTR/CVR | Normalized entropy + calibration, position/selection bias, freshness, delayed feedback, downsampling correction, serving parity | He et al. 2014 (Facebook); McMahan et al. 2013 (Google); Chapelle et al. 2014 (Criteo) |
| `llm-eval-engineer` | LLM components (generation, RAG, agents) | Assertions → trace review → LLM judge aligned to human labels → A/B; failures become tests | Hamel Husain; OpenAI *Testing Agent Skills with Evals* |
| `ml-production-auditor` | Before launch / major release; periodically | ML Test Score (28 tests, 4 categories, score = min category) + hidden-technical-debt and skew checks | Breck, Cai, Nielsen, Salib, Sculley 2017 (Google); Sculley et al. 2015 (Google) |
| `ab-test-analyst` | Online tests of model changes | OEC + guardrails, power, randomisation unit; SRM, A/A, peeking, novelty, Twyman's law before interpretation; CUPED | Kohavi, Tang, Xu *Trustworthy Online Controlled Experiments*; Deng et al. 2013 (Microsoft) |

## How they fit the team

```
ml-problem-framer ──► design doc ──► orchestrator plans tasks ──► workers build ──► supervisor gates
        ▲                                   │        ▲
        │                 experiment-scientist / training-debugger / error-analyst / ranking-ctr-specialist / llm-eval-engineer
        │                                   ▼
ml-production-auditor ◄── release candidate ──► ab-test-analyst (online test) ──► ship / iterate
```

## What we reviewed in popular agent repos (Nov 2026)

| Repo | ML agents found | Assessment |
|---|---|---|
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | `mle-reviewer`, `mle-workflow` skill, `pytorch-build-resolver`, `rag-pipeline-reviewer` | Strongest of the set: decision/mistake-budget framing, point-in-time joins, promotion discipline. Its framing ideas shaped `ml-problem-framer` and the supervisor. |
| [wshobson/agents](https://github.com/wshobson/agents) | `llm-finetuning-{architect,training-engineer,eval-engineer}`, `ai-engineer`, `prompt-engineer` | Solid LLM fine-tuning lifecycle; narrower than classical ML. |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | `ml-engineer`, `mlops-engineer`, `data-scientist`, `nlp-engineer`, `llm-architect`, `ab-test-analysis` | Broad coverage but mostly keyword checklists ("Training time < 4 hours", "Feature stores") with little method. |
| [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | `ml-engineer`, `mlops-engineer`, `model-evaluator`, `computer-vision-engineer` | Similar generic style. |

The gap these repos leave — *method* from people who ran ML in production — is what the specialists above fill. All agent text here is original and paraphrases the cited sources.

## Further reading
- [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) · [Deep Learning Tuning Playbook](https://github.com/google-research/tuning_playbook) · [ML Test Score](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/) · [Hidden Technical Debt in ML Systems](https://papers.nips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html)
- [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) · [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) · [Trustworthy Online Controlled Experiments](https://experimentguide.com/) · [ml-design-docs](https://github.com/eugeneyan/ml-design-docs) · [Stas Bekman, ML Engineering (large-scale training)](https://github.com/stas00/ml-engineering)
