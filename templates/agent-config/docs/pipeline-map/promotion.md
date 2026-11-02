# Promotion (champion / challenger)

## What it is
`make promote` compares the newest version with `@champion`, overall and per slice, and sets `@challenger` on pass. `APPROVE=1` (human) moves `@champion`.

## How to reach it
- `make promote` · `make promote APPROVE=1` (human) · `make rollback` (human)

## Evidence that counts
- The comparison tables and `PROMOTION: PASS/FAIL`, plus the alias state afterwards (`@challenger` → version N).

## What usually lies
- Comparing against a champion trained on different data — check both versions' run configs.
- A pass overall that hides a slice regression — read the slice section.
