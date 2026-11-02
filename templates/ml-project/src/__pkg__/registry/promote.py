"""Champion/challenger promotion with the MLflow model registry.

python -m {{pkg}}.registry.promote --config configs/base.yaml [--version N] [--approve]
python -m {{pkg}}.registry.promote --config configs/base.yaml --rollback

1. Evaluate the candidate version (default: latest) and the current @champion on the same
   validation split, overall and per slice.
2. Candidate must not regress beyond configs/gates.json tolerances (overall and on every slice).
3. Passing candidates get @challenger. Only with --approve (a human decision) does the candidate
   become @champion; the old champion keeps @previous-champion for one-command rollback.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

from ..config import load_config
from ..data.load import load_dataset, split
from ..evaluation.gates import compare_metrics, format_table
from ..evaluation.metrics import classification_metrics
from ..models.train import features_and_target
from ..tracking import CHALLENGER, CHAMPION, PREVIOUS, configure


def score_version(name: str, version: str, X: pd.DataFrame, y: pd.Series) -> dict:
    model = mlflow.sklearn.load_model(f"models:/{name}/{version}")
    return classification_metrics(y.to_numpy(), model.predict_proba(X)[:, 1])


def slice_metrics(name: str, version: str, valid: pd.DataFrame, cfg: dict, column: str) -> dict:
    X, y = features_and_target(valid, cfg)
    model = mlflow.sklearn.load_model(f"models:/{name}/{version}")
    prob = pd.Series(model.predict_proba(X)[:, 1], index=valid.index)
    buckets = pd.qcut(valid[column], q=cfg.get("promotion", {}).get("slice_bins", 3), duplicates="drop")
    out = {}
    for b, idx in valid.groupby(buckets, observed=True).groups.items():
        if y.loc[idx].nunique() == 2:
            out[str(b)] = classification_metrics(y.loc[idx].to_numpy(), prob.loc[idx].to_numpy())
    return out


def alias_version(client: MlflowClient, name: str, alias: str) -> str | None:
    try:
        return str(client.get_model_version_by_alias(name, alias).version)
    except MlflowException:
        return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a config value")
    p.add_argument("--version")
    p.add_argument("--approve", action="store_true", help="human approval to make the candidate @champion")
    p.add_argument("--rollback", action="store_true", help="point @champion back to @previous-champion")
    p.add_argument("--rules", default="configs/gates.json")
    a = p.parse_args()
    cfg = load_config(a.config, a.set)
    name = configure(cfg)
    client = MlflowClient()

    if a.rollback:
        prev = alias_version(client, name, PREVIOUS)
        if prev is None:
            print("no @previous-champion to roll back to")
            return 1
        client.set_registered_model_alias(name, CHAMPION, prev)
        print(f"@champion -> v{prev} (rolled back)")
        return 0

    candidate = a.version or str(max(int(v.version) for v in client.search_model_versions(f"name='{name}'")))
    champion = alias_version(client, name, CHAMPION)
    _, valid = split(load_dataset(cfg), cfg)
    X, y = features_and_target(valid, cfg)
    rules = json.loads(Path(a.rules).read_text())["metrics"]
    cand = score_version(name, candidate, X, y)

    passed = True
    if champion and champion != candidate:
        champ = score_version(name, champion, X, y)
        passed, rows = compare_metrics(cand, champ, rules)
        print(f"overall: candidate v{candidate} vs champion v{champion}")
        print(format_table(rows, ref_label="champion"))
        slice_col = cfg.get("promotion", {}).get("slice_column")
        if slice_col:
            cs = slice_metrics(name, candidate, valid, cfg, slice_col)
            ps = slice_metrics(name, champion, valid, cfg, slice_col)
            for s in sorted(set(cs) & set(ps)):
                ok, srows = compare_metrics(cs[s], ps[s], rules)
                if not ok:
                    passed = False
                    print(f"slice {slice_col}={s}: REGRESSION")
                    print(format_table(srows, ref_label="champion"))
    else:
        print(f"no other champion; candidate v{candidate}: {cand}")

    for k, v in cand.items():
        client.set_model_version_tag(name, candidate, f"valid_{k}", f"{v:.6f}")
    client.set_model_version_tag(name, candidate, "promotion_check", "pass" if passed else "fail")
    if not passed:
        print(f"PROMOTION: FAIL - v{candidate} stays unaliased")
        return 1
    client.set_registered_model_alias(name, CHALLENGER, candidate)
    print(f"PROMOTION: PASS - v{candidate} is @challenger")
    if a.approve:
        if champion and champion != candidate:
            client.set_registered_model_alias(name, PREVIOUS, champion)
        client.set_registered_model_alias(name, CHAMPION, candidate)
        note = f"; @previous-champion -> v{champion}" if champion else ""
        print(f"@champion -> v{candidate} (approved){note}")
    else:
        print("re-run with --approve (human decision) to make it @champion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
