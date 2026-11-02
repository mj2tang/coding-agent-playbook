"""Thin MLflow helpers so every entrypoint tracks runs the same way.

Conventions: one experiment per project, run tags for git SHA and config, a single registered
model whose versions are promoted with aliases (@champion, @challenger, @previous-champion).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import mlflow

from .gitinfo import git_sha

CHAMPION, CHALLENGER, PREVIOUS = "champion", "challenger", "previous-champion"


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


def describe(cfg: dict[str, Any], limit: int = 10) -> str:
    """Read-only summary of the registered model: versions, aliases, source commit, valid metrics."""
    name = configure(cfg)
    client = mlflow.MlflowClient()
    try:
        versions = client.search_model_versions(f"name='{name}'")
    except Exception as e:  # registry not created yet
        return f"no registered model {name!r} yet ({e.__class__.__name__})"
    rows = [f"registered model: {name}", "version  aliases                      git_sha        valid metrics"]
    for v in sorted(versions, key=lambda v: int(v.version), reverse=True)[:limit]:
        if v.run_id is None:  # registered from a URI without a tracked run
            rows.append(f"{v.version:<8} {'-':<28} {'?':<14} (no run)")
            continue
        run = client.get_run(v.run_id)
        metrics = ", ".join(
            f"{k.removeprefix('valid_')}={x:.4f}"
            for k, x in sorted(run.data.metrics.items())
            if k.startswith("valid_")
        )
        aliases = ",".join(f"@{a}" for a in v.aliases) or "-"
        rows.append(f"{v.version:<8} {aliases:<28} {run.data.tags.get('git_sha', '?'):<14} {metrics}")
    return "\n".join(rows)


if __name__ == "__main__":
    import argparse

    from .config import load_config

    parser = argparse.ArgumentParser(description="Show registered model versions (read-only).")
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    print(describe(load_config(args.config, args.set)))
