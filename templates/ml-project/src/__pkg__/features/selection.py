"""Feature selection helpers. All functions take *training* data only.

Typical order: drop near-constant → screen leakage suspects → prune highly correlated pairs →
confirm with permutation importance measured on validation data (see `permutation_ranking`).
"""

from __future__ import annotations

import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score


def near_constant(X: pd.DataFrame, threshold: float = 0.99) -> list[str]:
    """Columns whose most frequent value covers >= threshold of rows."""
    return [c for c in X.columns if X[c].value_counts(normalize=True, dropna=False).iloc[0] >= threshold]


def leakage_suspects(X: pd.DataFrame, y: pd.Series, auc_threshold: float = 0.98) -> list[str]:
    """Numeric columns that alone separate a binary target almost perfectly."""
    out = []
    for c in X.select_dtypes("number").columns:
        mask = X[c].notna()
        if y[mask].nunique() == 2 and X[c][mask].nunique() > 1:
            auc = roc_auc_score(y[mask], X[c][mask])
            if max(auc, 1 - auc) >= auc_threshold:
                out.append(c)
    return out


def correlated_to_drop(X: pd.DataFrame, y: pd.Series, threshold: float = 0.95) -> list[str]:
    """For each numeric pair with |corr| >= threshold, drop the one less correlated with the target."""
    num = X.select_dtypes("number")
    corr = num.corr().abs().to_numpy()
    target_corr = num.corrwith(y).abs().fillna(0).to_numpy()
    cols = list(num.columns)
    drop: set[str] = set()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if cols[i] in drop or cols[j] in drop:
                continue
            if corr[i, j] >= threshold:
                drop.add(cols[i] if target_corr[i] < target_corr[j] else cols[j])
    return sorted(drop)


def permutation_ranking(
    model, X_valid: pd.DataFrame, y_valid: pd.Series, seed: int, n_repeats: int = 5
) -> pd.DataFrame:
    """Permutation importance on held-out data (model already fitted on train)."""
    r = permutation_importance(
        model, X_valid, y_valid, n_repeats=n_repeats, random_state=seed, scoring="roc_auc"
    )
    return (
        pd.DataFrame({"feature": X_valid.columns, "importance": r.importances_mean, "std": r.importances_std})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def select_features(X: pd.DataFrame, y: pd.Series, cfg: dict) -> tuple[list[str], dict[str, list[str]]]:
    """Return kept columns and the reason each dropped column was removed."""
    fs = cfg.get("feature_selection", {})
    reasons = {
        "near_constant": near_constant(X, fs.get("near_constant_threshold", 0.99)),
        "leakage_suspect": leakage_suspects(X, y, fs.get("leakage_auc", 0.98)),
    }
    remaining = X.drop(columns=sorted(set(sum(reasons.values(), []))))
    reasons["correlated"] = correlated_to_drop(remaining, y, fs.get("corr_threshold", 0.95))
    dropped = set(sum(reasons.values(), []))
    kept = [c for c in X.columns if c not in dropped]
    return kept, reasons
