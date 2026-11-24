# Assumptions and Decisions

Each entry: what was decided, and why.

1. **Python 3.11 installed with uv.** Only Python 3.12 and 3.13 were on the machine. `uv python install 3.11`
   adds a private 3.11 interpreter without touching the system Python. The venv is `.venv`.
2. **Package versions** are the latest releases available for Python 3.11 at build time, pinned exactly
   in requirements.txt (runtime) and requirements-dev.txt (development). The model is trained with the
   same scikit-learn version the app installs (1.9.1).
3. **`*.csv` is ignored globally except `data/sample.csv`**, on top of the required data/raw/ and
   data/processed/ entries, so a stray export can never be committed.
4. **Team slide ownership** (config/project.json, `slides`): Moaz Farag presents title, problem and data;
   Mohamed Rafat presents threat model and signals; Mohamed Mohy presents EDA; Mahmoud Ibrahim presents
   models and the accuracy trap; Mohamed Mahmoud presents results and evasion; Ali Mahmoud presents the app,
   the live demo, limits and next steps.
5. **Faculty name** on the cover is written as "Faculty of Computers and Artificial Intelligence". If the
   official name differs, edit `faculty` in config/project.json and run `python build_deliverables.py`.
