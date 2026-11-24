"""Data loading helpers shared by the notebooks and the app.

All paths are built with pathlib from the project root, so the space in
"D:\\project\\fraud detection" never causes problems.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "PS_20174392719_1491204439457_log.csv"
PROCESSED = ROOT / "data" / "processed"
CLEAN_PARQUET = PROCESSED / "clean.parquet"
FEATURES_PARQUET = PROCESSED / "features.parquet"
SAMPLE_CSV = ROOT / "data" / "sample.csv"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
CONFIG = ROOT / "config" / "project.json"

PAYSIM_COLUMNS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig",
    "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud", "isFlaggedFraud",
]

# Compact dtypes. Money columns stay float64 on purpose: float32 keeps only about
# 7 significant digits, which loses cents on balances above ~100,000 and would make
# the "do the balances add up?" checks unreliable (see ASSUMPTIONS.md).
RAW_DTYPES = {
    "step": "int16",
    "type": "category",
    "amount": "float64",
    "nameOrig": "string",
    "oldbalanceOrg": "float64",
    "newbalanceOrig": "float64",
    "nameDest": "string",
    "oldbalanceDest": "float64",
    "newbalanceDest": "float64",
    "isFraud": "int8",
    "isFlaggedFraud": "int8",
}

TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
SCORED_TYPES = ["TRANSFER", "CASH_OUT"]


def load_raw(path: Path = RAW_CSV) -> pd.DataFrame:
    """Read the original PaySim CSV once, with compact column types."""
    return pd.read_csv(path, usecols=PAYSIM_COLUMNS, dtype=RAW_DTYPES)


def load_clean() -> pd.DataFrame:
    return pd.read_parquet(CLEAN_PARQUET)


def load_features() -> pd.DataFrame:
    return pd.read_parquet(FEATURES_PARQUET)


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_findings(notebook_stem: str, bullets: list[str]) -> None:
    """Save a notebook's key findings; tools/stamp_notebooks.py copies them into its last markdown cell."""
    write_json({"notebook": notebook_stem, "findings": bullets}, REPORTS / "findings" / f"{notebook_stem}.json")


def find_root(start: Path | None = None) -> Path:
    """Project root = the folder that contains config/project.json."""
    p = (start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "config" / "project.json").exists():
            return cand
    return ROOT
