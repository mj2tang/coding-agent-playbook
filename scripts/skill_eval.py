#!/usr/bin/env python3
"""Blinded A/B evaluation of a skill change (see skills/skill-eval/SKILL.md).

  skill_eval.py --skill worker-protocol --variant-a skills/worker-protocol --variant-b ~/edited \
      --prompt-file evals/prompts/add-brier.txt --rubric evals/rubrics/worker-protocol.md --runs 3

For each variant x run: scaffold a fresh project under a neutral name, install the variant over
``.agents/skills/<skill>``, commit, run the task with ``--runner`` (prompt on stdin, cwd = the
project), and save the resulting diff. Then shuffle all submissions under neutral labels and ask
``--judge`` (prompt on stdin) to score them against the rubric as JSON. ``report.md`` un-blinds
and averages per variant. Candidates never see the rubric, other submissions, or eval wording.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Phrases that tell an agent it is being tested. Domain words (score, evaluation, experiment,
# benchmark, candidate) are normal in ML tasks, so they are not banned on their own.
BANNED = re.compile(
    r"\b(rubric|judge[ds]?|judging|grader|grading)\b"
    r"|you('re| are) being (evaluated|tested|graded|scored|judged|watched|compared)"
    r"|this is (a|an|part of an?) (eval|evaluation|test|experiment|benchmark|trial)\b"
    r"|(show|demonstrate|prove) (me |us )?(that |how )?you (follow|use|apply|obey)"
    r"|which (skills|principles|rules|instructions) (you|did you)"
    r"|\bvariant [ab]\b|\bcandidate[ -]?\d|\bcompeting (agents|submissions)\b",
    re.I,
)
PROJECT_NAMES = [
    "harbor-churn",
    "lumen-demand",
    "cedar-risk",
    "atlas-pricing",
    "quartz-leads",
    "maple-retention",
    "orbit-forecast",
    "pine-conversion",
    "ember-ltv",
    "slate-fraud",
]
MAX_DIFF_CHARS = 30_000


def check_blind(text: str, what: str) -> None:
    hit = BANNED.search(text)
    if hit:
        raise ValueError(
            f"{what} reveals the evaluation ({hit.group(0)!r}); rewrite it as an organic request"
        )


def run(cmd: str, cwd: Path, stdin: str = "", timeout: int = 3600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        shlex.split(cmd), cwd=cwd, input=stdin, capture_output=True, text=True, timeout=timeout
    )


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


def make_project(workdir: Path, name: str, skill: str, variant: Path) -> Path:
    proj = workdir / name
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/playbook.py"), "new", str(proj), "--name", name],
        check=True,
        capture_output=True,
    )
    dest = proj / ".agents/skills" / skill
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(variant, dest)
    git(proj, "add", "-A")
    git(
        proj,
        "-c",
        "user.name=dev",
        "-c",
        "user.email=dev@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "setup",
    )
    return proj


def submission(proj: Path) -> str:
    git(proj, "add", "-A")  # include new files in the diff
    diff = git(proj, "diff", "--cached", "HEAD")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n... [diff truncated]\n"
    return diff or "(no changes)"


def judge_prompt(rubric: str, labelled: dict[str, str], task: str) -> str:
    parts = [
        "Several independent engineers completed the same task in identical repositories.",
        f"Task they were given:\n{task.strip()}\n",
        f"Grade each submission against these criteria (0-5 each, 5 = fully met):\n{rubric.strip()}\n",
        'Return ONLY a JSON object: {"<label>": {"<criterion>": <0-5>, ..., "notes": "<one line>"}, ...}',
        "using the criterion names exactly as listed above.",
    ]
    for label, diff in labelled.items():
        parts.append(f"\n===== {label} =====\n{diff}")
    return "\n".join(parts)


def parse_scores(raw: str) -> dict[str, dict[str, object]]:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("judge output has no JSON object")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("judge JSON is not an object")
    return data


def summarise(scores: dict[str, dict[str, object]], mapping: dict[str, str]) -> dict[str, dict[str, float]]:
    """Mean numeric score per variant per criterion (plus 'total')."""
    sums: dict[str, dict[str, list[float]]] = {}
    for label, crit in scores.items():
        variant = mapping.get(label)
        if variant is None:
            continue
        for k, v in crit.items():
            if isinstance(v, (int, float)):
                sums.setdefault(variant, {}).setdefault(k, []).append(float(v))
        total = sum(float(v) for v in crit.values() if isinstance(v, (int, float)))
        sums.setdefault(variant, {}).setdefault("total", []).append(total)
    return {v: {k: sum(xs) / len(xs) for k, xs in c.items()} for v, c in sums.items()}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--skill", required=True)
    p.add_argument("--variant-a", required=True, type=Path)
    p.add_argument("--variant-b", required=True, type=Path)
    p.add_argument("--prompt-file", required=True, type=Path)
    p.add_argument("--rubric", required=True, type=Path)
    p.add_argument("--runs", type=int, default=2)
    p.add_argument("--runner", default="claude -p --permission-mode acceptEdits")
    p.add_argument("--judge", default="claude -p --model opus")
    p.add_argument("--out", type=Path, default=Path(".audit/skill-evals"))
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args(argv)

    for d in (a.variant_a, a.variant_b):
        if not (d / "SKILL.md").exists():
            p.error(f"{d} has no SKILL.md")
    task = a.prompt_file.read_text()
    check_blind(task, "the task prompt")
    rubric = a.rubric.read_text()
    rng = random.Random(a.seed)
    out = a.out / f"{a.skill}"
    out.mkdir(parents=True, exist_ok=True)

    names = rng.sample(PROJECT_NAMES, k=min(len(PROJECT_NAMES), 2 * a.runs))
    jobs = [(v, path) for v, path in (("A", a.variant_a), ("B", a.variant_b)) for _ in range(a.runs)]
    rng.shuffle(jobs)
    submissions: dict[str, tuple[str, str]] = {}  # project -> (variant, diff)
    with tempfile.TemporaryDirectory() as tmp:
        for (variant, path), name in zip(jobs, names, strict=False):
            proj = make_project(Path(tmp), name, a.skill, path.resolve())
            res = run(a.runner, proj, stdin=task)
            (out / f"{name}.transcript.txt").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
            submissions[name] = (variant, submission(proj))
            print(f"ran {name} (exit {res.returncode})")

    order = list(submissions)
    rng.shuffle(order)
    mapping = {f"Submission {i + 1}": submissions[n][0] for i, n in enumerate(order)}
    labelled = {f"Submission {i + 1}": submissions[n][1] for i, n in enumerate(order)}
    (out / "mapping.json").write_text(
        json.dumps(
            {label: {"variant": mapping[label], "project": order[i]} for i, label in enumerate(mapping)},
            indent=2,
        )
    )

    res = run(a.judge, ROOT, stdin=judge_prompt(rubric, labelled, task))
    (out / "judge.txt").write_text(res.stdout)
    scores = parse_scores(res.stdout)
    summary = summarise(scores, mapping)
    lines = [
        f"# Skill eval: {a.skill}",
        "",
        f"Runs per variant: {a.runs}",
        "",
        "| variant | " + " | ".join(sorted({k for s in summary.values() for k in s})) + " |",
    ]
    crits = sorted({k for s in summary.values() for k in s})
    lines.append("|---|" + "---|" * len(crits))
    for v in sorted(summary):
        lines.append(f"| {v} | " + " | ".join(f"{summary[v].get(c, float('nan')):.2f}" for c in crits) + " |")
    lines += ["", "Per-submission notes (un-blinded):"]
    for label, crit in scores.items():
        lines.append(f"- {label} ({mapping.get(label, '?')}): {crit.get('notes', '')}")
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[: 6 + len(summary)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
