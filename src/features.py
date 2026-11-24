"""Feature engineering shared by training and the app.

The same functions build features for the 6.3M-row training data, for an uploaded
batch file, and for a single transaction typed into the app, so the model always
sees features computed in exactly the same way.

Feature groups
--------------
BASIC     what any payment system knows about the transaction itself
RECEIVER  history of the receiving account, using only EARLIER hours (money-mule signal)
PRE       balances known before the transaction (available at approval time)
POST      balances after the transaction and balance "errors" (leaky in PaySim)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

HOURS_CAP = 744.0          # PaySim covers 743 hours; "no earlier transfer" is filled with this cap
FRAUD_MAX_AMOUNT = 10_000_000.0  # largest single fraud amount in PaySim (verified in notebook 03)
NEAR_MAX_RATIO = 0.99
ROUND_UNIT = 1_000.0

BASIC = ["is_transfer", "amount", "log_amount", "hour", "is_round_amount", "is_near_max_amount"]
RECEIVER = ["recv_count_before", "recv_total_before", "recv_is_new", "recv_hours_since_last"]
PRE = ["oldbalanceOrg", "oldbalanceDest", "amount_to_balance"]
POST = ["newbalanceOrig", "newbalanceDest", "errorOrig", "errorDest"]

FEATURE_SETS = {
    "R": BASIC + RECEIVER,
    "P": BASIC + RECEIVER + PRE,
    "L": BASIC + RECEIVER + PRE + POST,
}

FEATURE_LABELS = {
    "is_transfer": "Type is TRANSFER (vs CASH_OUT)",
    "amount": "Amount",
    "log_amount": "Amount (log scale)",
    "hour": "Hour of day",
    "is_round_amount": "Round amount",
    "is_near_max_amount": "Amount near the 10M maximum",
    "recv_count_before": "Receiver: transfers received before",
    "recv_total_before": "Receiver: total received before",
    "recv_is_new": "Receiver is a new account",
    "recv_hours_since_last": "Receiver: hours since last incoming",
    "oldbalanceOrg": "Sender balance before",
    "oldbalanceDest": "Receiver balance before",
    "amount_to_balance": "Amount / sender balance",
    "newbalanceOrig": "Sender balance after",
    "newbalanceDest": "Receiver balance after",
    "errorOrig": "Sender balance error",
    "errorDest": "Receiver balance error",
}


def receiver_history(df: pd.DataFrame) -> pd.DataFrame:
    """History of each receiving account (nameDest) using only STRICTLY EARLIER steps.

    For a transaction at step s going to account D we count only the transactions
    that D received at steps < s. Transactions in the same hour (step) are NOT
    counted, and nothing from the future is used. Works on any rows that have
    the columns step, nameDest and amount, in any order.

    Returns a DataFrame aligned with df.index with columns:
    recv_count_before, recv_total_before, recv_is_new, recv_hours_since_last
    """
    key = df[["nameDest", "step"]].copy()
    key["amount"] = df["amount"].astype("float64")

    # 1) one row per (receiver, hour): how many transfers and how much money arrived in that hour
    per_step = (
        key.groupby(["nameDest", "step"], observed=True, sort=True)["amount"]
        .agg(cnt="size", tot="sum")
        .reset_index()
    )
    # 2) running totals per receiver, then subtract the current hour so only EARLIER hours count
    g = per_step.groupby("nameDest", observed=True, sort=False)
    per_step["recv_count_before"] = g["cnt"].cumsum() - per_step["cnt"]
    per_step["recv_total_before"] = g["tot"].cumsum() - per_step["tot"]
    # 3) the previous hour in which this receiver got money (NaN if none)
    per_step["prev_step"] = g["step"].shift(1)
    per_step["recv_hours_since_last"] = (per_step["step"] - per_step["prev_step"]).astype("float64")

    out = key.merge(
        per_step[["nameDest", "step", "recv_count_before", "recv_total_before", "recv_hours_since_last"]],
        on=["nameDest", "step"],
        how="left",
    )
    out.index = df.index
    out["recv_count_before"] = out["recv_count_before"].astype("float64")
    out["recv_total_before"] = out["recv_total_before"].astype("float64")
    out["recv_is_new"] = (out["recv_count_before"] == 0).astype("int8")
    out["recv_hours_since_last"] = out["recv_hours_since_last"].fillna(HOURS_CAP).clip(upper=HOURS_CAP)
    return out[RECEIVER]


def basic_features(df: pd.DataFrame) -> pd.DataFrame:
    amount = df["amount"].astype("float64").clip(lower=0)
    step = df["step"].astype("int64")
    out = pd.DataFrame(index=df.index)
    out["is_transfer"] = (df["type"].astype(str) == "TRANSFER").astype("int8")
    out["amount"] = amount
    out["log_amount"] = np.log1p(amount)
    out["hour"] = (step % 24).astype("int8")
    out["day"] = (step // 24).astype("int16")  # kept for analysis, not used by the models
    out["is_round_amount"] = ((amount > 0) & (np.mod(amount, ROUND_UNIT) == 0)).astype("int8")
    out["is_near_max_amount"] = (amount >= NEAR_MAX_RATIO * FRAUD_MAX_AMOUNT).astype("int8")
    return out


def balance_features(df: pd.DataFrame) -> pd.DataFrame:
    amount = df["amount"].astype("float64")
    old_o = df["oldbalanceOrg"].astype("float64")
    new_o = df["newbalanceOrig"].astype("float64")
    old_d = df["oldbalanceDest"].astype("float64")
    new_d = df["newbalanceDest"].astype("float64")
    out = pd.DataFrame(index=df.index)
    out["oldbalanceOrg"] = old_o
    out["oldbalanceDest"] = old_d
    # safe division: a zero balance is treated as 1 so the ratio stays finite; capped at 1000
    out["amount_to_balance"] = (amount / old_o.clip(lower=1.0)).clip(upper=1000.0)
    out["newbalanceOrig"] = new_o
    out["newbalanceDest"] = new_d
    out["errorOrig"] = old_o - amount - new_o
    out["errorDest"] = old_d + amount - new_d
    return out


def build_features(df: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build every feature group for rows in PaySim format.

    If `history` is None the receiver history is computed from df itself
    (used for the full dataset and for uploaded batch files).
    Balance columns that are missing (single-transaction input) are filled with NaN.
    """
    df = df.copy()
    for col in ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
        if col not in df.columns:
            df[col] = np.nan
    if history is None:
        history = receiver_history(df)
    feats = pd.concat([basic_features(df), history, balance_features(df)], axis=1)
    return feats


def single_transaction(
    tx_type: str,
    amount: float,
    hour: int,
    recv_count_before: float,
    recv_total_before: float,
    recv_hours_since_last: float,
    oldbalanceOrg: float | None = None,
    oldbalanceDest: float | None = None,
) -> pd.DataFrame:
    """Features for one transaction typed into the app (receiver history given directly)."""
    row = pd.DataFrame(
        {
            "step": [int(hour)],
            "type": [tx_type],
            "amount": [float(amount)],
            "oldbalanceOrg": [np.nan if oldbalanceOrg is None else float(oldbalanceOrg)],
            "oldbalanceDest": [np.nan if oldbalanceDest is None else float(oldbalanceDest)],
        }
    )
    count = max(float(recv_count_before), 0.0)
    hist = pd.DataFrame(
        {
            "recv_count_before": [count],
            "recv_total_before": [max(float(recv_total_before), 0.0) if count > 0 else 0.0],
            "recv_is_new": [int(count == 0)],
            "recv_hours_since_last": [HOURS_CAP if count == 0 else float(min(max(recv_hours_since_last, 1.0), HOURS_CAP))],
        }
    )
    return build_features(row, history=hist)
