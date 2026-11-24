"""Validation of uploaded batch files (PaySim format) for the app."""
from __future__ import annotations

import io

import pandas as pd

from src.data import TYPES

MAX_BATCH_ROWS = 20_000


def required_columns(uses_balances: bool) -> list[str]:
    return ["step", "type", "amount", "nameDest"] + (["oldbalanceOrg", "oldbalanceDest"] if uses_balances else [])


def check_batch(raw: bytes, uses_balances: bool, max_rows: int = MAX_BATCH_ROWS):
    """Validate an uploaded CSV. Returns (clean rows or None, errors, warnings)."""
    warns: list[str] = []
    required = required_columns(uses_balances)
    numeric = ["step", "amount"] + (["oldbalanceOrg", "oldbalanceDest"] if uses_balances else [])
    if not raw or not raw.strip():
        return None, ["The file is empty."], warns
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception:
        return None, ["The file could not be read as CSV. Save it as comma-separated values with a header row."], warns
    if df.empty:
        return None, ["The file has a header but no rows."], warns
    if len(df) > max_rows:
        return None, [f"The file has {len(df):,} rows; the limit is {max_rows:,}. Split it into smaller files."], warns
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None, ["Missing required columns: " + ", ".join(missing) + ". Use the template (PaySim format)."], warns
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["type"] = df["type"].astype(str).str.strip().str.upper()
    df["nameDest"] = df["nameDest"].astype(str)
    bad = df[numeric].isna().any(axis=1) | ~df["type"].isin(TYPES) | (df["amount"] < 0) | (df["step"] < 0)
    if bad.all():
        return None, ["No valid rows: check that numbers are numbers and that type is one of " + ", ".join(TYPES) + "."], warns
    if bad.any():
        warns.append(f"{int(bad.sum())} rows were skipped because of invalid numbers or an unknown type.")
    df = df[~bad].copy()
    df["step"] = df["step"].astype(int)
    return df, [], warns
