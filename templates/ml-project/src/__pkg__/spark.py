"""Spark access for Databricks: the active session on a cluster/serverless job, else Databricks Connect.

Imported lazily so local development and CI never need pyspark.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def get_spark() -> Any:
    try:
        from pyspark.sql import SparkSession

        active = SparkSession.getActiveSession()
        if active is not None:
            return active
    except ImportError:
        pass
    try:
        from databricks.connect import DatabricksSession
    except ImportError as e:
        raise RuntimeError(
            "No Spark session. Run on Databricks, or install the 'databricks' extra "
            "(uv sync --extra databricks) and configure Databricks Connect."
        ) from e
    return DatabricksSession.builder.getOrCreate()


def read_table(name: str, limit: int | None = None, spark: Any = None) -> pd.DataFrame:
    """Read a Unity Catalog table (catalog.schema.table) into pandas."""
    if name.count(".") != 2:
        raise ValueError(f"expected a three-level Unity Catalog name catalog.schema.table, got {name!r}")
    table = (spark or get_spark()).table(name)
    if limit is not None:
        table = table.limit(limit)
    return table.toPandas()
