import numpy as np
import pandas as pd
import pytest

from {{pkg}}.features.build import log_transform


def test_log_transform_known_values():
    out = log_transform(pd.DataFrame({"a": [0.0, np.e - 1]}), ["a"])
    assert out["log_a"].tolist() == pytest.approx([0.0, 1.0])
    assert "a" in out  # original column kept


def test_log_transform_rejects_negatives():
    with pytest.raises(ValueError):
        log_transform(pd.DataFrame({"a": [-1.0]}), ["a"])
