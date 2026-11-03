#!/usr/bin/env python3
"""Decision trail and trust ladder for the agent team.

  audit.py log <phase> <task> <actor> <decision> <why> <evidence> <result>
  audit.py trust            # how many workers the team has earned (prints the number)
  audit.py trust --explain  # level, streak, and the rows that moved it
  audit.py show [--last N]  # recent rows as an aligned table

The trail is a TSV (default ``.audit/decisions.tsv``, override with AUDIT_LOG): one row per
decision point - a dispatch, a verdict, a merge or revert, a pivot, a blocker. Evidence is a
pointer (commit, file:line, artifact path), never prose. It stays local by default; commit it
when a reviewer needs the trail to trust a large or unattended run.

Trust ladder: parallelism is earned, not configured. The team starts at ``trust.start_workers``.
Every ``trust.promote_after`` consecutive clean approvals raise the limit by one (up to
``trust.max_workers``); a revert or human rework drops it by one and resets the streak;
``changes_requested`` resets the streak only. Settings come from ``configs/team.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = ["ts", "phase", "task", "actor", "decision", "why", "evidence", "result"]
POSITIVE = {"approved"}
RESET = {"changes_requested"}
NEUTRAL = {
    "approved_after_rework",
    "merged",
    "blocked",
    "progress",
    "no_progress",
    "dispatched",
    "planned",
    "paused",
    "encoded",
    "started",
    "forced",
}
NEGATIVE = {"reverted", "human_rework"}
DEFAULT_TRUST = {"start_workers": 1, "max_workers": 3, "promote_after": 3}


def log_path() -> Path:
    """AUDIT_LOG if set; else .audit/decisions.tsv in the main checkout, so rows written from any
    git worktree (each worker runs in one) land in the same trail the trust ladder reads."""
    if "AUDIT_LOG" in os.environ:
        return Path(os.environ["AUDIT_LOG"])
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return Path(".audit/decisions.tsv")
    return Path(common).parent / ".audit" / "decisions.tsv"


def clean(cell: str) -> str:
    """Single-line cell; neutralise spreadsheet formula prefixes (=, +, -, @)."""
    text = " ".join(str(cell).replace("\t", " ").split())
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def append(row: dict[str, str], path: Path | None = None) -> None:
    path = path or log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        if new:
            w.writerow(COLUMNS)
        w.writerow([clean(row.get(c, "")) for c in COLUMNS])


def read(path: Path | None = None) -> list[dict[str, str]]:
    path = path or log_path()
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def trust_settings(team_json: Path = Path("configs/team.json")) -> dict[str, int]:
    cfg = dict(DEFAULT_TRUST)
    if team_json.exists():
        team = json.loads(team_json.read_text())
        cfg["max_workers"] = int(team.get("max_parallel_workers", cfg["max_workers"]))
        cfg.update({k: int(v) for k, v in team.get("trust", {}).items() if k in DEFAULT_TRUST})
    if not 1 <= cfg["start_workers"] <= cfg["max_workers"] or cfg["promote_after"] < 1:
        raise ValueError("need 1 <= start_workers <= max_workers and promote_after >= 1")
    return cfg


def trust_level(rows: list[dict[str, str]], settings: dict[str, int]) -> tuple[int, int, list[str]]:
    """Replay the trail. Returns (allowed workers, current clean streak, explanation lines)."""
    level, streak, why = settings["start_workers"], 0, []
    for r in rows:
        result = r.get("result", "").strip().lower()
        if result in POSITIVE:
            streak += 1
            if streak >= settings["promote_after"] and level < settings["max_workers"]:
                level, streak = level + 1, 0
                n = settings["promote_after"]
                why.append(f"{r['ts']} {r['task']}: {n} clean approvals -> {level} workers")
        elif result in RESET:
            streak = 0
        elif result in NEGATIVE:
            old, level, streak = level, max(settings["start_workers"], level - 1), 0
            why.append(f"{r['ts']} {r['task']}: {result} -> {level} workers (was {old})")
    return level, streak, why


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("log")
    for col in COLUMNS[1:]:
        lg.add_argument(col)
    tr = sub.add_parser("trust")
    tr.add_argument("--explain", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("--last", type=int, default=20)
    a = p.parse_args(argv)

    if a.cmd == "log":
        row = {c: getattr(a, c) for c in COLUMNS[1:]}
        row["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = row["result"].strip().lower()
        known = POSITIVE | RESET | NEGATIVE | NEUTRAL
        if result not in known and not re.match(r"^[A-Z ]+:", row["result"].strip()):
            vocab = ", ".join(sorted(known))
            note = f"note: result {row['result']!r} is not in the vocabulary ({vocab}); treated as neutral"
            print(note, file=sys.stderr)
        append(row)
        return 0
    rows = read()
    if a.cmd == "trust":
        settings = trust_settings()
        level, streak, why = trust_level(rows, settings)
        if a.explain:
            start, cap = settings["start_workers"], settings["max_workers"]
            print(f"allowed workers: {level} (start {start}, max {cap})")
            print(f"clean approvals toward next level: {streak}/{settings['promote_after']}")
            for line in why or ["no level changes yet"]:
                print(f"  {line}")
        else:
            print(level)
        return 0
    if not rows:
        print("no decisions logged yet")
        return 0
    shown = rows[-a.last :]
    widths = {c: min(40, max(len(c), *(len(r.get(c, "")) for r in shown))) for c in COLUMNS}
    print("  ".join(c.ljust(widths[c]) for c in COLUMNS))
    for r in shown:
        print("  ".join(r.get(c, "")[: widths[c]].ljust(widths[c]) for c in COLUMNS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
