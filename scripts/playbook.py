#!/usr/bin/env python3
"""Scaffold ML projects for a team of coding agents (Claude Code + Codex).

  playbook.py new  <dir> --name my-project [--description "..."] [--mode vendor|plugin] [--bootstrap]
  playbook.py init <dir> [--mode vendor|plugin]      # add the agent setup to an existing repo
  playbook.py sync <dir> [--force]                    # update vendored skills/agents/hooks

Standard library only. Never overwrites a file the project changed unless --force is given.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
MARKETPLACE = "mj2tang"
PLUGIN = "agent-playbook"
PLUGIN_REPO = "mj2tang/coding-agent-playbook"
LOCK = ".agents/playbook.lock.json"

PERMISSIONS = {
    "allow": [
        "Bash(make setup)", "Bash(make check)", "Bash(make lint)", "Bash(make types)",
        "Bash(make test)", "Bash(make data-check)", "Bash(make eval)", "Bash(make gate)",
        "Bash(make train:*)", "Bash(make eda)", "Bash(make select)", "Bash(make tune)",
        "Bash(make promote)", "Bash(make monitor:*)", "Bash(uv sync)", "Bash(uv run pytest:*)", "Bash(uv run ruff:*)",
        "Bash(uv run mypy:*)", "Bash(uv run python -m:*)",
        "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
        "Bash(git add:*)", "Bash(git commit:*)", "Bash(git switch:*)", "Bash(git checkout:*)",
        "Bash(git branch:*)", "Bash(git worktree:*)", "Bash(git merge:*)", "Bash(git revert:*)",
        "Bash(scripts/agent-team/run-wave.sh:*)",
    ],
    "ask": ["Bash(make rebaseline)", "Bash(make promote APPROVE=1:*)", "Bash(make rollback)",
            "Bash(git push:*)", "Bash(uv add:*)"],
    "deny": ["Read(./.env)", "Read(./.env.*)", "Edit(./data/raw/**)"],
}


def hooks_config(guard: str) -> dict:
    def cmd(mode: str) -> list:
        return [{"type": "command", "command": f"python3 {guard} {mode}"}]

    return {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": cmd("bash")},
            {"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": cmd("files")},
        ],
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit", "hooks": cmd("format")}],
    }


class Scaffolder:
    def __init__(self, target: Path, subs: dict[str, str], force: bool, dry_run: bool):
        self.target = target
        self.subs = subs
        self.force = force
        self.dry_run = dry_run
        self.lock: dict[str, str] = {}
        self.report: dict[str, list[str]] = {"created": [], "updated": [], "skipped": []}
        lock_path = target / LOCK
        self.old_lock = json.loads(lock_path.read_text())["files"] if lock_path.exists() else {}

    def render(self, text: str) -> str:
        return re.sub(r"\{\{(\w+)\}\}", lambda m: self.subs.get(m.group(1), m.group(0)), text)

    def write(self, rel: str, content: str, managed: bool = False, mode: int | None = None) -> None:
        """Write a file. Managed files are tracked in the lock so `sync` can update them safely."""
        dest = self.target / rel
        digest = hashlib.sha256(content.encode()).hexdigest()
        if dest.exists():
            current = hashlib.sha256(dest.read_bytes()).hexdigest()
            if current == digest:
                if managed:
                    self.lock[rel] = digest
                return
            untouched = managed and self.old_lock.get(rel) == current
            if not (self.force or untouched):
                self.report["skipped"].append(rel)
                if managed and rel in self.old_lock:
                    self.lock[rel] = self.old_lock[rel]
                return
            self.report["updated"].append(rel)
        else:
            self.report["created"].append(rel)
        if managed:
            self.lock[rel] = digest
        if self.dry_run:
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        if mode:
            dest.chmod(mode)

    def copy_tree(self, src: Path, dest_rel: str, managed: bool = False) -> None:
        for path in sorted(src.rglob("*")):
            if path.is_dir() or path.name == ".DS_Store" or "__pycache__" in path.parts:
                continue
            rel = path.relative_to(src).as_posix().replace("__pkg__", self.subs.get("pkg", "__pkg__"))
            mode = 0o755 if os.access(path, os.X_OK) else None
            text = path.read_text()
            self.write(f"{dest_rel}/{rel}".lstrip("/"), self.render(text), managed=managed, mode=mode)

    def merge_settings(self, extra: dict) -> None:
        """Merge playbook settings into .claude/settings.json, keeping the project's own entries."""
        path = self.target / ".claude" / "settings.json"
        settings = json.loads(path.read_text()) if path.exists() else {}
        perms = settings.setdefault("permissions", {})
        for key, rules in PERMISSIONS.items():
            existing = perms.setdefault(key, [])
            existing.extend(r for r in rules if r not in existing)
        for key, value in extra.items():
            if key == "hooks":
                hooks = settings.setdefault("hooks", {})
                for event, entries in value.items():
                    current = hooks.setdefault(event, [])
                    current.extend(e for e in entries if e not in current)
            elif isinstance(value, dict):
                settings.setdefault(key, {}).update(value)
            else:
                settings.setdefault(key, value)
        content = json.dumps(settings, indent=2) + "\n"
        rel = ".claude/settings.json"
        if path.exists() and path.read_text() == content:
            return
        self.report["updated" if path.exists() else "created"].append(rel)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def symlink(self, rel: str, to: str) -> None:
        link = self.target / rel
        if link.is_symlink() or link.exists():
            return
        self.report["created"].append(f"{rel} -> {to}")
        if not self.dry_run:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(to)

    def save_lock(self) -> None:
        if self.dry_run:
            return
        lock = {"playbook_version": VERSION, "source": PLUGIN_REPO, "files": dict(sorted(self.lock.items()))}
        path = self.target / LOCK
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lock, indent=2) + "\n")


