"""Dataset loading. Replace the example source with your own; keep the contract check."""

from typing import Any

import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from .contracts import Column, Contract, validate

TARGET = "target"

EXAMPLE_CONTRACT = Contract(
    name="breast_cancer",
    columns={
        "mean radius": Column("float", min=0),
        "mean area": Column("float", min=0),
        "worst area": Column("float", min=0),
        TARGET: Column("int", allowed=(0, 1)),
    },
    min_rows=100,
)


def load_dataset(cfg: dict[str, Any]) -> pd.DataFrame:
    source = cfg["data"]["source"]
    if source == "sklearn_breast_cancer":
        frame = load_breast_cancer(as_frame=True).frame
    elif source == "uc_table":
        # Databricks: read the Unity Catalog table named in config; the contract still applies.
        from ..spark import read_table

        frame = read_table(cfg["data"]["table"], limit=cfg["data"].get("limit"))
    else:
        raise ValueError(f"unknown data source: {source}")
    return validate(frame, EXAMPLE_CONTRACT)


def split(df: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split before any fitting so preprocessing never sees validation rows."""
    train, valid = train_test_split(
        df,
        test_size=cfg["data"]["valid_size"],
        random_state=cfg["seed"],
        stratify=df[TARGET],
    )
    return train.reset_index(drop=True), valid.reset_index(drop=True)
