"""Monitoring entrypoint: python -m {{pkg}}.monitoring.run --config configs/base.yaml --current batch.csv

Compares a current batch against the training reference, writes reports/monitoring.json,
and exits 3 when the retraining policy says retrain (so schedulers/CI can branch on it).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..config import load_config
from ..data.load import TARGET, load_dataset, split
from .drift import DriftConfig, detect_drift
from .retrain import RetrainPolicy, decide_retrain


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a config value")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--current", help="CSV or Parquet of the current scoring batch")
    src.add_argument("--current-table", help="Unity Catalog table catalog.schema.table (Databricks)")
    p.add_argument("--model-trained-at", help="ISO timestamp of the serving model (default: now)")
    p.add_argument("--out", default="reports/monitoring.json")
    a = p.parse_args()
    cfg = load_config(a.config, a.set)
    mcfg = cfg.get("monitoring", {})
    reference, _ = split(load_dataset(cfg), cfg)
    if a.current_table:
        from ..spark import read_table

        current = read_table(a.current_table)
    else:
        path = Path(a.current)
        current = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    features = [c for c in reference.columns if c != TARGET]
    report = detect_drift(
        reference,
        current,
        features,
        DriftConfig(
            p_value=mcfg.get("p_value", 0.05),
            distance=mcfg.get("distance", 0.1),
            drift_share=mcfg.get("drift_share", 0.5),
        ),
    )
    trained_at = (
        datetime.fromisoformat(a.model_trained_at) if a.model_trained_at else datetime.now(timezone.utc)
    )
    decision = decide_retrain(
        RetrainPolicy(
            max_model_age_days=mcfg.get("max_model_age_days", 30),
            max_metric_drop=mcfg.get("max_metric_drop", 0.02),
        ),
        dataset_drift=report.dataset_drift,
        model_trained_at=trained_at,
    )
    out = {"drift": report.to_dict(), "retrain": decision.to_dict(), "rows": len(current)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n")
    print(
        json.dumps(
            {
                "dataset_drift": report.dataset_drift,
                "retrain": decision.retrain,
                "reasons": decision.reasons,
            }
        )
    )
    return 3 if decision.retrain else 0


if __name__ == "__main__":
    sys.exit(main())
