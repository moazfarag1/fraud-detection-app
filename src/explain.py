"""Rule-based "warning signs" in plain English.

These are simple, readable checks on the same features the model uses. They help a
human reviewer, but they are NOT the model's exact reasoning.
"""
from __future__ import annotations

import pandas as pd

NIGHT_HOURS = set(range(0, 6))
LARGE_AMOUNT = 1_000_000.0
BUSY_RECEIVER_COUNT = 20
RECENT_HOURS = 6


def warning_signs(row: pd.Series, use_balances: bool = True) -> list[str]:
    """Return the warning signs found for one feature row (see src/features.py)."""
    signs: list[str] = []
    if row.get("recv_is_new", 0) == 1:
        signs.append("Money goes to a brand-new receiver account (no earlier incoming transfers).")
    else:
        if row.get("recv_count_before", 0) >= BUSY_RECEIVER_COUNT:
            signs.append("Receiver got many transfers before (possible collection or mule account).")
        if row.get("recv_hours_since_last", 999) <= RECENT_HOURS:
            signs.append("Receiver got another transfer in the last few hours.")
    if row.get("is_near_max_amount", 0) == 1:
        signs.append("Amount is at the 10,000,000 maximum that large frauds are split into.")
    elif row.get("amount", 0) >= LARGE_AMOUNT:
        signs.append("Very large amount (1,000,000 or more).")
    if int(row.get("hour", 12)) in NIGHT_HOURS:
        signs.append("Unusual hour (night, 00:00 to 05:59).")
    if use_balances:
        ratio = row.get("amount_to_balance")
        old_org = row.get("oldbalanceOrg")
        if pd.notna(ratio) and pd.notna(old_org) and old_org > 0 and 0.99 <= ratio <= 1.01:
            signs.append("The transaction empties the whole balance of the sender.")
        old_dest = row.get("oldbalanceDest")
        if pd.notna(old_dest) and old_dest == 0 and row.get("is_transfer", 0) == 1:
            signs.append("Receiver account shows a zero balance before the transfer.")
    return signs
