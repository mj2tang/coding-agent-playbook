#!/usr/bin/env python3
"""Install the coding-agent-playbook into COPIES of existing projects and prove it does no harm.

  python3 scripts/check_install_safety.py <playbook-dir> <scratch-dir> <project> [<project> ...]

Your projects are only read (copied, excluding node_modules/venvs); all installs happen in the copies.

For each (project, mode): copy the project (originals are never touched), fingerprint every file
and the git state, install, fingerprint again, and check:
  - no file deleted; no pre-existing file modified except .claude/settings.json
  - .claude/settings.json (if it existed) is a strict superset of the original
  - every new path is inside the playbook's footprint
  - git HEAD, branch, stash and the content of pre-existing uncommitted changes are unchanged
  - a second install is a no-op (idempotent)
Modes: vendor (playbook.py init), plugin (playbook.py init --mode plugin),
cli (claude plugin marketplace add + install, --scope project).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

PLAYBOOK = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
PROJECTS = [Path(p).resolve() for p in sys.argv[3:]]
EXCLUDE = {"node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
FOOTPRINT = (".agents/", ".claude/agents/", ".claude/skills", ".claude/hooks/", "tasks/", "scripts/agent-team/",
             "docs/pipeline-map/", "configs/team.json", "configs/gates.json", "AGENTS.playbook.md",
             ".claude/settings.json")
APPEND_ONLY = ("CLAUDE.md", "AGENTS.md")  # may be created/appended only in the opt-in --link mode


def fingerprint(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel == ".git" or set(p.relative_to(root).parts) & EXCLUDE:
            continue
        if p.is_symlink():
            out[rel] = "symlink:" + str(p.readlink())
        elif p.is_file():
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def git_state(root: Path) -> dict[str, str]:
    if not (root / ".git").exists():
        return {}

    def g(*a: str) -> str:
        return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True).stdout.strip()

    return {"head": g("rev-parse", "HEAD"), "branch": g("branch", "--show-current"), "stash": g("stash", "list"),
            "dirty_tracked": g("diff", "--name-only")}


def superset(old: object, new: object, path: str = "") -> list[str]:
    """Problems where `new` drops or changes something from `old` (lists may grow, dicts may gain keys)."""
    if isinstance(old, dict) and isinstance(new, dict):
        probs = []
        for k, v in old.items():
            if k not in new:
                probs.append(f"{path}/{k} removed")
            else:
                probs += superset(v, new[k], f"{path}/{k}")
        return probs
    if isinstance(old, list) and isinstance(new, list):
        return [f"{path}: item {x!r} removed" for x in old if x not in new]
    return [] if old == new else [f"{path}: {old!r} -> {new!r}"]


def install(proj: Path, mode: str) -> str:
    if mode == "vendor":
        cmd = [sys.executable, str(PLAYBOOK / "scripts/playbook.py"), "init", str(proj)]
    elif mode == "full":
        cmd = [sys.executable, str(PLAYBOOK / "scripts/playbook.py"), "init", str(proj), "--profile", "ml",
               "--guardrails", "--link"]
    elif mode == "plugin":
        cmd = [sys.executable, str(PLAYBOOK / "scripts/playbook.py"), "init", str(proj), "--mode", "plugin"]
    else:
        out = []
        for c in (["claude", "plugin", "marketplace", "add", str(PLAYBOOK), "--scope", "project"],
                  ["claude", "plugin", "install", "agent-playbook@mj2tang", "--scope", "project", "-y"]):
            r = subprocess.run(c, cwd=proj, capture_output=True, text=True, timeout=300)
            out.append(f"$ {' '.join(c[:4])} ... -> {r.returncode}\n{r.stdout[-400:]}{r.stderr[-400:]}")
        return "\n".join(out)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout + r.stderr


def check(src: Path, mode: str) -> dict[str, object]:
    proj = OUT / f"{src.name}-{mode}"
    if proj.exists():
        shutil.rmtree(proj)
    shutil.copytree(src, proj, symlinks=True, ignore=shutil.ignore_patterns(*EXCLUDE))
    before, git_before = fingerprint(proj), git_state(proj)
    originals = {f: (proj / f).read_text() for f in APPEND_ONLY if (proj / f).exists()}
    settings_before = json.loads((proj / ".claude/settings.json").read_text()) \
        if (proj / ".claude/settings.json").exists() else None
    log = install(proj, mode)
    after, git_after = fingerprint(proj), git_state(proj)

    added = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    modified = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    problems = [f"deleted: {p}" for p in deleted]
    for p in modified:
        if p == ".claude/settings.json":
            continue
        if mode == "full" and p in APPEND_ONLY and (proj / p).read_text().startswith(originals[p]):
            continue  # opt-in pointer line appended; original text intact
        problems.append(f"modified pre-existing file: {p}")
    problems += [f"new path outside playbook footprint: {p}" for p in added
                 if not p.startswith(FOOTPRINT) and not (mode == "full" and p in APPEND_ONLY)]
    if settings_before is not None and ".claude/settings.json" in modified:
        problems += [f"settings.json {x}" for x in superset(settings_before, json.loads(
            (proj / ".claude/settings.json").read_text()))]
    if mode == "full" and git_after:  # --link appends a pointer line to tracked instruction files
        git_after = dict(git_after, dirty_tracked="\n".join(
            f for f in git_after["dirty_tracked"].splitlines() if f not in APPEND_ONLY))
    if git_before != git_after:
        problems.append(f"git state changed: {git_before} -> {git_after}")

    second = fingerprint(proj)
    settings_after = json.loads((proj / ".claude/settings.json").read_text()) \
        if (proj / ".claude/settings.json").exists() else None
    log2 = install(proj, mode)
    third = fingerprint(proj)
    rerun_changes = sorted(k for k in set(second) | set(third) if second.get(k) != third.get(k))
    if ".claude/settings.json" in rerun_changes:  # re-serialisation is fine if the content is the same
        rerun_changes.remove(".claude/settings.json") if settings_after == json.loads(
            (proj / ".claude/settings.json").read_text()) else None
    if rerun_changes:
        problems.append(f"second install changed: {rerun_changes[:5]}")
    return {"project": src.name, "mode": mode, "copy": str(proj), "added": len(added),
            "added_top": sorted({a.split('/')[0] + ('/' if '/' in a else '') for a in added}),
            "modified": modified, "deleted": deleted, "problems": problems, "install_log": log[-1500:],
            "rerun_log": log2[-300:]}


results = [check(p, m) for p in PROJECTS for m in ("vendor", "plugin", "cli", "full")]
(OUT / "results.json").write_text(json.dumps(results, indent=2))
for r in results:
    status = "PASS" if not r["problems"] else "FAIL"
    print(f"{status} {r['project']:14s} {r['mode']:7s} added={r['added']:3d} modified={r['modified']} "
          f"deleted={len(r['deleted'])} top={r['added_top']}")
    for p in r["problems"]:
        print(f"    - {p}")
