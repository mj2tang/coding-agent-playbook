import numpy as np
import pytest

from {{pkg}}.evaluation.metrics import classification_metrics


def test_known_answer():
    m = classification_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.35, 0.8]))
    assert m["roc_auc"] == pytest.approx(0.75)
    assert m["accuracy"] == pytest.approx(0.75)


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        classification_metrics(np.array([0, 1]), np.array([0.5]))
