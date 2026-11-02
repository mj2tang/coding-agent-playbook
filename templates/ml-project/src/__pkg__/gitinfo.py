"""Which code produced an artifact: the commit, marked "-dirty" when tracked files had changes.

A "-dirty" SHA on metrics or an MLflow run means the result came from uncommitted code, so it is
not proof for any commit - commit first, then re-run.
"""

import subprocess


def git_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"], text=True
        ).strip()
    except Exception:
        return "unknown"
    return f"{sha}-dirty" if dirty else sha
