"""Unit tests for src/features.py, src/explain.py and src/scoring.py."""
import numpy as np
import pandas as pd
import pytest

from src import explain, features as F, scoring


def tx(step, dest, amount, typ="TRANSFER"):
    return {"step": step, "type": typ, "amount": amount, "nameDest": dest,
            "oldbalanceOrg": 1000.0, "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0}


def test_zero_amount_is_safe():
    f = F.build_features(pd.DataFrame([tx(1, "C1", 0.0)]))
    assert f.loc[0, "amount"] == 0
    assert f.loc[0, "log_amount"] == 0
    assert f.loc[0, "is_round_amount"] == 0
    assert np.isfinite(f[F.FEATURE_SETS["L"]].to_numpy()).all()


def test_huge_amount_flags_and_stays_finite():
    f = F.build_features(pd.DataFrame([tx(1, "C1", 9.99e9)]))
    assert f.loc[0, "is_near_max_amount"] == 1
    assert f.loc[0, "amount_to_balance"] == 1000.0  # capped
    assert np.isfinite(f[F.FEATURE_SETS["L"]].to_numpy()).all()


def test_zero_sender_balance_safe_division():
    row = tx(1, "C1", 500.0)
    row["oldbalanceOrg"] = 0.0
    f = F.build_features(pd.DataFrame([row]))
    assert f.loc[0, "amount_to_balance"] == 500.0


def test_new_receiver_and_missing_history():
    f = F.build_features(pd.DataFrame([tx(5, "C_NEW", 100.0)]))
    assert f.loc[0, "recv_is_new"] == 1
    assert f.loc[0, "recv_count_before"] == 0
    assert f.loc[0, "recv_total_before"] == 0
    assert f.loc[0, "recv_hours_since_last"] == F.HOURS_CAP


def test_history_counts_only_strictly_earlier_steps():
    df = pd.DataFrame([tx(1, "A", 100), tx(3, "A", 50), tx(3, "A", 70), tx(8, "A", 10)])
    h = F.receiver_history(df)
    assert h["recv_count_before"].tolist() == [0, 1, 1, 3]
    assert h["recv_total_before"].tolist() == [0, 100, 100, 220]
    assert h["recv_hours_since_last"].tolist() == [F.HOURS_CAP, 2, 2, 5]


def test_no_future_leakage():
    rng = np.random.default_rng(0)
    n = 2000
    df = pd.DataFrame({"step": rng.integers(1, 100, n), "type": "TRANSFER",
                       "amount": rng.uniform(1, 1000, n), "nameDest": rng.choice(list("ABCDEFG"), n)})
    full = F.receiver_history(df)
    past = df[df["step"] <= 50]
    assert np.allclose(F.receiver_history(past).to_numpy(), full.loc[past.index].to_numpy())


def test_row_order_does_not_matter():
    df = pd.DataFrame([tx(4, "B", 5), tx(1, "B", 7), tx(2, "C", 9), tx(9, "B", 1)])
    a = F.receiver_history(df)
    b = F.receiver_history(df.iloc[::-1]).loc[a.index]
    assert np.allclose(a.to_numpy(), b.to_numpy())


def test_single_transaction_matches_feature_sets():
    f = F.single_transaction("CASH_OUT", 1000.0, 3, 0, 0, 744, 1000.0, 0.0)
    for cols in F.FEATURE_SETS.values():
        assert set(F.FEATURE_SETS["P"]).issubset(f.columns)
    assert f.loc[0, "is_transfer"] == 0 and f.loc[0, "hour"] == 3 and f.loc[0, "recv_is_new"] == 1


def test_warning_signs_plain_english():
    f = F.single_transaction("TRANSFER", 2_000_000.0, 2, 0, 0, 744, 2_000_000.0, 0.0)
    signs = explain.warning_signs(f.iloc[0])
    assert any("brand-new receiver" in s for s in signs)
    assert any("night" in s for s in signs)
    assert any("empties" in s for s in signs)


def test_risk_points_mapping_and_verdicts():
    t1, t2 = 0.9, 0.99
    pts = scoring.risk_points(np.array([0.0, t1, t2, 1.0]), t1, t2)
    assert np.allclose(pts, [0, 50, 80, 100])
    assert scoring.verdict(0.5, t1, t2) == "Approve"
    assert scoring.verdict(0.95, t1, t2) == "Review"
    assert scoring.verdict(0.995, t1, t2) == "Block"


@pytest.mark.parametrize("typ", ["PAYMENT", "CASH_IN", "DEBIT"])
def test_unscored_types_are_low_risk(typ):
    model, meta = scoring.load_model(), scoring.load_meta()
    f = F.single_transaction(typ, 100.0, 12, 5, 100.0, 10, 1000.0, 0.0)
    out = scoring.score_frame(model, meta, f, pd.Series([typ]))
    assert out["verdict"].iloc[0] == scoring.NOT_SCORED


# ---------------------------------------------------------------- batch file validation
from src import batch  # noqa: E402

HEADER = "step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest\n"


def test_batch_empty_file():
    df, errs, _ = batch.check_batch(b"", True)
    assert df is None and "empty" in errs[0]


def test_batch_header_only():
    df, errs, _ = batch.check_batch(HEADER.encode(), True)
    assert df is None and "no rows" in errs[0]


def test_batch_missing_columns():
    df, errs, _ = batch.check_batch(b"step,type,amount\n1,TRANSFER,100\n", True)
    assert df is None and "Missing required columns" in errs[0]


def test_batch_wrong_types_are_skipped():
    raw = (HEADER + "1,TRANSFER,abc,C1,10,0,C2,0,0\n2,TRANSFER,50,C1,50,0,C2,0,0\n3,BITCOIN,5,C1,5,0,C2,0,0\n").encode()
    df, errs, warns = batch.check_batch(raw, True)
    assert not errs and len(df) == 1 and "2 rows were skipped" in warns[0]


def test_batch_too_many_rows():
    raw = (HEADER + "1,TRANSFER,5,C1,5,0,C2,0,0\n" * 30).encode()
    df, errs, _ = batch.check_batch(raw, True, max_rows=20)
    assert df is None and "limit" in errs[0]


def test_batch_sample_file_is_valid():
    from src.data import SAMPLE_CSV
    df, errs, warns = batch.check_batch(SAMPLE_CSV.read_bytes(), True)
    assert not errs and not warns and len(df) > 10_000
