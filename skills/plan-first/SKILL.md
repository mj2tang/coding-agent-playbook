---
name: plan-first
description: Explore the codebase read-only and produce a concrete step-by-step plan (files, changes, verification per step) for approval before writing code. Use for any change larger than a small, obvious edit. Not for trivial, single-file edits.
---

# Plan first

1. **Explore** read-only: entry points, the modules involved, existing patterns and tests.
2. **Write the plan:**
   - Goal and non-goals
   - Steps, each with: files touched, the change, how to verify it (command + expected result)
   - Risks / open questions
3. **Stop for approval.** Do not edit files until the plan is accepted.
4. While implementing, if reality diverges from the plan, update the plan and say so — don't silently improvise.
