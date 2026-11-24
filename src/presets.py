"""Six synthetic example transactions for the app and notebook 05. No real people or accounts."""
from __future__ import annotations

# Receiver profiles shown in the app, mapped to receiver-history feature values.
# "Some history" uses values close to the median of normal receivers in PaySim
# (about 5 earlier incoming transactions, last one about 21 hours ago).
RECEIVER_PROFILES = {
    "New account (no history)": {"count": 0, "total": 0.0, "hours": 744.0},
    "Some history": {"count": 5, "total": 900_000.0, "hours": 21.0},
    "Very active recently": {"count": 40, "total": 8_000_000.0, "hours": 1.0},
}

PRESETS = [
    {
        "key": "normal_payment",
        "title": "Normal payment",
        "story": "A customer pays a merchant 2,500 in the afternoon.",
        "type": "PAYMENT", "amount": 2_500.0, "hour": 14,
        "profile": "Some history", "oldbalanceOrg": 40_000.0, "oldbalanceDest": 0.0,
    },
    {
        "key": "small_transfer",
        "title": "Normal small transfer",
        "story": "A customer sends 15,000 of a 120,000 balance to a known account at 11:00.",
        "type": "TRANSFER", "amount": 15_000.0, "hour": 11,
        "profile": "Some history", "oldbalanceOrg": 120_000.0, "oldbalanceDest": 45_000.0,
    },
    {
        "key": "night_new_receiver",
        "title": "Large transfer to a brand-new receiver at night",
        "story": "At 03:00 the whole balance of 2,400,000 is sent to an account that never received money before.",
        "type": "TRANSFER", "amount": 2_400_000.0, "hour": 3,
        "profile": "New account (no history)", "oldbalanceOrg": 2_400_000.0, "oldbalanceDest": 0.0,
    },
    {
        "key": "cash_out_after_receiving",
        "title": "Cash-out right after receiving",
        "story": "An account that just received 2,400,000 cashes out all of it one hour later, at 04:00.",
        "type": "CASH_OUT", "amount": 2_400_000.0, "hour": 4,
        "profile": "Some history", "oldbalanceOrg": 2_400_000.0, "oldbalanceDest": 150_000.0,
    },
    {
        "key": "mule_many_transfers",
        "title": "Mule account receiving many transfers",
        "story": "A sender empties a 300,000 balance into an account that received 40 transfers recently.",
        "type": "TRANSFER", "amount": 300_000.0, "hour": 22,
        "profile": "Very active recently", "oldbalanceOrg": 300_000.0, "oldbalanceDest": 1_200_000.0,
    },
    {
        "key": "split_fraud",
        "title": "Split fraud with smaller amounts",
        "story": "A fraudster moves 450,000 of a 2,000,000 balance, one of several smaller pieces, at 02:00.",
        "type": "TRANSFER", "amount": 450_000.0, "hour": 2,
        "profile": "Some history", "oldbalanceOrg": 2_000_000.0, "oldbalanceDest": 60_000.0,
    },
]
