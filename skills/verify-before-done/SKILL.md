---
name: verify-before-done
description: Before claiming work is complete, run the project's verification commands and report actual output - build, lint, types, tests, and ML gates. Use at the end of every task, before committing, and before opening a PR. Not needed for read-only questions.
---

# Verify before done

Run, in order, and stop at the first failure:

```bash
make check        # lint + types + unit tests
make data-check   # if data code changed
make gate         # if model/feature/eval code changed
git status && git diff --stat
```

Then report:
- Each command and whether it passed (paste the failing lines if not).
- What you did **not** verify and why.

For anything beyond a small edit, also follow `prove-it-works`: cover every affected entry point in `docs/pipeline-map/` and record the evidence.

Never write "done", "fixed", or "all tests pass" without having run the commands in this session.
