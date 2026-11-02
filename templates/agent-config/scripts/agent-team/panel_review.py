#!/usr/bin/env python3
"""Adversarial review panel: the same intent, diff, and rubric go to reviewers on different models.

  panel_review.py <branch> <task-file> [--base main] [--out .audit/reviews]

Reviewers come from ``configs/team.json -> review_panel`` (name + command). Each command receives
the prompt on stdin and runs read-only in the repo (Claude Code in plan mode, Codex with a
read-only sandbox). Missing CLIs are skipped, not fatal. Each review is written to
``<out>/<task>/<name>.md``; then synthesise: findings raised by 2+ models are high-confidence,
single-model findings are worth reading but lower confidence. Nothing is auto-applied.
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PANEL = [
    {"name": "claude", "cmd": "claude -p --permission-mode plan --model opus"},
    {"name": "codex", "cmd": "codex exec --sandbox read-only -"},
]

RUBRIC = """Review rubric (report only problems you can tie to a file:line or command output):
1. Correctness: does the change achieve the stated intent? Edge cases, error paths, off-by-one.
2. ML integrity: data leakage (fit on validation/test, target or future information in features),
   reproducibility (seeds, configs), evaluation on the right split, silent NaN handling.
3. Tests: does new behaviour have tests that would fail without the change? Any test weakened?
4. Scope: changes outside the task's owned files; unnecessary abstractions or dead code.
5. Gates: configs/gates.json, metrics/baseline.json, data/raw untouched unless the task says so.
For each finding give: severity (high/medium/low), file:line, the problem, a concrete failure
scenario, and a suggested fix. End with VERDICT: APPROVE or CHANGES_REQUESTED."""


def build_prompt(task_text: str, branch: str, base: str) -> str:
    return (
        "You are reviewing a change in this repository. Do not modify any files.\n\n"
        f"Intent (from the task file):\n{task_text.strip()}\n\n"
        f"Inspect the change yourself with `git diff {base}...{branch}` and read surrounding code "
        "as needed.\n\n" + RUBRIC
    )


def load_panel(team_json: Path = Path("configs/team.json")) -> list[dict[str, str]]:
    if team_json.exists():
        panel = json.loads(team_json.read_text()).get("review_panel")
        if panel:
            return list(panel)
    return DEFAULT_PANEL


def run_panel(prompt: str, panel: list[dict[str, str]], out_dir: Path, timeout: int = 1800) -> dict[str, str]:
    """Run each available reviewer; returns {name: status}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    status: dict[str, str] = {}
    for reviewer in panel:
        argv = shlex.split(reviewer["cmd"])
        if shutil.which(argv[0]) is None:
            status[reviewer["name"]] = f"skipped: {argv[0]} not installed"
            continue
        try:
            res = subprocess.run(argv, input=prompt, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            status[reviewer["name"]] = "timed out"
            continue
        (out_dir / f"{reviewer['name']}.md").write_text(res.stdout)
        status[reviewer["name"]] = "ok" if res.returncode == 0 else f"exit {res.returncode}"
    return status


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("branch")
    p.add_argument("task_file")
    p.add_argument("--base", default="main")
    p.add_argument("--out", default=".audit/reviews")
    a = p.parse_args(argv)
    task = Path(a.task_file)
    prompt = build_prompt(task.read_text(), a.branch, a.base)
    status = run_panel(prompt, load_panel(), Path(a.out) / task.stem)
    for name, s in status.items():
        print(f"{name:12s} {s}")
    ok = [n for n, s in status.items() if s == "ok"]
    if len(ok) < 2:
        print("warning: fewer than two reviewers completed; agreement signal is weak")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
