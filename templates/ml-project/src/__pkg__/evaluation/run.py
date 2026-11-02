"""Evaluation entrypoint: trains on the train split, scores the valid split, writes metrics JSON."""

import argparse
import json
from pathlib import Path

from ..config import load_config, set_seed
from ..data.load import load_dataset, split
from ..gitinfo import git_sha
from ..models.train import features_and_target, fit
from .metrics import classification_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--set", action="append", default=[], metavar="KEY=VALUE", help="override a config value"
    )
    parser.add_argument("--out", default="metrics/current.json")
    args = parser.parse_args()
    cfg = load_config(args.config, args.set)
    set_seed(cfg["seed"])
    train, valid = split(load_dataset(cfg), cfg)
    model = fit(train, cfg)
    X_valid, y_valid = features_and_target(valid, cfg)
    metrics = classification_metrics(y_valid.to_numpy(), model.predict_proba(X_valid)[:, 1])
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
