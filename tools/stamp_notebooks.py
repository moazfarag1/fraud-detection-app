"""Write the header cell and the "Key findings" cell of every team notebook.

- Header: from config/project.json (project, owner, role, course, university) plus the notebook's
  goal, inputs and outputs below.
- Key findings: from reports/findings/<notebook>.json, written by the notebook's last code cell.

Only these two markdown cells change; code cells and their outputs are left untouched,
so this runs in a second and never re-executes or retrains anything.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]

NOTEBOOK_INFO = {
    "01_data_cleaning": {
        "title": "01 - Data Collection & Cleaning",
        "goal": "Load the PaySim data efficiently, check its quality, decide what to keep, and save a clean copy plus a small sample for the app.",
        "inputs": ["data/raw/PS_20174392719_1491204439457_log.csv (Kaggle ealaxi/paysim1)"],
        "outputs": ["data/processed/clean.parquet", "data/sample.csv", "reports/figures/01_*.png"],
    },
    "02_eda": {
        "title": "02 - Exploratory Data Analysis (EDA)",
        "goal": "Measure and visualize how fraud behaves in the data: how rare it is, when it happens, how large it is, and which columns can be trusted.",
        "inputs": ["data/processed/clean.parquet"],
        "outputs": ["reports/data_facts.json", "reports/figures/02_*.png"],
    },
    "03_feature_engineering": {
        "title": "03 - Feature Engineering & Threat Model",
        "goal": "Describe how attackers operate and turn that into features the model can use, including receiver history computed without looking into the future.",
        "inputs": ["data/processed/clean.parquet", "src/features.py"],
        "outputs": ["data/processed/features.parquet", "reports/figures/03_*.png"],
    },
    "04a_model_training": {
        "title": "04a - Model Training",
        "goal": "Train three models (R, P, L) and two baselines with a time-based split, choose the model for the app, and set its Approve / Review / Block thresholds.",
        "inputs": ["data/processed/features.parquet", "src/train.py"],
        "outputs": ["models/model.joblib", "models/model_meta.json", "reports/validation.json", "reports/figures/04a_*.png"],
    },
    "04b_evaluation_and_evasion": {
        "title": "04b - Model Evaluation & Evasion Testing",
        "goal": "Measure every model honestly on unseen test data, explain the accuracy trap, find which signals matter, and test whether simple attacker tricks fool the model.",
        "inputs": ["data/processed/features.parquet", "models/", "reports/validation.json"],
        "outputs": ["reports/metrics.json", "reports/feature_importance.json", "reports/evasion.json", "reports/figures/04b_*.png"],
    },
    "05_deployment": {
        "title": "05 - Deployment & Web Application",
        "goal": "Show how the Streamlit app is built, run its six example transactions and the batch check, and explain how it is deployed to Streamlit Community Cloud.",
        "inputs": ["models/model.joblib", "models/model_meta.json", "data/sample.csv", "app.py"],
        "outputs": ["reports/app_presets.json", "reports/screens/*.png"],
    },
}


def header_markdown(cfg: dict, member: dict, stem: str) -> str:
    info = NOTEBOOK_INFO[stem]
    lines = [
        f"# {cfg['project_name']}",
        f"## Notebook {info['title']}",
        "",
        f"**Owner:** {member['name']}  ",
        f"**Role:** {member['role']}  ",
        f"**Course / University:** {cfg['course']}, {cfg['university']}  ",
        f"**Date:** {cfg['date']}",
        "",
        f"**Goal.** {info['goal']}",
        "",
        "**Inputs:** " + ", ".join(f"`{x}`" for x in info["inputs"]),
        "",
        "**Outputs:** " + ", ".join(f"`{x}`" for x in info["outputs"]),
        "",
        "Run the notebooks in order 01, 02, 03, 04a, 04b, 05; each one reads the files saved by the previous one.",
    ]
    return "\n".join(lines)


def findings_markdown(stem: str) -> str | None:
    path = ROOT / "reports" / "findings" / f"{stem}.json"
    if not path.exists():
        return None
    bullets = json.loads(path.read_text(encoding="utf-8"))["findings"]
    return "## Key findings\n\n" + "\n".join(f"- {b}" for b in bullets)


def stamp(verbose: bool = True) -> None:
    cfg = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
    for member in cfg["team"]:
        path = ROOT / member["notebook"]
        stem = path.stem
        if not path.exists():
            if verbose:
                print(f"skip (missing): {path.name}")
            continue
        nb = nbformat.read(path, as_version=4)
        for cell in nb.cells:
            tags = cell.get("metadata", {}).get("tags", [])
            if "header" in tags:
                cell.source = header_markdown(cfg, member, stem)
            elif "findings" in tags:
                text = findings_markdown(stem)
                if text:
                    cell.source = text
        nbformat.write(nb, path)
        if verbose:
            print(f"stamped {path.name} (owner: {member['name']})")


if __name__ == "__main__":
    stamp(verbose="-q" not in sys.argv)
