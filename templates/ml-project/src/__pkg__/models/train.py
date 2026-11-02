"""Training entrypoint: python -m {{pkg}}.models.train --config configs/base.yaml

Fits on the train split, scores the valid split, logs params/metrics/model to MLflow, and
registers a new model version (tagged with git SHA and valid metrics). Promotion is separate.
"""

import argparse
from typing import Any

import mlflow
import pandas as pd
from mlflow.models import infer_signature
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..config import load_config, set_seed
from ..data.load import TARGET, load_dataset, split
from ..evaluation.metrics import classification_metrics
from ..features.build import build_features
from ..tracking import start_run


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


def features_and_target(df: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.Series]:
    X = build_features(df, cfg).drop(columns=[TARGET])
    keep = cfg.get("features", {}).get("keep")
    return (X[keep] if keep else X), df[TARGET]


def fit(train: pd.DataFrame, cfg: dict[str, Any]) -> Pipeline:
    X, y = features_and_target(train, cfg)
    model = make_model(cfg)
    model.fit(X, y)
    return model


def train_and_register(cfg: dict[str, Any], config_path: str) -> str:
    """Train, log, and register. Returns the new registered model version."""
    set_seed(cfg["seed"])
    train, valid = split(load_dataset(cfg), cfg)
    with start_run(cfg, run_name="train", config_path=config_path, stage="train"):
        model = fit(train, cfg)
        X_valid, y_valid = features_and_target(valid, cfg)
        metrics = classification_metrics(y_valid.to_numpy(), model.predict_proba(X_valid)[:, 1])
        mlflow.log_metrics({f"valid_{k}": v for k, v in metrics.items()})
        info = mlflow.sklearn.log_model(
            model,
            name="model",
            signature=infer_signature(X_valid, model.predict_proba(X_valid)[:, 1]),
            input_example=X_valid.head(3),
            registered_model_name=cfg["mlflow"]["registered_model"],
        )
    version = str(info.registered_model_version)
    print(f"registered {cfg['mlflow']['registered_model']} v{version}: {metrics}")
    return version


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    train_and_register(load_config(args.config), args.config)


if __name__ == "__main__":
    main()
