# Data loading and contracts

## What it is
`src/{{pkg}}/data/load.py` reads the source configured in `configs/*.yaml → data` and validates it against `data/contracts.py` before anything else runs.

## How to reach it
- `make data-check` (contract tests on fixtures)
- Any training/eval/monitoring entry point calls `load_dataset` first.

## Evidence that counts
- `make data-check` output, plus a real load: `uv run python -c "from {{pkg}}.data.load import load_dataset; from {{pkg}}.config import load_config; print(load_dataset(load_config('configs/base.yaml')).shape)"` with the row count you expect.

## What usually lies
- Fixture tests pass while the real source has new columns or nulls — always do one real load.
- Contracts checked after a silent `dropna` — the count of dropped rows is the evidence, not the clean frame.
