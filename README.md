# Financial Transaction Fraud Detector

Course project for **AI in Cybersecurity**, Sohag University (Computer Science (AI & Data Science track)).

A machine-learning system that flags suspicious money transfers (TRANSFER and CASH_OUT) in a mobile-money service,
evaluated honestly on data it never saw, explained in plain English, tested against simple attacker tricks, and
deployed as a Streamlit web app.

Live app: https://transaction-fraud-detector-sohag.streamlit.app/

## Results in one minute

| | |
|---|---|
| Model used in the app | P (Pre-transaction): gradient-boosted trees on transaction, receiver-history and pre-transaction balance features |
| Fraud caught (test period, Review or Block) | 93.6% |
| Alerts that are real fraud (precision) | 87.8% |
| Alerts per 1,000 transactions | 10.3 (test period has a 0.97% fraud rate; 2.6 on validation) |
| PR-AUC | 0.979 |
| Test PR-AUC by model | R (no balances) 0.561, P 0.979, L (leaky, not real) 1.000 |
| Evasion | splitting the amount lets 91% of caught frauds through |

Always answering "not fraud" is 99.87% accurate and catches nothing, so accuracy is not reported
as a success measure. All data is simulated (PaySim); no real people or accounts are involved.

## Team

| Member | Role | Notebook |
|---|---|---|
| Moaz Farag | Data Collection & Cleaning, project coordination | `notebooks/01_data_cleaning.ipynb` |
| Mohamed Mohy | Exploratory Data Analysis (EDA) | `notebooks/02_eda.ipynb` |
| Mohamed Rafat | Feature Engineering & Threat Model | `notebooks/03_feature_engineering.ipynb` |
| Mahmoud Ibrahim | Model Training (models R/P/L, baselines, thresholds) | `notebooks/04a_model_training.ipynb` |
| Mohamed Mahmoud | Model Evaluation & Evasion Testing | `notebooks/04b_evaluation_and_evasion.ipynb` |
| Ali Mahmoud | Deployment & Web Application | `notebooks/05_deployment.ipynb` |

## Data

PaySim (Lopez-Rojas, Elmir and Axelsson, EMSS 2016), Kaggle dataset `ealaxi/paysim1`. The raw CSV (about 470 MB) is
**not** in this repository. To rebuild everything, download it and place it at:

```
data/raw/PS_20174392719_1491204439457_log.csv
```

For example: `pip install kagglehub` then
`python -c "import kagglehub; print(kagglehub.dataset_download('ealaxi/paysim1'))"` and copy the CSV into `data/raw/`.
The app itself does **not** need the raw data.

## Run the app on Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

(Python 3.11. If `py -3.11` is not available, `uv python install 3.11` installs it.)

## Run the notebooks (full pipeline)

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m ipykernel install --user --name fraud-detection --display-name "Python 3.11 (fraud-detection)"
.venv\Scripts\python tools\run_notebooks.py
```

The notebooks run in order and each reads the previous one's outputs:
`01_data_cleaning` -> `02_eda` -> `03_feature_engineering` -> `04a_model_training` -> `04b_evaluation_and_evasion` -> `05_deployment`.
Retraining the model = running `04a` (and then `04b` and `05` to refresh the results). `tools\run_notebooks.py 04a 04b 05`
runs only those.

## Regenerate the deliverables

```powershell
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python tools\screenshot_app.py
.venv\Scripts\python build_deliverables.py
.venv\Scripts\python check_consistency.py
```

This rebuilds the slides, both PDF reports, the demo script, this README and the notebook header and findings cells
from `config/project.json` and `reports/*.json`, without retraining or re-executing notebooks.

## Change team names or roles

Edit `config/project.json` (names, roles, notebooks, the slides each person presents, the date, and `app_url` once the
app is deployed), then run `python build_deliverables.py`.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```

Unit tests for the features (zero and huge amounts, new receivers, missing history, no future leakage), batch-file
validation, and an AppTest smoke test that clicks every example and runs the batch check.

## Project structure

```
app.py                  Streamlit app (no network calls, reads only repository files)
src/                    shared code: data, features, train, scoring, explain, evasion, batch, presets, plotstyle
notebooks/              the six team notebooks
models/                 model.joblib (primary model) and model_meta.json
reports/                data_facts, metrics, feature_importance, evasion JSON; figures/; screens/;
                        Report_EN.pdf, Report_AR.pdf, Demo_Script.md
slides/                 Fraud_Detector.pptx
config/project.json     project and team information (single source of truth)
data/sample.csv         small PaySim-format sample (batch demo and upload template)
tools/                  run_notebooks, stamp_notebooks, screenshot_app, deliverable builders
tests/                  pytest tests
build_deliverables.py   rebuilds all deliverables
check_consistency.py    checks that slides and reports quote the numbers in reports/metrics.json
```

## Limitations

- PaySim is simulated. In PaySim a fraudster almost always moves the whole balance (98% of fraud),
  which makes model P look better than it would on real data; model R (0.561) is the cautious estimate.
- Balance columns after the transaction are distorted for fraud by the simulator, so they are never used by the app.
- The model can be evaded by splitting the amount; it does not look at several transactions of one account together.
- The batch check computes receiver history only within the uploaded file.
- Educational project, not a production banking system.
