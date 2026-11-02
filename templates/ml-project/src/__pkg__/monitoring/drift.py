"""Data drift detection between a reference dataset (e.g. training data) and a current batch.

Defaults follow the widely used Evidently conventions:
- reference <= 1000 rows: two-sample KS test (numeric) / chi-squared test (categorical), drift if p <= 0.05
- reference  > 1000 rows: normalised Wasserstein distance (numeric) / Jensen-Shannon distance
  (categorical), drift if distance >= 0.1
- a column is "categorical" if it is non-numeric or has <= 5 unique values
- the dataset drifts if the share of drifting columns >= 0.5
PSI is reported alongside for teams that use the 0.1 (watch) / 0.25 (act) convention.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import jensenshannon

SMALL_SAMPLE = 1000
CATEGORICAL_MAX_UNIQUE = 5


@dataclass(frozen=True)
class DriftConfig:
    p_value: float = 0.05
    distance: float = 0.1
    drift_share: float = 0.5
    psi_bins: int = 10


@dataclass(frozen=True)
class ColumnDrift:
    column: str
    kind: str  # "numeric" | "categorical"
    method: str
    statistic: float
    threshold: float
    drifted: bool
    psi: float


@dataclass(frozen=True)
class DriftReport:
    columns: list[ColumnDrift]
    drift_share: float
    dataset_drift: bool

    def to_dict(self) -> dict:
        return {
            "dataset_drift": self.dataset_drift,
            "drift_share": round(self.drift_share, 4),
            "drifted_columns": [c.column for c in self.columns if c.drifted],
            "columns": [asdict(c) for c in self.columns],
        }


def is_categorical(s: pd.Series) -> bool:
    return not pd.api.types.is_numeric_dtype(s) or s.nunique(dropna=True) <= CATEGORICAL_MAX_UNIQUE


def psi(reference: pd.Series, current: pd.Series, bins: int = 10, eps: float = 1e-6) -> float:
    """Population stability index. Numeric columns use reference-quantile bins."""
    ref, cur = reference.dropna(), current.dropna()
    p: np.ndarray
    q: np.ndarray
    if is_categorical(ref):
        cats = sorted(set(ref.astype(str)) | set(cur.astype(str)))
        p = ref.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
        q = cur.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    else:
        edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
        if len(edges) < 2:
            return 0.0
        edges[0], edges[-1] = -np.inf, np.inf
        p = np.histogram(ref, edges)[0] / len(ref)
        q = np.histogram(cur, edges)[0] / len(cur)
    p, q = np.clip(p, eps, None), np.clip(q, eps, None)
    return float(np.sum((q - p) * np.log(q / p)))


def column_drift(reference: pd.Series, current: pd.Series, cfg: DriftConfig | None = None) -> ColumnDrift:
    cfg = cfg or DriftConfig()
    ref, cur = reference.dropna(), current.dropna()
    if len(ref) == 0 or len(cur) == 0:
        raise ValueError(f"{reference.name}: empty reference or current data after dropping nulls")
    categorical = is_categorical(ref)
    small = len(ref) <= SMALL_SAMPLE
    if categorical:
        cats = sorted(set(ref.astype(str)) | set(cur.astype(str)))
        ref_counts = ref.astype(str).value_counts().reindex(cats, fill_value=0).to_numpy()
        cur_counts = cur.astype(str).value_counts().reindex(cats, fill_value=0).to_numpy()
        if small:
            if len(cats) == 1:
                p = 1.0  # a single shared category cannot drift
            else:
                p = stats.chi2_contingency(np.vstack([ref_counts, cur_counts])).pvalue
            method, statistic, threshold, drifted = (
                "chi_squared",
                float(p),
                cfg.p_value,
                p <= cfg.p_value,
            )
        else:
            d = jensenshannon(ref_counts / ref_counts.sum(), cur_counts / cur_counts.sum(), base=2)
            method, statistic, threshold, drifted = (
                "jensen_shannon",
                float(d),
                cfg.distance,
                d >= cfg.distance,
            )
    else:
        if small:
            p = stats.ks_2samp(ref, cur).pvalue
            method, statistic, threshold, drifted = "ks", float(p), cfg.p_value, p <= cfg.p_value
        else:
            scale = float(np.std(ref)) or 1.0
            d = stats.wasserstein_distance(ref, cur) / scale
            method, statistic, threshold, drifted = (
                "wasserstein_normed",
                float(d),
                cfg.distance,
                d >= cfg.distance,
            )
    return ColumnDrift(
        column=str(reference.name),
        kind="categorical" if categorical else "numeric",
        method=method,
        statistic=round(statistic, 6),
        threshold=threshold,
        drifted=bool(drifted),
        psi=round(psi(ref, cur, cfg.psi_bins), 6),
    )


def detect_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    columns: list[str] | None = None,
    cfg: DriftConfig | None = None,
) -> DriftReport:
    cfg = cfg or DriftConfig()
    columns = columns or [c for c in reference.columns if c in current.columns]
    missing = [c for c in columns if c not in current.columns]
    if missing:
        raise ValueError(f"current data is missing columns: {missing}")
    results = [column_drift(reference[c], current[c], cfg) for c in columns]
    share = sum(r.drifted for r in results) / len(results) if results else 0.0
    return DriftReport(columns=results, drift_share=share, dataset_drift=share >= cfg.drift_share)
