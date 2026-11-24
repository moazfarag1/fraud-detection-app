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
6. **Money columns are float64, not float32.** float32 keeps about 7 significant digits, so balances above
   ~100,000 lose their cents and the "do the balances add up?" checks in notebook 02 would be wrong. The
   whole file still fits in about 0.5 GB of memory. `type` is a category, `step` int16, flags int8.
7. **The calendar day (`step // 24`) is computed but not used by the models.** With a time-based split the
   test days never appear in training, so a tree model would turn "day" into a shortcut for "late in the
   month" (where the fraud rate is higher) instead of learning fraud. Hour of day is used.
8. **Receiver history counts every earlier incoming transaction of the account, of any type** (CASH_IN,
   PAYMENT to merchants, TRANSFER, ...), using only strictly earlier steps.
9. **Primary model is P, not R.** R reached validation PR-AUC 0.416 (above the 0.30 floor), but at 85% recall
   only 1.0% of its alerts were real fraud (117 alerts per 1,000 transactions). We defined "usable" in advance
   as at least 10% precision at 85% recall. P adds only balances known before the transaction. Its strength
   comes mostly from the PaySim pattern that fraud empties the whole sender balance, so its numbers are
   treated as an optimistic upper bound in all write-ups. L is never used in the app.
10. **Thresholds.** Block (t2) = lowest validation threshold with at least 90% precision. Review (t1) = the
    highest threshold that catches 95% of validation fraud. The brief asks for at least 85%; a review only
    costs a human check, and the extra workload on validation is small (2.6 alerts per 1,000 vs 1.3).
11. **Risk points.** The model score is close to 1 for most alerts (class weighting plus undersampling push
    scores up), so the app shows "risk points" from 0 to 100: a monotonic piecewise-linear rescaling where the
    Review line is 50 points and the Block line is 80 points. Verdicts are identical either way.
12. **Undersampling ratio** is 50 normal rows per fraud row in the training split only.
13. **Test-period fraud rate is 0.97%** (vs 0.13% overall) because normal traffic thins out after about
    step 400 while fraud continues. Precision and alerts per 1,000 on the test period are therefore higher
    than at a typical fraud rate; validation (0.13% fraud) shows 2.6 alerts per 1,000. A stratified random
    split is reported as a secondary check and gives the same ranking of models.
14. **Evasion test** uses 100 random test-period frauds that the model catches; "split the amount" counts
    as a success only when every piece is approved.
15. **Slide 10 team table uses 13 pt text** (the brief asks for body text of at least 18 pt). Six long role
    names do not fit in a table at 18 pt; all other body text is 18 pt or larger.
16. **The cited fact on slide 2** is the US Federal Trade Commission's March 2025 report of 12.5 billion US
    dollars lost to fraud in 2024. It is listed in the report references.
17. **LibreOffice is not installed**, so slides were rendered to PNG through the installed Microsoft PowerPoint
    (COM export) for visual inspection, plus a programmatic bounds check.
18. **Fonts**: Noto Sans (English) and Cairo (Arabic), both under the SIL Open Font License, downloaded once
    into assets/fonts and embedded with @font-face; nothing is loaded from a CDN at render time.
19. **Arabic report**: team names, roles, file names and technical terms stay in Latin script (as in
    config/project.json); numbers use Western digits.
20. **Notebook headers and findings** are filled by tools/stamp_notebooks.py from config/project.json and
    reports/findings/*.json, so `build_deliverables.py` updates them without re-executing anything.
