#!/usr/bin/env python3
"""Guardrail hooks for coding agents (Claude Code hook protocol).

Reads the hook event JSON on stdin. Exit 2 + stderr blocks the tool call;
exit 0 allows it. Modes:
  bash     PreToolUse(Bash): block destructive or irreversible shell commands; force a human
           prompt ("ask") for approval-only actions such as rebaseline, rollback, promotion
  files    PreToolUse(Edit|Write): block edits to protected paths
  format   PostToolUse(Edit|Write): best-effort auto-format of the edited file
"""
import json
import os
import re
import shutil
import subprocess
import sys

# `git` followed by any global options (-C <path>, -c key=val, --git-dir=...) before the subcommand,
# so `git -C ../wt push` is caught the same as `git push`.
GIT = r"\bgit\b(?:\s+(?:-C\s+\S+|-c\s+\S+|--[\w-]+(?:=\S+)?))*\s+"
MAKE = r"\bmake\b[^\n;&|]*?\s"  # make with any flags/-C path before the target

DANGEROUS_BASH = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME)(\s|$)", "recursive delete of / or home"),
    (GIT + r"push\b[^\n]*(--force|-f)\b", "force push"),
    (GIT + r"push\b", "git push (needs human approval)"),
    (GIT + r"reset\s+--hard\b", "git reset --hard discards work"),
    (GIT + r"clean\s+-[a-zA-Z]*f", "git clean deletes untracked files"),
    (r"\b(dvc\s+push|aws\s+s3\s+(rm|sync)|gsutil\s+(-m\s+)?rm)\b", "remote data mutation"),
    (r"\bdrop\s+(table|database)\b", "destructive SQL"),
    (r"\bdata/raw\b[^\n]*(>|\brm\b|\bmv\b)|(\brm\b|\bmv\b)[^\n]*\bdata/raw\b", "data/raw is immutable"),
]

# Allowed only with a human in the loop: the hook asks even when an allow rule (e.g. `make -C:*`)
# would match. In headless runs an "ask" is a denial, which is what we want.
HUMAN_APPROVAL_BASH = [
    (MAKE + r"rebaseline\b", "rebaselining metrics"),
    (MAKE + r"(bundle-)?rollback\b", "rolling back the champion model"),
    (MAKE + r"(bundle-)?promote(-approve)?\b[^\n]*APPROVE=|" + MAKE + r"bundle-promote-approve\b",
     "moving @champion"),
    (r"--approve\b", "moving @champion"),
    (r"\buv\s+add\b", "adding a dependency"),
    (MAKE + r"bundle-deploy\b[^\n]*TARGET=prod", "deploying to production"),
]

PROTECTED_PATHS = [
    (r"(^|/)\.env(\.|$)", "secrets file"),
    (r"\.(pem|key|p12)$", "key material"),
    (r"(^|/)data/raw/", "data/raw is immutable"),
    (r"(^|/)\.git/", "git internals"),
    (r"(^|/)metrics/baseline\.json$", "baseline metrics change only via `make rebaseline` with human approval"),
    (r"(^|/)configs/gates\.json$", "quality-gate thresholds change only with human approval"),
]


def block(reason):
    print(f"Blocked by agent-playbook guard: {reason}. Ask the user if this is intended.", file=sys.stderr)
    sys.exit(2)


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": f"agent-playbook guard: {reason} needs human approval",
    }}))
    sys.exit(0)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool_input = event.get("tool_input") or {}

    if os.environ.get("PLAYBOOK_GUARD_OFF") == "1":
        sys.exit(0)

    if mode == "bash":
        cmd = tool_input.get("command", "")
        for pattern, reason in DANGEROUS_BASH:
            if re.search(pattern, cmd, re.IGNORECASE):
                block(reason)
        for pattern, reason in HUMAN_APPROVAL_BASH:
            if re.search(pattern, cmd):
                ask(reason)
    elif mode == "files":
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        for pattern, reason in PROTECTED_PATHS:
            if re.search(pattern, path):
                block(f"{path}: {reason}")
    elif mode == "format":
        path = tool_input.get("file_path", "")
        if not path or not os.path.isfile(path):
            sys.exit(0)
        cmd = None
        if path.endswith(".py") and shutil.which("ruff"):
            cmd = ["ruff", "format", "--quiet", path]
        elif re.search(r"\.(ts|tsx|js|jsx|json|css|md)$", path) and shutil.which("prettier"):
            cmd = ["prettier", "--write", "--log-level", "warn", path]
        if cmd:
            subprocess.run(cmd, check=False, timeout=30)
    sys.exit(0)


if __name__ == "__main__":
    main()
