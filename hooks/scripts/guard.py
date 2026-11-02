#!/usr/bin/env python3
"""Guardrail hooks for coding agents (Claude Code hook protocol).

Reads the hook event JSON on stdin. Exit 2 + stderr blocks the tool call;
exit 0 allows it. Modes:
  bash     PreToolUse(Bash): block destructive or irreversible shell commands
  files    PreToolUse(Edit|Write): block edits to protected paths
  format   PostToolUse(Edit|Write): best-effort auto-format of the edited file
"""
import json
import os
import re
import shutil
import subprocess
import sys

DANGEROUS_BASH = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME)(\s|$)", "recursive delete of / or home"),
    (r"\bgit\s+push\b[^\n]*(--force|-f)\b", "force push"),
    (r"\bgit\s+push\b", "git push (needs human approval)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards work"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean deletes untracked files"),
    (r"\b(dvc\s+push|aws\s+s3\s+(rm|sync)|gsutil\s+(-m\s+)?rm)\b", "remote data mutation"),
    (r"\bdrop\s+(table|database)\b", "destructive SQL"),
    (r"\bdata/raw\b[^\n]*(>|\brm\b|\bmv\b)|(\brm\b|\bmv\b)[^\n]*\bdata/raw\b", "data/raw is immutable"),
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
