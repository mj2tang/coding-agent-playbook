#!/usr/bin/env python3
"""Compare current metrics to the committed baseline using configs/gates.json. Exit 1 on regression."""

import argparse
import json
import sys
from pathlib import Path

from {{pkg}}.evaluation.gates import compare_metrics, format_table


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--current", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--rules", required=True)
    a = p.parse_args()
    if not Path(a.baseline).exists():
        print(f"No baseline at {a.baseline}. A human should run `make rebaseline` and commit it.")
        return 1
    current = json.loads(Path(a.current).read_text())
    if str(current.get("git_sha", "")).endswith("-dirty"):
        print(
            "warning: metrics were computed on uncommitted changes (git_sha ends in -dirty); "
            "commit, then re-run before using them as proof"
        )
    cur = current["metrics"]
    base = json.loads(Path(a.baseline).read_text())["metrics"]
    rules = json.loads(Path(a.rules).read_text())["metrics"]
    passed, rows = compare_metrics(cur, base, rules)
    print(format_table(rows))
    if any(r.status == "SUSPICIOUS GAIN" for r in rows):
        print("warning: suspiciously large gain - check for leakage before celebrating")
    print("GATE:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
