"""Data contracts: declare expectations at dataset boundaries and fail loudly."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class Column:
    dtype: str  # "float", "int", or "category"
    nullable: bool = False
    min: float | None = None
    max: float | None = None
    allowed: tuple[object, ...] | None = None


@dataclass(frozen=True)
class Contract:
    name: str
    columns: dict[str, Column]
    min_rows: int = 1
    key: tuple[str, ...] = field(default_factory=tuple)


class ContractViolation(ValueError):
    pass


def validate(df: pd.DataFrame, contract: Contract) -> pd.DataFrame:
    """Return df unchanged if it satisfies the contract, else raise listing every violation."""
    errors: list[str] = []
    if len(df) < contract.min_rows:
        errors.append(f"expected >= {contract.min_rows} rows, got {len(df)}")
    missing = set(contract.columns) - set(df.columns)
    if missing:
        errors.append(f"missing columns: {sorted(missing)}")
    for name, col in contract.columns.items():
        if name not in df.columns:
            continue
        s = df[name]
        if not col.nullable and s.isna().any():
            errors.append(f"{name}: {int(s.isna().sum())} nulls")
        if col.dtype == "float" and not pd.api.types.is_float_dtype(s):
            errors.append(f"{name}: expected float, got {s.dtype}")
        if col.dtype == "int" and not pd.api.types.is_integer_dtype(s):
            errors.append(f"{name}: expected int, got {s.dtype}")
        if col.min is not None and (s.dropna() < col.min).any():
            errors.append(f"{name}: values below {col.min}")
        if col.max is not None and (s.dropna() > col.max).any():
            errors.append(f"{name}: values above {col.max}")
        if col.allowed is not None and not s.dropna().isin(col.allowed).all():
            errors.append(f"{name}: values outside {list(col.allowed)}")
    if contract.key and df.duplicated(list(contract.key)).any():
        errors.append(f"duplicate keys on {contract.key}")
    if errors:
        raise ContractViolation(f"[{contract.name}] " + "; ".join(errors))
    return df
