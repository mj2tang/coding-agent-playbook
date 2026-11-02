#!/usr/bin/env python3
"""Compare current metrics to the baseline using per-metric rules. Exit 1 on regression."""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--current", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--rules", required=True)
    a = p.parse_args()
    if not Path(a.baseline).exists():
        print(f"No baseline at {a.baseline}. A human should run `make rebaseline` and commit it.")
        return 1
    cur = json.loads(Path(a.current).read_text())["metrics"]
    base = json.loads(Path(a.baseline).read_text())["metrics"]
    rules = json.loads(Path(a.rules).read_text())["metrics"]
    failed = False
    print(f"{'metric':<12} {'baseline':>10} {'current':>10} {'delta':>9}  status")
    for name, rule in rules.items():
        if name not in cur or name not in base:
            print(f"{name:<12} missing from current or baseline  FAIL")
            failed = True
            continue
        delta = cur[name] - base[name]
        worse = -delta if rule["direction"] == "higher" else delta
        status = "ok"
        if worse > rule["tolerance"]:
            status, failed = "REGRESSION", True
        elif "suspicious_gain" in rule and -worse > rule["suspicious_gain"]:
            status = "SUSPICIOUS GAIN (check for leakage)"
        print(f"{name:<12} {base[name]:>10.4f} {cur[name]:>10.4f} {delta:>+9.4f}  {status}")
    print("GATE:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
