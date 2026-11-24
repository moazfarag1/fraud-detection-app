# Project Plan: Financial Transaction Fraud Detector

Priority if time runs short: (1) correct model + working app on GitHub, (2) six notebooks executed,
(3) slides, (4) English PDF report, (5) Arabic PDF report, (6) demo script.

## Phase 1: Setup
- [x] Folder structure, .gitignore, raw CSV moved to data/raw/ (ignored)
- [x] Python 3.11 venv, requirements.txt (runtime, pinned) and requirements-dev.txt
- [x] Jupyter kernel registered
- [x] config/project.json with team and roles
- [x] git init, first commit (no CSV/parquet staged)
- Gate: imports succeed, versions printed, git status clean of data files

## Phase 2: Notebook 01 - Data Collection & Cleaning (Moaz Farag)
- [x] Load CSV once with compact dtypes, cache to data/processed/clean.parquet
- [x] Quality checks: types, missing, duplicates, amounts, categories
- [x] Verify fraud only in TRANSFER and CASH_OUT
- [x] Stratified sample to data/sample.csv (<= 2 MB)
- Gate: notebook executes, outputs saved

## Phase 3: Notebook 02 - EDA (Mohamed Mohy)
- [x] Fraud rate overall and per type, amounts, hour, step
- [x] isFlaggedFraud coverage, ID repetition, merchant prefix
- [x] Balance-column artifact measured
- [x] reports/data_facts.json
- Gate: notebook executes, data_facts.json written

## Phase 4: Notebook 03 - Feature Engineering & Threat Model (Mohamed Rafat)
- [x] Threat model
- [x] src/features.py: basic, receiver history (strictly earlier steps), pre-balance, post-balance
- [x] Leakage worked example
- [x] data/processed/features.parquet
- Gate: notebook executes, leakage example shown, features saved

## Phase 5: Notebook 04a - Model Training (Mahmoud Ibrahim)
- [x] Time-based split, fraud rate per split
- [x] Models R, P, L (HistGradientBoosting) + Logistic Regression baseline + isFlaggedFraud rule
- [x] Thresholds on validation (recall >= 0.85 at Review or Block)
- [x] models/model.joblib, models/model_meta.json, reports/validation.json
- Gate: notebook executes, model reloads in a fresh process

## Phase 6: Notebook 04b - Evaluation & Evasion (Mohamed Mahmoud)
- [x] Test metrics for all models and baselines, accuracy trap
- [x] Permutation importance
- [x] Warning signs (src/explain.py)
- [x] Evasion test (4 tricks)
- [x] reports/metrics.json, feature_importance.json, evasion.json
- Gate: notebook executes, JSON written, numbers sensible

## Phase 7: App + Notebook 05 - Deployment (Ali Mahmoud)
- [x] app.py: Check, Batch, Dashboard, About tabs; 6 presets
- [x] Tests: features unit tests, AppTest smoke test
- [x] Screenshots of every tab (Playwright)
- [x] Notebook 05
- [x] tools/run_notebooks.py runs all 6 notebooks
- Gate: pytest passes, app starts, screenshots inspected, all notebooks execute

## Phase 8: Deliverables
- [x] slides/Fraud_Detector.pptx
- [x] reports/Report_EN.pdf
- [x] reports/Report_AR.pdf
- [x] reports/Demo_Script.md
- [x] README.md
- [x] check_consistency.py passes
- Gate: consistency check passes, page images inspected

## Phase 9: Git and deployment prep
- [ ] Size / secrets audit
- [ ] Private GitHub repo created and pushed
- [ ] Clean-install test with only requirements.txt
- [ ] Streamlit Cloud checklist

## Phase 10: Final self-review
- [ ] Names, roles, typos, no emojis, consistent numbers, presets behave as described
