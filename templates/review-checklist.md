# Reviewing agent-written diffs

- [ ] Does it do what was asked — and *only* that? (watch for drive-by refactors)
- [ ] Do tests actually exercise the new behaviour, or were they weakened/skipped?
- [ ] Edge cases: empty input, nulls, concurrency, large data, error paths
- [ ] Any invented APIs, config keys, or library functions? (verify they exist)
- [ ] Security: injection, secrets in code/logs, auth checks, unsafe deserialisation
- [ ] Dependencies added? Needed and pinned?
- [ ] Comments and naming match surrounding code
- [ ] Ran it yourself at least once
