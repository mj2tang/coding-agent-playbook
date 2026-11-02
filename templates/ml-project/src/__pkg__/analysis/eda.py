"""Automated first-pass EDA: python -m {{pkg}}.analysis.eda --config configs/base.yaml

Writes reports/eda.md with the checks practitioners do first: shape and dtypes, missingness,
cardinality, duplicates, target balance, numeric summaries, and *leakage suspects* (features
that predict the target almost perfectly on their own, or look like IDs).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score

from ..config import load_config
from ..data.load import TARGET, load_dataset, split


def single_feature_auc(x: pd.Series, y: pd.Series) -> float | None:
    """Direction-free AUC of one numeric feature against a binary target (0.5 = no signal)."""
    mask = x.notna()
    if not pd.api.types.is_numeric_dtype(x) or y[mask].nunique() != 2 or x[mask].nunique() < 2:
        return None
    auc = roc_auc_score(y[mask], x[mask])
    return float(max(auc, 1 - auc))


def profile(df: pd.DataFrame, target: str, leakage_auc: float = 0.98) -> dict:
    y = df[target]
    features = [c for c in df.columns if c != target]
    rows = []
    for c in features:
        s = df[c]
        auc = single_feature_auc(s, y) if y.nunique() == 2 else None
        rows.append(
            {
                "column": c,
                "dtype": str(s.dtype),
                "missing_pct": round(100 * s.isna().mean(), 2),
                "unique": int(s.nunique()),
                "id_like": bool(s.nunique() == len(s) and len(s) > 1),
                "constant": bool(s.nunique(dropna=True) <= 1),
                "single_feature_auc": None if auc is None else round(auc, 4),
                "leakage_suspect": bool(auc is not None and auc >= leakage_auc),
            }
        )
    return {
        "n_rows": len(df),
        "n_features": len(features),
        "duplicate_rows": int(df.duplicated().sum()),
        "target_distribution": {
            str(k): round(float(v), 4) for k, v in y.value_counts(normalize=True).items()
        },
        "columns": rows,
    }


def to_markdown(p: dict) -> str:
    lines = [
        "# EDA report (training split)",
        "",
        f"- Rows: {p['n_rows']} · Features: {p['n_features']} · Duplicate rows: {p['duplicate_rows']}",
        f"- Target distribution: {p['target_distribution']}",
        "",
    ]
    suspects = [r["column"] for r in p["columns"] if r["leakage_suspect"] or r["id_like"]]
    flags = [r["column"] for r in p["columns"] if r["constant"] or r["missing_pct"] > 30]
    lines += [
        "## Flags",
        f"- Leakage / ID suspects: {suspects or 'none'}",
        f"- Constant or >30% missing: {flags or 'none'}",
        "",
        "## Columns",
        "| column | dtype | missing % | unique | single-feature AUC | flags |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(p["columns"], key=lambda r: -(r["single_feature_auc"] or 0)):
        f = ",".join(k for k in ("leakage_suspect", "id_like", "constant") if r[k])
        lines.append(
            f"| {r['column']} | {r['dtype']} | {r['missing_pct']} | {r['unique']} | "
            f"{r['single_feature_auc'] if r['single_feature_auc'] is not None else '—'} | {f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a config value")
    p.add_argument("--out", default="reports/eda.md")
    a = p.parse_args()
    cfg = load_config(a.config, a.set)
    train, _ = split(load_dataset(cfg), cfg)  # EDA on train only: never look at validation
    leakage_auc = cfg.get("feature_selection", {}).get("leakage_auc", 0.98)
    report = profile(train, TARGET, leakage_auc)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(to_markdown(report))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
