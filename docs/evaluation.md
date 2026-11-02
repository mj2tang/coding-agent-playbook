# Evaluating agents

How to tell whether a new prompt, skill, model, or tool actually helped.

- **Build a small task set** from your real work: 10–30 tasks with a clear pass/fail check (tests, expected output).
- **Measure outcomes, not vibes:** pass rate, number of human interventions, time to green, diff size, cost.
- **Change one thing at a time** and rerun the set; agent runs are noisy, so run more than once.
- **Check the trajectory, not just the result:** did it take dangerous actions, loop, or ignore instructions?
- **Use LLM-as-judge carefully:** good for rubric checks (did it follow the style guide?), backed by deterministic checks where possible.

See evaluation links in [resources.md](../resources.md#evaluation).
