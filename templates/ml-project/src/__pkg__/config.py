import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base (override wins); returns a new dict."""
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def apply_overrides(cfg: dict[str, Any], overrides: list[str]) -> dict[str, Any]:
    """Apply dotted KEY=VALUE overrides (values parsed as YAML), e.g. mlflow.registered_model=a.b.c."""
    out = deep_merge(cfg, {})
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"override must be KEY=VALUE, got {item!r}")
        key, raw = item.split("=", 1)
        node = out
        *parents, leaf = key.split(".")
        for part in parents:
            node = node.setdefault(part, {})
        node[leaf] = yaml.safe_load(raw)
    return out


def load_config(path: str | Path, overrides: list[str] | None = None) -> dict[str, Any]:
    """Load a YAML config. `extends: other.yaml` (relative to this file) inherits and overrides;
    `overrides` (from `--set KEY=VALUE`) are applied last."""
    path = Path(path)
    with open(path) as f:
        cfg: dict[str, Any] = yaml.safe_load(f) or {}
    parent = cfg.pop("extends", None)
    if parent:
        cfg = deep_merge(load_config(path.parent / parent), cfg)
    return apply_overrides(cfg, overrides or [])


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)  # noqa: NPY002 - seeds libraries that use the global RNG