def install_agent_setup(s: Scaffolder, mode: str) -> None:
    """Skills for Codex + Claude, subagents, guard hooks, settings, task board, team scripts."""
    # Skills: Codex reads .agents/skills; Claude Code reads .claude/skills (symlinked in vendor mode).
    s.copy_tree(ROOT / "skills", ".agents/skills", managed=True)
    if mode == "vendor":
        s.symlink(".claude/skills", "../.agents/skills")
        s.copy_tree(ROOT / "agents", ".claude/agents", managed=True)
        s.write(".claude/hooks/guard.py", (ROOT / "hooks/scripts/guard.py").read_text(), managed=True, mode=0o755)
        s.merge_settings({"hooks": hooks_config('"$CLAUDE_PROJECT_DIR"/.claude/hooks/guard.py')})
    else:
        s.merge_settings({
            "extraKnownMarketplaces": {MARKETPLACE: {"source": {"source": "github", "repo": PLUGIN_REPO}}},
            "enabledPlugins": {f"{PLUGIN}@{MARKETPLACE}": True},
        })
    s.copy_tree(ROOT / "templates/agent-config/tasks", "tasks")
    s.copy_tree(ROOT / "templates/agent-config/scripts", "scripts", managed=True)
    s.write("CLAUDE.md", s.render((ROOT / "templates/agent-config/CLAUDE.md").read_text()))
    agents_md = s.render((ROOT / "templates/agent-config/AGENTS.md").read_text())
    if (s.target / "AGENTS.md").exists() and not s.force:
        s.write("AGENTS.playbook.md", agents_md)  # merge by hand into the existing AGENTS.md
    else:
        s.write("AGENTS.md", agents_md)
    for rel in ("configs/team.json", "configs/gates.json"):
        s.write(rel, (ROOT / "templates/ml-project" / rel).read_text())


def git(target: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(target), *args], check=True, capture_output=True)


