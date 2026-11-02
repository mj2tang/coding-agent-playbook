import pandas as pd
import pytest

from {{pkg}}.data.contracts import Column, Contract, ContractViolation, validate
from {{pkg}}.data.load import load_dataset

pytestmark = pytest.mark.data

C = Contract("tiny", {"x": Column("float", min=0), "y": Column("int", allowed=(0, 1))}, key=("id",))


def test_valid_frame_passes():
    df = pd.DataFrame({"id": [1, 2], "x": [0.5, 1.0], "y": [0, 1]})
    assert validate(df, C) is df


def test_reports_every_violation():
    df = pd.DataFrame({"id": [1, 1], "x": [-1.0, None], "y": [0, 2]})
    with pytest.raises(ContractViolation) as e:
        validate(df, C)
    msg = str(e.value)
    for expected in ["nulls", "below 0", "outside", "duplicate keys"]:
        assert expected in msg


def test_example_dataset_meets_contract(cfg):
    assert len(load_dataset(cfg)) > 100
