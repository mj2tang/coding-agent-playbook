import numpy as np
import pandas as pd

from {{pkg}}.features.selection import (
    correlated_to_drop,
    leakage_suspects,
    near_constant,
    select_features,
)

rng = np.random.default_rng(0)
N = 300
y = pd.Series(rng.integers(0, 2, N))
signal = y + rng.normal(0, 1.0, N)
X = pd.DataFrame(
    {
        "signal": signal,
        "signal_copy": signal * 2 + rng.normal(0, 0.01, N),  # redundant
        "weak": rng.normal(size=N),
        "const": np.r_[np.zeros(N - 1), 1.0],  # near-constant
        "leak": y.astype(float),  # leakage
    }
)


def test_individual_screens():
    assert near_constant(X) == ["const"]
    assert leakage_suspects(X, y) == ["leak"]
    assert correlated_to_drop(X[["signal", "signal_copy", "weak"]], y) in (
        ["signal"],
        ["signal_copy"],
    )


def test_select_features_reports_reasons():
    kept, reasons = select_features(X, y, {})
    assert "const" in reasons["near_constant"] and "leak" in reasons["leakage_suspect"]
    assert "weak" in kept and len(set(kept) & {"signal", "signal_copy"}) == 1
