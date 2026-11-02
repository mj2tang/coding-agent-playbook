"""Stateless feature transforms. Anything that learns from data belongs in the model pipeline."""

import numpy as np
import pandas as pd


def log_transform(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if (out[col] < 0).any():
            raise ValueError(f"log_transform: {col} has negative values")
        out[f"log_{col}"] = np.log1p(out[col])
    return out


def build_features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    return log_transform(df, cfg["features"]["log_transform"])
