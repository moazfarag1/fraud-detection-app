"""Model loading and verdicts, used by the app and the notebooks."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.data import MODELS, SCORED_TYPES

VERDICTS = ["Approve", "Review", "Block"]
NOT_SCORED = "Low risk"


def load_meta(models_dir: Path = MODELS) -> dict:
    return json.loads((models_dir / "model_meta.json").read_text(encoding="utf-8"))


def load_model(models_dir: Path = MODELS):
    return joblib.load(models_dir / "model.joblib")


def verdict(score: float, t1: float, t2: float) -> str:
    if score >= t2:
        return "Block"
    if score >= t1:
        return "Review"
    return "Approve"


def score_frame(model, meta: dict, feats: pd.DataFrame, types: pd.Series) -> pd.DataFrame:
    """Score rows. Types other than TRANSFER / CASH_OUT are not scored (no fraud of that type in the data)."""
    t1, t2 = meta["thresholds"]["review"], meta["thresholds"]["block"]
    scored = types.astype(str).isin(SCORED_TYPES).to_numpy()
    risk = np.full(len(feats), np.nan)
    if scored.any():
        risk[scored] = model.predict_proba(feats.loc[scored, meta["features"]])[:, 1]
    out = pd.DataFrame(index=feats.index)
    out["risk_score"] = risk
    out["verdict"] = [verdict(r, t1, t2) if s else NOT_SCORED for r, s in zip(risk, scored)]
    return out