def cmd_new(a: argparse.Namespace) -> int:
    target = Path(a.dir).resolve()
    if target.exists() and any(target.iterdir()) and not a.force:
        print(f"{target} is not empty; use `init` for existing projects (or --force).")
        return 1
    pkg = a.pkg or re.sub(r"\W", "_", a.name.lower()).strip("_")
    subs = {"project": a.name, "pkg": pkg, "description": a.description}
    s = Scaffolder(target, subs, a.force, a.dry_run)
    s.copy_tree(ROOT / "templates/ml-project", "")
    install_agent_setup(s, a.mode)
    s.save_lock()
    print_report(s, target)
    if a.dry_run:
        return 0
    if not (target / ".git").exists():
        git(target, "init", "-q", "-b", "main")
        git(target, "add", "-A")
        try:
            git(target, "commit", "-q", "-m", f"Scaffold {a.name} with coding-agent-playbook {VERSION}")
            print("git: initialised repo on main with an initial commit")
        except subprocess.CalledProcessError:
            # Usually no git identity configured; worktrees need a commit, so tell the user.
            print("git: initialised repo, but the initial commit failed (is user.name/user.email set?). "
                  "Commit manually before running the agent team.")
            return 0 if not a.bootstrap else 1
    if a.bootstrap:
        print("bootstrap: uv sync, make check, make rebaseline ...")
        for step in (["uv", "sync"], ["make", "check"], ["make", "rebaseline"]):
            subprocess.run(step, cwd=target, check=True)
        git(target, "add", "metrics/baseline.json")
        git(target, "commit", "-q", "-m", "Initial metrics baseline")
    else:
        print("next: cd into the project, run `make setup && make check`, then `make rebaseline` and commit it")
    return 0


def cmd_init(a: argparse.Namespace) -> int:
    target = Path(a.dir).resolve()
    if not target.is_dir():
        print(f"{target} does not exist")
        return 1
    name = a.name or target.name
    pkg = a.pkg or re.sub(r"\W", "_", name.lower()).strip("_")
    s = Scaffolder(target, {"project": name, "pkg": pkg, "description": a.description}, a.force, a.dry_run)
    install_agent_setup(s, a.mode)
    s.save_lock()
    print_report(s, target)
    if (target / "AGENTS.playbook.md").exists():
        print("note: AGENTS.md already existed; merge the sections you want from AGENTS.playbook.md")
    if not (target / "Makefile").exists():
        print("note: no Makefile found; the skills and agents expect `make check`, `make data-check`, `make gate`")
    return 0


def cmd_sync(a: argparse.Namespace) -> int:
    target = Path(a.dir).resolve()
    lock_path = target / LOCK
    if not lock_path.exists():
        print("no playbook lock found; run `init` first")
        return 1
    mode = "vendor" if (target / ".claude/agents/orchestrator.md").exists() else "plugin"
    s = Scaffolder(target, {}, a.force, a.dry_run)
    s.copy_tree(ROOT / "skills", ".agents/skills", managed=True)
    if mode == "vendor":
        s.copy_tree(ROOT / "agents", ".claude/agents", managed=True)
        s.write(".claude/hooks/guard.py", (ROOT / "hooks/scripts/guard.py").read_text(), managed=True, mode=0o755)
    s.copy_tree(ROOT / "templates/agent-config/scripts", "scripts", managed=True)
    s.save_lock()
    print_report(s, target)
    if s.report["skipped"]:
        print("skipped files were edited locally; re-run with --force to overwrite them")
    return 0


def print_report(s: Scaffolder, target: Path) -> None:
    prefix = "[dry-run] " if s.dry_run else ""
    print(f"{prefix}{target}: {len(s.report['created'])} created, "
          f"{len(s.report['updated'])} updated, {len(s.report['skipped'])} skipped")
    for rel in s.report["skipped"]:
        print(f"  skipped (exists/modified): {rel}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("new", "init", "sync"):
        sp = sub.add_parser(name)
        sp.add_argument("dir")
        sp.add_argument("--force", action="store_true")
        sp.add_argument("--dry-run", action="store_true")
        if name != "sync":
            sp.add_argument("--name", required=name == "new")
            sp.add_argument("--pkg")
            sp.add_argument("--description", default="A machine learning project built by a team of agents.")
            sp.add_argument("--mode", choices=["vendor", "plugin"], default="vendor",
                            help="vendor: copy skills/agents/hooks into the repo (default). "
                                 "plugin: enable the agent-playbook Claude Code plugin instead.")
        if name == "new":
            sp.add_argument("--bootstrap", action="store_true",
                            help="also run uv sync, make check, and record the first metrics baseline")
    a = p.parse_args()
    return {"new": cmd_new, "init": cmd_init, "sync": cmd_sync}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
