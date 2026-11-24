"""English report content."""
from __future__ import annotations

from tools.deliverables.report import FIG, SCREENS, Doc, cover_html

REFERENCES = [
    "E. A. Lopez-Rojas, A. Elmir and S. Axelsson, \"PaySim: A financial mobile money simulator for fraud detection\", "
    "in Proc. 28th European Modeling and Simulation Symposium (EMSS), Larnaca, Cyprus, 2016.",
    "E. A. Lopez-Rojas, \"Synthetic Financial Datasets For Fraud Detection\" (PaySim), Kaggle dataset ealaxi/paysim1, "
    "https://www.kaggle.com/datasets/ealaxi/paysim1.",
    "US Federal Trade Commission, \"New FTC Data Show a Big Jump in Reported Losses to Fraud to $12.5 Billion in 2024\", "
    "press release, 10 March 2025.",
    "T. Saito and M. Rehmsmeier, \"The precision-recall plot is more informative than the ROC plot when evaluating "
    "binary classifiers on imbalanced datasets\", PLoS ONE 10(3): e0118432, 2015.",
    "F. Pedregosa et al., \"Scikit-learn: Machine Learning in Python\", Journal of Machine Learning Research 12, "
    "pp. 2825-2830, 2011.",
    "Streamlit documentation, https://docs.streamlit.io (used for the web application and its deployment).",
]


