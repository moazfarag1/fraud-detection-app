"""Evasion tricks: change one thing about a fraud transaction and see if it slips through."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features import FRAUD_MAX_AMOUNT, HOURS_CAP, NEAR_MAX_RATIO, ROUND_UNIT

TRICKS = {
    "split_amount": "Split the amount into 3 to 5 smaller transfers",
    "receiver_with_history": "Use a receiver account with normal history instead of a new one",
    "daytime_hour": "Move the transfer to a daytime hour (14:00)",
    "round_amount": "Use a round, normal-looking amount (rounded down to 1,000)",
}


def _refresh_amount(df: pd.DataFrame) -> pd.DataFrame:
    df["log_amount"] = np.log1p(df["amount"])
    df["is_round_amount"] = ((df["amount"] > 0) & (np.mod(df["amount"], ROUND_UNIT) == 0)).astype("int8")
    df["is_near_max_amount"] = (df["amount"] >= NEAR_MAX_RATIO * FRAUD_MAX_AMOUNT).astype("int8")
    if "oldbalanceOrg" in df:
        df["amount_to_balance"] = (df["amount"] / df["oldbalanceOrg"].clip(lower=1.0)).clip(upper=1000.0)
    return df


def split_amount(rows: pd.DataFrame, seed: int = 0):
    """Each fraud becomes k pieces (k = 3..5). Returns the pieces and the original row number of each piece."""
    rng = np.random.default_rng(seed)
    parts, ids = [], []
    for i in range(len(rows)):
        r = rows.iloc[[i]]
        k = int(rng.integers(3, 6))
        piece = pd.concat([r] * k, ignore_index=True)
        piece["amount"] = float(r["amount"].iloc[0]) / k
        parts.append(piece)
        ids.extend([i] * k)
    out = _refresh_amount(pd.concat(parts, ignore_index=True))
    return out, np.array(ids)


def receiver_with_history(rows: pd.DataFrame, count: float, total: float, hours: float) -> pd.DataFrame:
    out = rows.copy()
    out["recv_count_before"] = float(count)
    out["recv_total_before"] = float(total)
    out["recv_is_new"] = 0
    out["recv_hours_since_last"] = float(min(hours, HOURS_CAP))
    return out


def daytime_hour(rows: pd.DataFrame, hour: int = 14) -> pd.DataFrame:
    out = rows.copy()
    out["hour"] = hour
    return out


def round_amount(rows: pd.DataFrame) -> pd.DataFrame:
    out = rows.copy()
    out["amount"] = np.maximum(np.floor(out["amount"] / ROUND_UNIT) * ROUND_UNIT, ROUND_UNIT)
    return _refresh_amount(out)
