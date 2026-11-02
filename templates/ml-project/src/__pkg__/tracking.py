"""Thin MLflow helpers so every entrypoint tracks runs the same way.

Conventions: one experiment per project, run tags for git SHA and config, a single registered
model whose versions are promoted with aliases (@champion, @challenger, @previous-champion).
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import mlflow

CHAMPION, CHALLENGER, PREVIOUS = "champion", "challenger", "previous-champion"


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def configure(cfg: dict[str, Any]) -> str:
    m = cfg["mlflow"]
    mlflow.set_tracking_uri(m["tracking_uri"])
    mlflow.set_registry_uri(m.get("registry_uri", m["tracking_uri"]))
    mlflow.set_experiment(m["experiment"])
    return str(m["registered_model"])


def flatten(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, f"{key}."))
        else:
            out[key] = v if not isinstance(v, list) else ",".join(map(str, v))
    return out


@contextmanager
def start_run(cfg: dict[str, Any], run_name: str, config_path: str, **tags: str) -> Iterator[Any]:
    configure(cfg)
    with mlflow.start_run(
        run_name=run_name, tags={"git_sha": git_sha(), "config": config_path, **tags}
    ) as run:
        params = {k: v for k, v in flatten(cfg).items() if not k.startswith("mlflow.")}
        mlflow.log_params(params)
        yield run