def build(cfg: dict, n: dict) -> tuple[Doc, str]:
    d = Doc("en")
    owner = {m["notebook"].split("/")[-1].split("_")[0]: m["name"] for m in cfg["team"]}

    d.add("Introduction and problem", f"""
<p>Mobile-money services and online banking let people move money in seconds. The same speed helps criminals:
once they take over an account, they can move the balance out before the customer notices. Losses are large;
the US Federal Trade Commission reports that consumers lost more than 12.5 billion US dollars to fraud in 2024 [3].</p>
<p>A bank must decide on every payment in real time. The difficulty is that fraud is <b>rare</b>: in our data only
{n['fraud_rate_pct']} of transactions are fraud (about one in {n['one_in']}). A useful system must catch most fraud
while sending as few honest payments as possible to manual review.</p>
<div class="box"><b>Project goal.</b> Build a fraud detector for money transfers that (1) is evaluated honestly on
data it has never seen, (2) explains its alerts in plain language, (3) is tested against simple attacker tricks,
and (4) is available as a web application.</div>
<p>This report follows the project pipeline. Each step is a Jupyter notebook owned by one team member (Section 11),
and every number in this report is produced by those notebooks.</p>
""")

    d.add("Threat model", f"""
<p>We describe the attack before choosing any feature, so that the features follow the attacker's behavior.</p>
{d.table(["Item", "Description"], [
        ["Attacker", "A criminal who gains control of a customer's account (stolen PIN, SIM swap, phishing or malware)."],
        ["Goal", "Move the victim's money out and turn it into cash before anyone reacts."],
        ["Assets", "The customer's balance and the bank's trust."],
        ["Limits", "The attacker cannot withdraw directly without being traced, so the money passes through other accounts."],
        ["What the attacker controls", "The amount, the time, and which receiving account is used."],
    ], caption="Threat model summary.")}
{d.fig(FIG / "00_attack_chain.png", "The attack chain as it appears in PaySim: account takeover, TRANSFER to a mule account, CASH_OUT.")}
<p><b>Why mule accounts matter.</b> A money mule is an account used only to receive stolen money and pass it on.
The bank cannot see the criminal, but it can see the <b>receiving account</b>: whether it is new, how much it
received before, and how recently. These questions become our receiver-history features (Section 6).</p>
""")

    d.add("Dataset", f"""
<p>We use <b>PaySim</b> [1, 2], a public simulator built by Lopez-Rojas, Elmir and Axelsson and calibrated on one
month of real transaction logs from a mobile-money service in an African country. Because it is simulated, it contains
no real customers, which makes it suitable for a course project.</p>
<div class="kpis">
 <div class="kpi"><div class="v">{n['rows_total']}</div><div class="l">transactions</div></div>
 <div class="kpi"><div class="v">{n['fraud_total']}</div><div class="l">fraud cases</div></div>
 <div class="kpi"><div class="v">{n['fraud_rate_pct']}</div><div class="l">fraud rate</div></div>
 <div class="kpi"><div class="v">743</div><div class="l">simulated hours (about 31 days)</div></div>
</div>
{d.table(["Column", "Meaning"], [
        ["step", "Hour of the simulation (1 to 743)"],
        ["type", "CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER"],
        ["amount", "Amount of money moved"],
        ["nameOrig / nameDest", "Sender / receiver account ID (C = customer, M = merchant)"],
        ["oldbalanceOrg / newbalanceOrig", "Sender balance before / after"],
        ["oldbalanceDest / newbalanceDest", "Receiver balance before / after"],
        ["isFraud", "1 if the transaction is fraud (the target)"],
        ["isFlaggedFraud", "1 if the simulator's simple rule flagged it"],
    ], caption="PaySim columns.")}
""")

    d.add("Data cleaning", f"""
<p><i>Notebook 01, owner: {owner['01']}.</i> The 470 MB file is read once with compact types (category for
<code>type</code>, small integers for <code>step</code> and the flags) and cached as a Parquet file for the
later notebooks. Money columns are kept as 64-bit numbers so that cents are not lost.</p>
<ul>
<li><b>Quality:</b> no missing values, no duplicated rows, and no negative amounts or balances.</li>
<li><b>Zero amounts:</b> 16 rows have an amount of 0, all of them fraud. They are kept.</li>
<li><b>Where fraud is:</b> fraud appears only in TRANSFER ({n['fraud_transfer']} cases) and CASH_OUT
({n['fraud_cashout']} cases). The other three types contain no fraud, so the models score only these two types
({n['rows_scored']} rows). All types are kept for computing receiver history.</li>
<li><b>Sample file:</b> a stratified sample of {n['sample_rows']} rows (with 300 fraud rows) is saved as
<code>data/sample.csv</code> for the app's batch demo.</li>
</ul>
{d.fig(FIG / "01_fraud_by_type.png", "Number of transactions per type; fraud appears only in TRANSFER and CASH_OUT.")}
""")

    d.add("Exploratory data analysis", f"""
<p><i>Notebook 02, owner: {owner['02']}.</i> Every statement below was measured, not assumed.</p>
<h3>5.1 Fraud is rare and larger</h3>
<p>The overall fraud rate is {n['fraud_rate_pct']}. Within TRANSFER and CASH_OUT the median fraud amount is
{n['median_ratio']} times the median normal amount, and {n['at_cap']} frauds sit exactly at 10,000,000, the largest
amount in a single fraud transaction (larger thefts are split into pieces of this size).</p>
{d.fig(FIG / "02_amounts.png", "Amount distribution of fraud and normal TRANSFER/CASH_OUT transactions (log scale).")}
<h3>5.2 Fraud does not sleep</h3>
<p>{n['night_fraud_pct']} of fraud happens between 00:00 and 05:59, against {n['night_normal_pct']} of normal traffic.
As a result the fraud rate at night is {n['night_rate_pct']}, compared with {n['day_rate_pct']} during the day.</p>
{d.fig(FIG / "02_fraud_by_hour.png", "Transactions per hour of day (bars) and fraud rate (line).")}
<h3>5.3 The fraud rate changes over the month</h3>
<p>Normal traffic thins out after about hour 400 while fraud continues at a steady pace, so the fraud rate rises from
{n['early_rate_pct']} (hours 1 to 400) to {n['late_rate_pct']} (hours 401 to 743). This matters for the time-based
test set in Section 7.</p>
{d.fig(FIG / "02_over_time.png", "Normal and fraud transactions per hour over the simulated month (log scale).")}
<h3>5.4 The simulator's rule and the account IDs</h3>
<p>The built-in rule <code>isFlaggedFraud</code> flags only {n['flagged_rows']} rows and catches {n['flag_recall_all_pct']}
of fraud. Senders almost never repeat ({n['unique_senders']} unique senders), while receivers repeat often
({n['unique_receivers']} unique receivers), which makes receiver history possible.</p>
<h3>5.5 A warning about the balance columns</h3>
<p>The dataset author notes that fraudulent transactions were cancelled in the simulation. We measured the effect:
{n['empties_fraud_pct']} of frauds move exactly the whole sender balance (normal: {n['empties_normal_pct']}), and for
{n['dest_zero_fraud_pct']} of frauds the receiver balance is 0 both before and after the transfer (normal:
{n['dest_zero_normal_pct']}). Some of this is real behavior (criminals empty accounts), but some is an artifact of the
simulator. Balance columns therefore separate the classes far too cleanly to trust blindly.</p>
{d.fig(FIG / "02_balance_artifact.png", "Balance checks for fraud and normal TRANSFER/CASH_OUT rows.")}
""")

    d.add("Feature engineering", f"""
<p><i>Notebook 03, owner: {owner['03']}.</i> All feature code is in <code>src/features.py</code> and is shared by
training and the app, so a transaction typed into the app is processed exactly like the training data.
The model never sees <code>isFraud</code> (the answer), <code>isFlaggedFraud</code> (kept only as a baseline) or the
raw account IDs.</p>
{d.table(["Group", "Features", "Known when?"], [
        ["Basic", "type (TRANSFER or CASH_OUT), amount, log of amount, hour of day, round amount, amount near the 10,000,000 maximum", "Before the payment"],
        ["Receiver history", "transfers received before, total received before, new receiver flag, hours since the last incoming transfer", "Before the payment"],
        ["Pre-transaction balances", "sender balance before, receiver balance before, amount divided by sender balance", "Before the payment"],
        ["Post-transaction balances", "sender and receiver balance after, balance errors", "Only after the payment (leaky)"],
    ], caption="Feature groups.")}
<p><b>No future leakage.</b> Receiver history counts only transactions from <b>strictly earlier hours</b>; transactions
in the same hour and later ones are never used. We proved it on the real data: recomputing the features using only the
first {n['leak_hours']} hours gave identical values for all {n['leak_rows']} rows in that period. The calendar day is not
used, because with a time-based split it would act as a shortcut for "late in the month".</p>
<p><b>The mule signal.</b> {n['new_recv_fraud_pct']} of frauds go to a brand-new receiver, against
{n['new_recv_normal_pct']} of normal transfers; a transfer to a new receiver is {n['new_recv_lift']} times more likely
to be fraud.</p>
{d.fig(FIG / "03_new_receiver.png", "Share of transfers sent to a brand-new receiver, and fraud rate by receiver type.")}
""")

    d.add("Models and training", f"""
<p><i>Notebook 04a, owner: {owner['04a']}.</i> All three models use the same algorithm, a gradient-boosted decision
tree (<code>HistGradientBoostingClassifier</code> from scikit-learn [5]) with balanced class weights. They differ only
in the information they receive:</p>
{d.table(["Model", "Features", "Purpose"], [
        ["R (Realistic)", f"Basic + receiver history ({n['n_feat_R']} features)", "Most cautious estimate, no balances at all"],
        ["P (Pre-transaction)", f"R + pre-transaction balances ({n['n_feat_P']} features)", "What a bank knows when it approves a payment"],
        ["L (Leaky)", f"Everything ({n['n_feat_L']} features)", "Shows why published 99.9% results on PaySim mislead; never used in the app"],
        ["Logistic Regression", "R features", "Simple baseline"],
        ["isFlaggedFraud", "Simulator rule", "Baseline"],
    ], caption="Models and baselines.")}
<h3>7.1 Time-based split</h3>
<p>A bank trains on the past and is used on the future, so we split by time: training on hours {n['train_steps']}
({n['train_rows']} rows, fraud rate {n['train_rate_pct']}), validation on hours {n['val_steps']} (fraud rate
{n['val_rate_pct']}) and test on hours {n['test_steps']} ({n['test_rows']} rows, fraud rate {n['test_rate_pct']}).
The test period has more fraud because normal traffic thins out late in the month (Section 5.3). As a secondary
check, a stratified random split gives the same ranking of models (test PR-AUC: R {n['rand_pr_auc_R']}, P
{n['rand_pr_auc_P']}).</p>
<p>For training only, normal rows are undersampled to {n['undersample']} per fraud row. Validation and test data keep
their real fraud rate.</p>
{d.fig(FIG / "04a_pr_curves_validation.png", "Precision-recall curves on the validation period.")}
<h3>7.2 Choosing the model for the app</h3>
<p>The rule was fixed before looking at the test set: use R if its validation PR-AUC is at least 0.30 and at least
10% of its alerts are real fraud when it catches 85% of fraud; otherwise use P; never use L. R reached a PR-AUC of
{n['val_pr_auc_R']}, but at 85% recall only {n['val_prec85_R_pct']} of its alerts were real fraud
({n['val_alerts85_R']} alerts per 1,000 transactions). That is not workable for a bank, so <b>the app uses model P</b>
(validation PR-AUC {n['val_pr_auc_P']}).</p>
<h3>7.3 Approve, Review, Block</h3>
<p>Two thresholds are chosen on validation. <b>Block</b> starts at the lowest score where at least 90% of validation
alerts are real fraud (score {n['thr_block']}). <b>Review</b> starts at the highest score that still catches 95% of
validation fraud (score {n['thr_review']}); the brief asked for at least 85%, and the extra review workload is small.
On validation this catches {n['val_rb_recall_pct']} of fraud at Review or Block with {n['val_rb_precision_pct']}
precision and {n['val_alerts']} alerts per 1,000 transactions. The app shows the score as 0 to 100 risk points, where
50 is the Review line and 80 the Block line.</p>
""")

    comp_rows = [
        ["isFlaggedFraud rule", "-", n["rule_recall_pct"], "-"],
        ["Logistic Regression", n["pr_auc_LR"], "-", "-"],
        ["R (Realistic)", n["pr_auc_R"], n["recall_R_pct"], n["prec_R_pct"]],
        ["P (Pre-transaction), used in the app", n["pr_auc_P"], n["recall_pct"], n["precision_pct"]],
        ["L (Leaky), not real", n["pr_auc_L"], "-", "-"],
    ]
    d.add("Evaluation results", f"""
<p><i>Notebook 04b, owner: {owner['04b']}.</i> All results are on the test period (hours {n['test_steps']}), which no
model saw during training or threshold selection.</p>
<h3>8.1 The accuracy trap</h3>
<div class="box">A "model" that always answers <b>not fraud</b> is {n['never_acc_all_pct']} accurate on the whole
dataset and {n['never_acc_test_pct']} accurate on the test period, yet it catches no fraud at all. Accuracy is
therefore meaningless here; we report precision, recall and PR-AUC, which is the more informative measure for rare
events [4].</div>
<h3>8.2 The primary model (P)</h3>
<div class="kpis">
 <div class="kpi"><div class="v">{n['recall_pct']}</div><div class="l">of fraud caught (Review or Block)</div></div>
 <div class="kpi"><div class="v">{n['precision_pct']}</div><div class="l">of alerts are real fraud</div></div>
 <div class="kpi"><div class="v">{n['alerts_per_1000']}</div><div class="l">alerts per 1,000 transactions</div></div>
 <div class="kpi"><div class="v">{n['pr_auc']}</div><div class="l">PR-AUC</div></div>
</div>
<p>In plain words: the model catches about <b>{n['per_100']} of every 100</b> fraud transfers in the test period.
It blocks {n['block_recall_pct']} of fraud directly with {n['block_precision_pct']} precision, sends the rest of its
alerts to review, and misses {n['missed']} of {n['test_fraud']} frauds. The test period has an unusually high fraud
rate ({n['test_rate_pct']}), so precision and alerts per 1,000 are higher than at a typical rate; on validation
(normal fraud rate) the same thresholds give {n['val_alerts']} alerts per 1,000.</p>
{d.fig(FIG / "04b_confusion_matrix.png", "Decisions of model P on the test period.")}
<h3>8.3 R vs P vs L</h3>
{d.table(["Model", "PR-AUC", "Recall", "Precision"], comp_rows, num_cols=(1, 2, 3),
         caption="Test-period results. Recall and precision for R use the threshold that caught 85% of validation fraud; for P they use the app's Review line.")}
{d.fig(FIG / "04b_model_comparison.png", "PR-AUC, precision and recall on the test period (all models at their 85%-validation-recall threshold).")}
<ul>
<li><b>L</b> is almost perfect (PR-AUC {n['pr_auc_L']}) only because it reads balances after the transaction, which the
simulator distorts for fraud. This is the leak behind many "99.9%" results on PaySim.</li>
<li><b>P</b> (PR-AUC {n['pr_auc_P']}) uses only information known before approval. Its strength comes mainly from one
pattern: in PaySim a fraudster almost always moves the whole balance. Real fraud is less regular, so P's numbers are
an optimistic upper bound.</li>
<li><b>R</b> (PR-AUC {n['pr_auc_R']}) uses no balances. It ranks fraud far better than chance and than the
Logistic Regression baseline ({n['pr_auc_LR']}), but it would raise too many alerts on its own.</li>
</ul>
<h3>8.4 What the model relies on</h3>
<p>Permutation importance (how much PR-AUC drops when one feature is shuffled) shows that model P relies mostly on
{', '.join(x.lower() for x in n['top_features'])}.</p>
{d.fig(FIG / "04b_feature_importance.png", "Permutation importance of the top features of model P.")}
""")

    d.add("Explanations and evasion test", f"""
<h3>9.1 Warning signs</h3>
<p><code>src/explain.py</code> turns the features into short warning signs, for example "Money goes to a brand-new
receiver account", "Unusual hour (night)" or "The transaction empties the whole balance of the sender". The app shows
them under the title <b>Warning signs found</b>. They are simple rules that help a person review a case; they are
<b>not</b> the model's exact reasoning.</p>
<h3>9.2 Evasion test</h3>
<p>We took 100 test-period frauds that the model catches and changed one thing at a time, as an attacker would.</p>
{d.table(["Attacker trick", "Frauds that slip through to Approve"], [
        ["Split the amount into 3 to 5 smaller transfers (all pieces must pass)", n["ev_split_pct"]],
        ["Use a receiver with normal history instead of a new account", n["ev_hist_pct"]],
        ["Move the transfer to a daytime hour (14:00)", n["ev_day_pct"]],
        ["Use a round amount (rounded down to 1,000)", n["ev_round_pct"]],
    ], num_cols=(1,), caption="Evasion test on 100 caught frauds.")}
{d.fig(FIG / "04b_evasion.png", "Share of caught frauds that drop to Approve after one attacker trick.")}
<div class="box warn"><b>Finding.</b> Tricks that remove the pattern the model depends on work best: if the attacker
does not empty the account in one transfer, most frauds slip through. Changing only the hour or rounding the amount
barely helps. A real system should also look at several transactions of the same account together.</div>
""")

    d.add("The application", f"""
<p><i>Notebook 05, owner: {owner['05']}.</i> The web app is a single Streamlit file (<code>app.py</code>) that reuses
<code>src/</code>. It reads only files in the repository and makes no network calls. It is deployed on Streamlit
Community Cloud from the project's GitHub repository.</p>
{f'<div class="box"><b>Live app:</b> {cfg["app_url"]}</div>' if cfg.get("app_url") else ""}
<ul>
<li><b>Check a transaction:</b> enter a transaction or click one of six synthetic examples; the app shows Approve,
Review or Block in color and text, a risk gauge, and the warning signs.</li>
<li><b>Batch check:</b> upload a CSV in PaySim format (up to 20,000 rows). Receiver history is computed within the
uploaded file. On the sample file ({n['sample_rows']} rows) {n['sample_flagged_pct']} of the labeled fraud rows go to
Review or Block, with {n['sample_false_alarms']} normal rows flagged.</li>
<li><b>Dashboard:</b> test results, the accuracy trap, model comparison, top signals and the evasion test.</li>
<li><b>About:</b> how it works, caveats and the team.</li>
</ul>
<p>Two of the six examples are shown honestly as <b>known limitations</b>: a busy mule account that still has money
in it, and a fraud split into smaller pieces. The model approves both.</p>
{d.fig(SCREENS / "01_check_block.png", "Check a transaction: a night transfer of the whole balance to a new account is blocked.", "screen")}
{d.fig(SCREENS / "05_dashboard.png", "Dashboard tab with the honest test results.", "screen")}
{d.fig(SCREENS / "04_batch.png", "Batch check on the sample file.", "screen")}
""")

    d.add("Team contributions", d.table(
        ["Member", "Role", "Notebook"],
        [[m["name"], m["role"], f"<code>{m['notebook']}</code>"] for m in cfg["team"]],
        caption="Each notebook is owned and presented by one member."))

    d.add("Conclusion and future work", f"""
<p>We built a complete, honest fraud detection pipeline on PaySim: clean data, measured insights, a threat model,
leakage-free features, three models compared fairly, an evasion test, and a working web application.</p>
<ul>
<li>The headline "99.9%" results on PaySim come from leaked balance information (model L). Without it, results drop
sharply (model R, PR-AUC {n['pr_auc_R']}).</li>
<li>Using only what a bank knows at approval time (model P), the system catches {n['per_100']} of every 100 fraud
transfers in the test period with {n['alerts_per_1000']} alerts per 1,000 transactions.</li>
<li>A careful attacker can evade it by splitting the amount ({n['ev_split_pct']} slip through).</li>
</ul>
<p><b>Future work:</b> features that follow several transactions of the same account over time (velocity and
splitting patterns), probability calibration, testing on real anonymized bank data, and monitoring how fraud
behavior changes after deployment.</p>
""")

    d.add("References", "<ol class='refs'>" + "".join(f"<li>{r}</li>" for r in REFERENCES) + "</ol>")

    cover = cover_html(cfg, "Course project report", "Detecting fraudulent money transfers with machine learning, honestly evaluated",
                       {"course": "Course", "university": "University", "team": "Team", "date": "Date"},
                       "All data is simulated (PaySim). No real customers or accounts are involved. Educational use only.")
    return d, cover
