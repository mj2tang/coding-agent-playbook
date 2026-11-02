import numpy as np
import pandas as pd
import pytest

from {{pkg}}.monitoring.drift import DriftConfig, column_drift, detect_drift, psi

rng = np.random.default_rng(0)


def test_no_drift_on_same_distribution_small_sample():
    a = pd.Series(rng.normal(0, 1, 500), name="x")
    b = pd.Series(rng.normal(0, 1, 500), name="x")
    r = column_drift(a, b)
    assert r.method == "ks" and not r.drifted


def test_detects_mean_shift_small_and_large_samples():
    small = column_drift(
        pd.Series(rng.normal(0, 1, 500), name="x"), pd.Series(rng.normal(1, 1, 500), name="x")
    )
    large = column_drift(
        pd.Series(rng.normal(0, 1, 5000), name="x"), pd.Series(rng.normal(1, 1, 5000), name="x")
    )
    assert small.drifted and small.method == "ks"
    assert large.drifted and large.method == "wasserstein_normed"


def test_categorical_methods_and_new_category():
    ref = pd.Series(["a", "b", "c"] * 100, name="c")
    cur = pd.Series(["a"] * 250 + ["d"] * 50, name="c")
    r = column_drift(ref, cur)
    assert r.kind == "categorical" and r.method == "chi_squared" and r.drifted
    big = column_drift(
        pd.Series(["a", "b"] * 1000, name="c"), pd.Series(["a"] * 1800 + ["b"] * 200, name="c")
    )
    assert big.method == "jensen_shannon" and big.drifted


def test_psi_known_properties():
    a = pd.Series(rng.normal(0, 1, 5000))
    assert psi(a, a) == pytest.approx(0.0, abs=1e-9)
    assert psi(a, a + 2) > 0.25


def test_dataset_drift_uses_share_threshold():
    ref = pd.DataFrame({"x": rng.normal(0, 1, 300), "y": rng.normal(0, 1, 300)})
    cur = pd.DataFrame({"x": rng.normal(3, 1, 300), "y": rng.normal(0, 1, 300)})
    assert detect_drift(ref, cur, cfg=DriftConfig(drift_share=0.5)).dataset_drift
    assert not detect_drift(ref, cur, cfg=DriftConfig(drift_share=0.75)).dataset_drift


def test_missing_column_raises():
    with pytest.raises(ValueError):
        detect_drift(pd.DataFrame({"x": [1.0, 2.0]}), pd.DataFrame({"z": [1.0]}), ["x"])
