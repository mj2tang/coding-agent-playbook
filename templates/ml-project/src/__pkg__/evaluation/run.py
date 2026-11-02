"""Evaluation entrypoint: trains on the train split, scores the valid split, writes metrics JSON."""

import argparse
import json
import subprocess
from pathlib import Path

from ..config import load_config, set_seed
from ..data.load import TARGET, load_dataset, split
from ..features.build import build_features
from ..models.train import fit
from .metrics import classification_metrics


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", default="metrics/current.json")
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    train, valid = split(load_dataset(cfg), cfg)
    model = fit(train, cfg)
    X_valid = build_features(valid, cfg).drop(columns=[TARGET])
    metrics = classification_metrics(valid[TARGET].to_numpy(), model.predict_proba(X_valid)[:, 1])
    report = {
        "metrics": {k: round(v, 6) for k, v in metrics.items()},
        "split": "valid",
        "n": len(valid),
        "seed": cfg["seed"],
        "config": args.config,
        "git_sha": git_sha(),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["metrics"]))


if __name__ == "__main__":
    main()
