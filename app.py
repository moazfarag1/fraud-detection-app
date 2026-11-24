"""Financial Transaction Fraud Detector - Streamlit app.

Runs fully offline: it reads only files inside this repository (models/, reports/, config/, data/sample.csv)
and makes no network calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sklearn
import streamlit as st

from src import batch, explain, features, scoring
from src.data import SCORED_TYPES, TYPES
from src.presets import PRESETS, RECEIVER_PROFILES

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
MAX_BATCH_ROWS = 20_000  # same limit as src/batch.py

COLORS = {
    "Approve": "#2A9D8F",
    "Review": "#E9A23B",
    "Block": "#C0392B",
    "Low risk": "#8A94A6",
    "navy": "#1F4E79",
    "ink": "#1B2430",
    "grey": "#8A94A6",
}
VERDICT_TEXT = {
    "Approve": "Looks normal. The payment can go through.",
    "Review": "Suspicious. Hold the payment until a person checks it.",
    "Block": "High risk. Stop the payment and contact the customer.",
    "Low risk": "Low risk: no fraud of this type was observed in the data.",
}

st.set_page_config(page_title="Fraud Detector", page_icon=None, layout="wide")

st.markdown(
    """
<style>
header[data-testid="stHeader"] {display: none;}
.block-container {padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1250px;}
.app-header {background: linear-gradient(90deg, #12324F 0%, #1F4E79 100%); color: #FFFFFF;
  padding: 18px 26px; border-radius: 10px; margin-bottom: 14px;}
.app-header h1 {color: #FFFFFF; font-size: 1.7rem; margin: 0; padding: 0; font-weight: 700; letter-spacing: 0.2px;}
.app-header p {color: #C9D8E8; margin: 4px 0 0 0; font-size: 0.95rem;}
.card {background: #FFFFFF; border: 1px solid #DCE3EB; border-radius: 10px; padding: 16px 18px; min-height: 128px;}
.card .label {color: #5B6878; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.6px;}
.card .value {color: #1B2430; font-size: 1.75rem; font-weight: 700; margin-top: 2px;}
.card .sub {color: #5B6878; font-size: 0.85rem;}
.verdict {border-radius: 10px; padding: 16px 20px; color: #FFFFFF; margin-bottom: 10px;}
.verdict .big {font-size: 2.0rem; font-weight: 800; letter-spacing: 1px;}
.verdict .small {font-size: 0.98rem; opacity: 0.95;}
.sign {background: #FFF6E8; border-left: 4px solid #E9A23B; padding: 8px 12px; margin: 6px 0; border-radius: 4px; color: #1B2430;}
.nosign {background: #EAF6F4; border-left: 4px solid #2A9D8F; padding: 8px 12px; margin: 6px 0; border-radius: 4px; color: #1B2430;}
.note {background: #EEF3F8; border-left: 4px solid #1F4E79; padding: 10px 14px; border-radius: 4px; color: #1B2430; font-size: 0.93rem;}
.limit {background: #FDECEA; border-left: 4px solid #C0392B; padding: 10px 14px; border-radius: 4px; color: #1B2430; font-size: 0.93rem;}
table.team {width: 100%; border-collapse: collapse; font-size: 0.9rem; background: #FFFFFF;}
table.team th {background: #1F4E79; color: #FFFFFF; text-align: left; padding: 7px 9px;}
table.team td {border-bottom: 1px solid #DCE3EB; padding: 7px 9px; vertical-align: top; color: #1B2430;}
table.team code {font-size: 0.78rem; color: #1F4E79; background: #EEF3F8;}
div[data-testid="stTabs"] button p {font-size: 1.02rem; font-weight: 600;}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------------------------
# Loading (cached)
# ----------------------------------------------------------------------------------------------
@st.cache_resource
def load_model_and_meta():
    return scoring.load_model(ROOT / "models"), scoring.load_meta(ROOT / "models")


@st.cache_data
def load_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


@st.cache_data
def load_config() -> dict:
    return json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))


@st.cache_data
def sample_bytes() -> bytes:
    return (ROOT / "data" / "sample.csv").read_bytes()


model, meta = load_model_and_meta()
cfg = load_config()
metrics = load_json("metrics.json")
T1, T2 = meta["thresholds"]["review"], meta["thresholds"]["block"]
USES_BAL = meta["uses_balances"]


def card(label: str, value: str, sub: str = "") -> str:
    return f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>'


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"


# ----------------------------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------------------------
st.markdown(
    f"""<div class="app-header"><h1>{cfg['project_name']}</h1>
<p>Bank security console &nbsp;|&nbsp; {cfg['course']}, {cfg['university']} &nbsp;|&nbsp; Educational project on simulated data</p></div>""",
    unsafe_allow_html=True,
)
if sklearn.__version__ != meta["sklearn_version"]:
    st.warning(
        f"The model was trained with scikit-learn {meta['sklearn_version']} but {sklearn.__version__} is installed. "
        "Install the versions in requirements.txt."
    )

tab_check, tab_batch, tab_dash, tab_about = st.tabs(["Check a transaction", "Batch check", "Dashboard", "About"])


# ----------------------------------------------------------------------------------------------
# Tab 1: single transaction
# ----------------------------------------------------------------------------------------------
DEFAULTS = {
    "in_type": "TRANSFER", "in_amount": 15_000.0, "in_hour": 11, "in_profile": "Some history",
    "in_exact": False, "in_count": 5, "in_total": 900_000.0, "in_hours": 21.0,
    "in_old_org": 120_000.0, "in_old_dest": 45_000.0, "preset": None,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def apply_preset(p: dict) -> None:
    prof = RECEIVER_PROFILES[p["profile"]]
    st.session_state.update({
        "in_type": p["type"], "in_amount": float(p["amount"]), "in_hour": int(p["hour"]),
        "in_profile": p["profile"], "in_exact": False,
        "in_count": int(prof["count"]), "in_total": float(prof["total"]), "in_hours": float(prof["hours"]),
        "in_old_org": float(p["oldbalanceOrg"]), "in_old_dest": float(p["oldbalanceDest"]),
        "preset": p["key"],
    })


def clear_preset() -> None:
    st.session_state["preset"] = None


def sync_profile() -> None:
    prof = RECEIVER_PROFILES[st.session_state["in_profile"]]
    st.session_state.update({"in_count": int(prof["count"]), "in_total": float(prof["total"]),
                             "in_hours": float(prof["hours"]), "preset": None})


PRESET_NOTES = {
    "normal_payment": ("note", "PAYMENT is not scored: the data contains no fraud of this type."),
    "small_transfer": ("note", "A typical everyday transfer. Expected result: Approve."),
    "night_new_receiver": ("note", "The classic account-takeover pattern. Expected result: Block."),
    "cash_out_after_receiving": ("note", "The second step of the attack chain: the mule cashes out everything. Expected result: Block."),
    "mule_many_transfers": ("limit", "Known limitation: in PaySim most mule accounts are new and empty, so the model learned that a busy "
                                     "receiver with money in it looks normal. It approves this case; the warning signs still point a person to it."),
    "split_fraud": ("limit", "Known limitation: when the fraudster sends one smaller piece instead of the whole balance, the strongest "
                             "signal disappears and the transfer usually slips through (see the evasion test in the Dashboard tab)."),
}

with tab_check:
    st.markdown("##### Try an example")
    cols = st.columns(3)
    for i, p in enumerate(PRESETS):
        cols[i % 3].button(p["title"], key=f"btn_{p['key']}", on_click=apply_preset, args=(p,), width="stretch")

    left, right = st.columns([1, 1.15], gap="large")
    with left:
        st.markdown("##### Transaction details")
        st.selectbox("Transaction type", TYPES, key="in_type", on_change=clear_preset)
        st.number_input("Amount", min_value=0.0, max_value=100_000_000.0, step=1_000.0, format="%.2f",
                        key="in_amount", on_change=clear_preset)
        st.slider("Hour of day (0 to 23)", 0, 23, key="in_hour", on_change=clear_preset)
        st.selectbox("Receiver account profile", list(RECEIVER_PROFILES), key="in_profile", on_change=sync_profile,
                     help="How much money the receiving account got before this transaction.")
        if USES_BAL:
            c1, c2 = st.columns(2)
            c1.number_input("Sender balance before", min_value=0.0, max_value=1_000_000_000.0, step=1_000.0,
                            format="%.2f", key="in_old_org", on_change=clear_preset)
            c2.number_input("Receiver balance before", min_value=0.0, max_value=1_000_000_000.0, step=1_000.0,
                            format="%.2f", key="in_old_dest", on_change=clear_preset)
        with st.expander("Advanced: exact receiver history"):
            st.checkbox("Use the exact numbers below instead of the profile", key="in_exact", on_change=clear_preset)
            a1, a2, a3 = st.columns(3)
            a1.number_input("Transfers received before", min_value=0, max_value=10_000, step=1, key="in_count", on_change=clear_preset)
            a2.number_input("Total received before", min_value=0.0, max_value=1e10, step=10_000.0, format="%.0f",
                            key="in_total", on_change=clear_preset)
            a3.number_input("Hours since last incoming", min_value=1.0, max_value=744.0, step=1.0, format="%.0f",
                            key="in_hours", on_change=clear_preset)
            st.caption("744 hours means no earlier incoming transfer (the data covers 743 hours).")

    ss = st.session_state
    if ss["in_exact"]:
        count, total, hours = float(ss["in_count"]), float(ss["in_total"]), float(ss["in_hours"])
    else:
        prof = RECEIVER_PROFILES[ss["in_profile"]]
        count, total, hours = float(prof["count"]), float(prof["total"]), float(prof["hours"])
    feats = features.single_transaction(
        ss["in_type"], ss["in_amount"], ss["in_hour"], count, total, hours,
        ss["in_old_org"] if USES_BAL else None, ss["in_old_dest"] if USES_BAL else None,
    )
    result = scoring.score_frame(model, meta, feats, pd.Series([ss["in_type"]]))
    v = result["verdict"].iloc[0]
    points = result["risk_points"].iloc[0]

    with right:
        st.markdown("##### Decision")
        st.markdown(
            f'<div class="verdict" style="background:{COLORS[v]}"><div class="big">{v.upper()}</div>'
            f'<div class="small">{VERDICT_TEXT[v]}</div></div>',
            unsafe_allow_html=True,
        )
        if ss["preset"]:
            preset = next(p for p in PRESETS if p["key"] == ss["preset"])
            kind, text = PRESET_NOTES[preset["key"]]
            st.markdown(f'<div class="{kind}"><b>{preset["title"]}.</b> {preset["story"]}<br>{text}</div>',
                        unsafe_allow_html=True)
        if v != "Low risk":
            gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=float(points),
                number={"suffix": " / 100", "font": {"size": 34, "color": COLORS["ink"]}},
                title={"text": "Risk points", "font": {"size": 15, "color": COLORS["ink"]}},
                gauge={
                    "axis": {"range": [0, 100], "tickvals": [0, 50, 80, 100]},
                    "bar": {"color": COLORS["ink"], "thickness": 0.28},
                    "steps": [
                        {"range": [0, 50], "color": "#CDEBE7"},
                        {"range": [50, 80], "color": "#FBE3BE"},
                        {"range": [80, 100], "color": "#F2C4BF"},
                    ],
                },
            ))
            gauge.update_layout(height=230, margin=dict(l=30, r=30, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(gauge, width="stretch", config={"displayModeBar": False})
            st.caption("0-49 Approve, 50-79 Review, 80-100 Block. Points are a rescaled model score.")
            st.markdown("##### Warning signs found")
            signs = explain.warning_signs(feats.iloc[0], use_balances=USES_BAL)
            if signs:
                for s in signs:
                    st.markdown(f'<div class="sign">{s}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="nosign">No warning signs found.</div>', unsafe_allow_html=True)
            st.caption("Warning signs are simple rules that help a person review the case. They are not the model's exact reasoning.")


# ----------------------------------------------------------------------------------------------
# Tab 2: batch
# ----------------------------------------------------------------------------------------------
REQUIRED = batch.required_columns(USES_BAL)


def run_batch(df: pd.DataFrame) -> pd.DataFrame:
    feats = features.build_features(df)
    res = scoring.score_frame(model, meta, feats, df["type"])
    out = df[[c for c in ["step", "type", "amount", "nameOrig", "nameDest", "isFraud"] if c in df.columns]].copy()
    out["risk_points"] = res["risk_points"].round(1)
    out["verdict"] = res["verdict"]
    out["warning_signs"] = [
        " | ".join(explain.warning_signs(feats.loc[i], use_balances=USES_BAL)) if res.loc[i, "verdict"] != "Low risk" else ""
        for i in feats.index
    ]
    return out


with tab_batch:
    st.markdown("##### Check many transactions at once")
    st.markdown(
        f'<div class="note">Upload a CSV in PaySim format (up to {MAX_BATCH_ROWS:,} rows). Required columns: '
        f'<b>{", ".join(REQUIRED)}</b>. Receiver history is computed <b>within the uploaded file only</b>: an account '
        "counts as new if it received nothing earlier in this file. Only TRANSFER and CASH_OUT are scored.</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    c1.download_button("Download the template (sample.csv)", sample_bytes(), file_name="sample.csv", mime="text/csv")
    use_sample = c2.button("Run on the sample file", key="run_sample")
    upload = st.file_uploader("Upload a CSV file", type=["csv"], key="batch_upload")

    payload = None
    if upload is not None:
        payload = upload.getvalue()
    elif use_sample or st.session_state.get("batch_used_sample"):
        st.session_state["batch_used_sample"] = True
        payload = sample_bytes()

    if payload is not None:
        df_in, errs, warns = batch.check_batch(payload, USES_BAL)
        for e in errs:
            st.error(e)
        for w in warns:
            st.warning(w)
        if df_in is not None:
            out = run_batch(df_in)
            counts = out["verdict"].value_counts()
            k = st.columns(4)
            for col, name in zip(k, ["Approve", "Review", "Block", "Low risk"]):
                col.markdown(card(name, f"{int(counts.get(name, 0)):,}",
                                  "not scored (type without fraud)" if name == "Low risk" else "transactions"),
                             unsafe_allow_html=True)
            if "isFraud" in out.columns:
                known = out[out["isFraud"] == 1]
                if len(known):
                    flagged = known["verdict"].isin(["Review", "Block"]).mean()
                    st.caption(f"The file includes labels: {len(known)} rows are marked as fraud and "
                               f"{pct(flagged)} of them were sent to Review or Block.")
            st.markdown(" ")
            order = {"Block": 0, "Review": 1, "Approve": 2, "Low risk": 3}
            shown = out.sort_values(["verdict", "risk_points"], key=lambda s: s.map(order) if s.name == "verdict" else -s.fillna(-1))
            st.dataframe(shown.head(500), width="stretch", hide_index=True,
                         column_config={"amount": st.column_config.NumberColumn(format="%.2f")})
            st.caption(f"Showing the {min(500, len(out)):,} highest-risk rows of {len(out):,}. The download contains all rows.")
            st.download_button("Download results (CSV)", out.to_csv(index=False).encode("utf-8"),
                               file_name="fraud_check_results.csv", mime="text/csv")


# ----------------------------------------------------------------------------------------------
# Tab 3: dashboard
# ----------------------------------------------------------------------------------------------
with tab_dash:
    prim = metrics["primary"]
    rb = prim["review_or_block"]
    st.markdown(f"##### How well model {prim['model']} ({prim['model_name']}) works on unseen test data")
    k = st.columns(4)
    k[0].markdown(card("Fraud caught", pct(rb["recall"]), "Review or Block"), unsafe_allow_html=True)
    k[1].markdown(card("Alerts that are fraud", pct(rb["precision"]), "precision"), unsafe_allow_html=True)
    k[2].markdown(card("Alerts per 1,000", f"{rb['alerts_per_1000']:.1f}", "transactions in the test period"), unsafe_allow_html=True)
    k[3].markdown(card("PR-AUC", f"{prim['pr_auc']:.3f}", "1.0 = perfect ranking"), unsafe_allow_html=True)
    trap = metrics["accuracy_trap"]["never_fraud_accuracy"]
    st.markdown(
        f'<div class="note" style="margin-top:12px"><b>The accuracy trap:</b> a model that always says "not fraud" is '
        f"{pct(trap, 2)} accurate on the same test data and catches no fraud at all. That is why we report "
        "precision, recall and PR-AUC instead of accuracy.</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Test period: hours {metrics['test_steps']}, {metrics['test_rows']:,} transactions, "
               f"{metrics['test_fraud']:,} fraud ({metrics['test_fraud_rate_pct']:.2f}%, higher than the 0.13% average, "
               "so alerts per 1,000 are higher than they would be in a typical month).")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        vc = prim["verdict_counts"]
        z = [[vc["Normal"][c] for c in ["Approve", "Review", "Block"]], [vc["Fraud"][c] for c in ["Approve", "Review", "Block"]]]
        share = [[x / sum(r) for x in r] for r in z]
        hm = go.Figure(go.Heatmap(
            z=share, x=["Approve", "Review", "Block"], y=["Normal", "Fraud"], colorscale="Blues", zmin=0, zmax=1,
            showscale=False, text=[[f"{v:,}<br>({100 * s:.1f}%)" for v, s in zip(rz, rs)] for rz, rs in zip(z, share)],
            texttemplate="%{text}", textfont={"size": 14},
        ))
        hm.update_layout(title="Decisions on the test period", height=330, margin=dict(l=10, r=10, t=50, b=10),
                         yaxis=dict(autorange="reversed"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(hm, width="stretch", config={"displayModeBar": False})
    with c2:
        comp = [c for c in metrics["comparison"] if c["pr_auc"] is not None]
        names = {"LogReg (R features)": "Logistic Regression", "R": "R Realistic", "P": "P Pre-transaction",
                 "L": "L Leaky (not real)"}
        fig = go.Figure(go.Bar(
            x=[names[c["model"]] for c in comp], y=[c["pr_auc"] for c in comp],
            marker_color=[COLORS["grey"], COLORS["navy"], "#2A9D8F", COLORS["Block"]],
            text=[f"{c['pr_auc']:.3f}" for c in comp], textposition="outside",
        ))
        fig.add_annotation(x=names["L"], y=1.17, text="uses leaked information, not real", showarrow=False,
                           font=dict(color=COLORS["Block"], size=12))
        fig.update_layout(title="PR-AUC by model (test period)", yaxis=dict(range=[0, 1.25], title="PR-AUC", tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0]),
                          height=330, margin=dict(l=10, r=10, t=50, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        rule = next(c for c in metrics["comparison"] if c["model"] == "isFlaggedFraud rule")
        st.caption(f"The simulator's own rule (isFlaggedFraud) catches only {pct(rule['recall'], 2)} of fraud.")

    c3, c4 = st.columns(2, gap="large")
    with c3:
        facts = load_json("data_facts.json")
        ft = facts["fraud_by_type"]
        order_t = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
        fig = go.Figure(go.Bar(x=order_t, y=[ft[t] for t in order_t],
                               marker_color=[COLORS["Block"] if ft[t] else COLORS["grey"] for t in order_t],
                               text=[f"{ft[t]:,}" for t in order_t], textposition="outside"))
        fig.update_layout(title="Fraud cases by transaction type (whole dataset)", height=320,
                          yaxis=dict(range=[0, max(ft.values()) * 1.2]), margin=dict(l=10, r=10, t=50, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with c4:
        imp = load_json("feature_importance.json")["features"][:6][::-1]
        fig = go.Figure(go.Bar(x=[f["importance"] for f in imp], y=[f["label"] for f in imp], orientation="h",
                               marker_color=COLORS["navy"]))
        fig.update_layout(title="Top signals the model relies on", height=320, xaxis_title="Drop in PR-AUC when shuffled",
                          margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    ev = load_json("evasion.json")
    st.markdown("##### Evasion test: one attacker trick at a time (100 frauds the model catches)")
    e_cols = st.columns(4)
    for col, (key, t) in zip(e_cols, ev["tricks"].items()):
        col.markdown(card(t["description"], f"{t['pct_approved']:.0f}%", "slip through to Approve"), unsafe_allow_html=True)


# ----------------------------------------------------------------------------------------------
# Tab 4: about
# ----------------------------------------------------------------------------------------------
with tab_about:
    facts = load_json("data_facts.json")
    ev = load_json("evasion.json")["tricks"]
    a1, a2 = st.columns([1.3, 1], gap="large")
    with a1:
        st.markdown("##### How it works")
        st.markdown(
            f"""
1. **Data.** We used PaySim, a public simulation of one month of mobile-money transactions
   ({facts['rows_total']:,} transactions, {facts['fraud_total']:,} of them fraud). No real people or accounts are involved.
2. **Attack pattern.** A criminal takes over an account, transfers the money to a "mule" account, and cashes it out.
   Fraud appears only in TRANSFER and CASH_OUT, so only those two types are scored.
3. **Signals.** For each transaction the model looks at the amount, the hour, the sender's balance before the
   payment, and the history of the receiving account (is it new, how much did it receive before).
4. **Model.** A gradient-boosted decision tree model (scikit-learn), trained on the earliest 70% of the month and
   tested on the latest 15%, which it never saw.
5. **Decision.** The risk score becomes Approve, Review (a person checks) or Block.
"""
        )
        st.markdown("##### Important caveats")
        st.markdown(
            f"""
- **Simulated data.** PaySim imitates real logs but is not real. Results on real bank data would be lower.
- **Balance columns.** The dataset author warns that fraud was cancelled in the simulation, so balance columns
  behave unnaturally for fraud. We never use balances **after** the transaction. We do use balances **before**
  it, which a bank knows; in PaySim fraud almost always moves the whole balance
  ({facts['balance_checks_pct']['Amount equals the whole sender balance']['fraud']:.0f}% of fraud cases), which makes the
  model look better than it would in real life.
- **Evasion.** Attackers can adapt. Splitting the amount into smaller transfers let {ev['split_amount']['pct_approved']:.0f}%
  of caught frauds slip through; using a receiver with normal history, {ev['receiver_with_history']['pct_approved']:.0f}%.
- **Educational use only.** This is a course project, not a production banking system.
"""
        )
    with a2:
        st.markdown("##### Team")
        rows = "".join(
            f"<tr><td style='white-space:nowrap'><b>{m['name']}</b></td><td>{m['role']}</td><td style='white-space:nowrap'><code>{Path(m['notebook']).stem.split('_')[0]}</code></td></tr>"
            for m in cfg["team"]
        )
        st.markdown(f'<table class="team"><tr><th>Name</th><th>Role</th><th>Notebook</th></tr>{rows}</table>'
                    '<div style="font-size:0.8rem;color:#5B6878;margin-top:4px">Notebooks are in the notebooks/ folder of the repository.</div>',
                    unsafe_allow_html=True)
        st.markdown("##### Course")
        st.markdown(f"{cfg['course']}  \n{cfg['department']}  \n{cfg['university']}")
        st.markdown("##### Data source")
        st.markdown("Lopez-Rojas, E. A., Elmir, A., and Axelsson, S. (2016). PaySim: A financial mobile money simulator "
                    "for fraud detection. EMSS 2016. Kaggle dataset: ealaxi/paysim1.")
