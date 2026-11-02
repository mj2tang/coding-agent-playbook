"""Feature selection report: python -m {{pkg}}.features.select_report --config configs/base.yaml

Runs the selection screens on the train split, then ranks survivors by permutation importance on
validation. Writes reports/feature_selection.md; adopting a selection means setting
`features.keep` in a config via a normal task.
"""

import argparse
from pathlib import Path

from ..config import load_config, set_seed
from ..data.load import load_dataset, split
from ..models.train import features_and_target, make_model
from .selection import permutation_ranking, select_features


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--out", default="reports/feature_selection.md")
    a = p.parse_args()
    cfg = load_config(a.config)
    set_seed(cfg["seed"])
    train, valid = split(load_dataset(cfg), cfg)
    X, y = features_and_target(train, cfg)
    kept, reasons = select_features(X, y, cfg)
    model = make_model(cfg).fit(X[kept], y)
    Xv, yv = features_and_target(valid, cfg)
    ranking = permutation_ranking(model, Xv[kept], yv, seed=cfg["seed"])
    lines = ["# Feature selection report", "", f"Kept {len(kept)} of {X.shape[1]} features.", ""]
    for reason, cols in reasons.items():
        lines.append(f"- Dropped as **{reason}**: {cols or 'none'}")
    lines += [
        "",
        "## Permutation importance (validation, ROC-AUC drop)",
        "",
        "| feature | importance | std |",
        "|---|---|---|",
    ]
    lines += [f"| {r.feature} | {r.importance:.4f} | {r.std:.4f} |" for r in ranking.itertuples()]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
