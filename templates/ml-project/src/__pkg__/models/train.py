"""Training entrypoint: python -m {{pkg}}.models.train --config configs/base.yaml"""

import argparse
import pickle
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..config import load_config, set_seed
from ..data.load import TARGET, load_dataset, split
from ..features.build import build_features


def make_model(cfg: dict[str, Any]) -> Pipeline:
    m = cfg["model"]
    if m["type"] != "logistic_regression":
        raise ValueError(f"unknown model type: {m['type']}")
    # Scaler lives inside the pipeline so it is fitted on training data only.
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(C=m["C"], max_iter=m["max_iter"], random_state=cfg["seed"])),
        ]
    )


def fit(train: pd.DataFrame, cfg: dict[str, Any]) -> Pipeline:
    X = build_features(train, cfg).drop(columns=[TARGET])
    model = make_model(cfg)
    model.fit(X, train[TARGET])
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    train, _ = split(load_dataset(cfg), cfg)
    model = fit(train, cfg)
    out = Path(cfg["artifacts_dir"]) / "model.pkl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pickle.dumps(model))
    print(f"saved {out}")


if __name__ == "__main__":
    main()
