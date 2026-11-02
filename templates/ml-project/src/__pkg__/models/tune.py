"""Hyperparameter search on the TRAIN split only (cross-validated), logged to MLflow.

python -m {{pkg}}.models.tune --config configs/base.yaml --out configs/experiments/tuned.yaml
Writes a full config with the best parameters; adopt it through a normal task + gates.
"""

import argparse
import copy
from pathlib import Path

import mlflow
import pandas as pd
import yaml
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold

from ..config import load_config, set_seed
from ..data.load import load_dataset, split
from ..tracking import start_run
from .train import features_and_target, make_model


def tune(cfg: dict, config_path: str) -> tuple[dict, pd.DataFrame]:
    set_seed(cfg["seed"])
    t = cfg["tuning"]
    train, _ = split(load_dataset(cfg), cfg)  # validation stays untouched for the final comparison
    X, y = features_and_target(train, cfg)
    search = RandomizedSearchCV(
        make_model(cfg),
        param_distributions=t["param_distributions"],
        n_iter=t["n_iter"],
        scoring=t.get("scoring", "roc_auc"),
        cv=StratifiedKFold(t["cv"], shuffle=True, random_state=cfg["seed"]),
        random_state=cfg["seed"],
        n_jobs=-1,
    )
    with start_run(cfg, run_name="tune", config_path=config_path, stage="tune"):
        search.fit(X, y)
        results = pd.DataFrame(search.cv_results_)[
            ["params", "mean_test_score", "std_test_score", "rank_test_score"]
        ]
        mlflow.log_metric("cv_best_score", float(search.best_score_))
        mlflow.log_params({f"best.{k}": v for k, v in search.best_params_.items()})
        mlflow.log_text(results.sort_values("rank_test_score").to_csv(index=False), "cv_results.csv")
    return search.best_params_, results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--out", default="configs/experiments/tuned.yaml")
    a = p.parse_args()
    cfg = load_config(a.config)
    best, results = tune(cfg, a.config)
    tuned = copy.deepcopy(cfg)
    for key, value in best.items():  # e.g. "clf__C" -> model.C
        tuned["model"][key.split("__", 1)[1]] = value
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(yaml.safe_dump(tuned, sort_keys=False))
    print(f"best {best} (cv {results['mean_test_score'].max():.4f}); wrote {a.out}")


if __name__ == "__main__":
    main()
