"""Training helpers used by notebook 04a (split, undersampling, models, thresholds, metrics)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score, precision_recall_curve,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42


def time_split(df: pd.DataFrame, train_frac: float = 0.70, val_frac: float = 0.15):
    """Split by time (step). Returns the two step cut-offs: train < s1 <= val < s2 <= test."""
    steps = df["step"].sort_values(kind="stable").to_numpy()
    s1 = int(steps[int(len(steps) * train_frac)])
    s2 = int(steps[int(len(steps) * (train_frac + val_frac))])
    return s1, s2


def apply_split(df: pd.DataFrame, s1: int, s2: int):
    train = df[df["step"] < s1]
    val = df[(df["step"] >= s1) & (df["step"] < s2)]
    test = df[df["step"] >= s2]
    return train, val, test


def undersample(train: pd.DataFrame, ratio: int = 50, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Keep every fraud row and `ratio` normal rows per fraud row. Used on TRAINING data only."""
    pos = train[train["isFraud"] == 1]
    neg = train[train["isFraud"] == 0]
    neg = neg.sample(n=min(len(neg), ratio * len(pos)), random_state=seed)
    return pd.concat([pos, neg]).sample(frac=1.0, random_state=seed)


def make_hgb(columns: list[str]) -> Pipeline:
    """Pipeline = pick the model's columns, then gradient-boosted trees."""
    return Pipeline([
        ("select", ColumnTransformer([("keep", "passthrough", columns)], remainder="drop")),
        ("clf", HistGradientBoostingClassifier(
            class_weight="balanced", max_iter=300, learning_rate=0.1,
            random_state=RANDOM_STATE)),
    ])


def make_logreg(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("select", ColumnTransformer([("keep", "passthrough", columns)], remainder="drop")),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=2000)),
    ])


def threshold_for_recall(y, p, target_recall: float = 0.85) -> float:
    """Highest threshold whose recall is still >= target_recall."""
    prec, rec, thr = precision_recall_curve(y, p)
    ok = np.where(rec[:-1] >= target_recall)[0]
    return float(thr[ok[-1]]) if len(ok) else float(thr[0])


def threshold_for_precision(y, p, target_precision: float = 0.90):
    """Lowest threshold whose precision is >= target_precision (keeps as much recall as possible)."""
    prec, rec, thr = precision_recall_curve(y, p)
    ok = np.where(prec[:-1] >= target_precision)[0]
    return float(thr[ok[0]]) if len(ok) else None


def binary_metrics(y, flagged) -> dict:
    y = np.asarray(y).astype(int)
    flagged = np.asarray(flagged).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, flagged, labels=[0, 1]).ravel()
    return {
        "precision": float(precision_score(y, flagged, zero_division=0)),
        "recall": float(recall_score(y, flagged, zero_division=0)),
        "f1": float(f1_score(y, flagged, zero_division=0)),
        "accuracy": float((tp + tn) / len(y)),
        "alerts_per_1000": float(1000 * flagged.mean()),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def score_metrics(y, p) -> dict:
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
    }
