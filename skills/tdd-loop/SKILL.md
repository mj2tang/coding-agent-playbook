---
name: tdd-loop
description: Red-green-refactor loop for agents - write a failing test from the requirement, confirm it fails for the right reason, implement the minimum to pass, then refactor with tests green. Use when implementing any feature or bug fix. Not for docs, config-only, or exploratory notebook work.
---

# TDD loop

1. **Red:** write the smallest test that captures the requirement. Run it; it must fail *for the expected reason* (not an import error).
2. **Green:** implement the minimum to pass. Run the test, then the module's suite.
3. **Refactor:** tidy names and structure; tests stay green.
4. Repeat per behaviour. For bugs, the first test reproduces the bug.

ML specifics: use tiny deterministic fixtures (5–50 rows), fixed seeds, and assert exact values for transforms and approximate values (`pytest.approx`) for models.

Never edit a test to make wrong code pass. If the test is wrong, say so explicitly and fix it in a separate step.
