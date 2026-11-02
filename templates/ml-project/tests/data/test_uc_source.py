"""The Unity Catalog source path, exercised offline with a fake Spark session."""

import pandas as pd
import pytest

from {{pkg}}.spark import read_table


class FakeFrame:
    def __init__(self, df):
        self.df = df

    def limit(self, n):
        return FakeFrame(self.df.head(n))

    def toPandas(self):  # noqa: N802 - Spark API name
        return self.df


class FakeSpark:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return FakeFrame(self.tables[name])


def test_read_table_uses_three_level_names():
    spark = FakeSpark({"main.ml.orders": pd.DataFrame({"x": [1, 2, 3]})})
    assert len(read_table("main.ml.orders", limit=2, spark=spark)) == 2
    with pytest.raises(ValueError):
        read_table("orders", spark=spark)
