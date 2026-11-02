import numpy as np
import pandas as pd

from {{pkg}}.analysis.eda import profile, to_markdown


def test_profile_flags_leakage_ids_and_constants():
    n = 200
    y = pd.Series(np.r_[np.zeros(n // 2), np.ones(n // 2)].astype(int))
    df = pd.DataFrame(
        {
            "leak": y * 10.0,  # perfectly separates the target
            "row_id": np.arange(n),  # ID-like
            "const": 1.0,
            "noise": np.random.default_rng(0).normal(size=n),
            "target": y,
        }
    )
    p = profile(df, "target")
    cols = {r["column"]: r for r in p["columns"]}
    assert cols["leak"]["leakage_suspect"]
    assert cols["row_id"]["id_like"]
    assert cols["const"]["constant"]
    assert not cols["noise"]["leakage_suspect"]
    md = to_markdown(p)
    assert "leak" in md and "# EDA report" in md
