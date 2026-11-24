"""Single source of the numbers quoted in slides, reports, demo script and README.

Everything is read from reports/*.json and formatted once here, so check_consistency.py can verify
that every deliverable quotes exactly these values.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict:
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))


def load_config() -> dict:
    return json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))


def key_numbers() -> dict:
    m = _load("metrics.json")
    v = _load("validation.json")
    f = _load("data_facts.json")
    e = _load("evasion.json")
    imp = _load("feature_importance.json")
    presets = _load("app_presets.json")
    meta = json.loads((ROOT / "models" / "model_meta.json").read_text(encoding="utf-8"))

    p = m["primary"]
    rb, blk = p["review_or_block"], p["block"]
    comp = {c["model"]: c for c in m["comparison"]}
    vmod = {r["model"]: r for r in v["models"]}
    bal = f["balance_checks_pct"]
    tricks = e["tricks"]
    split = {r["part"]: r for r in v["split"]}

    def pc(x, d=1):
        return f"{100 * x:.{d}f}%"

    n = {
        # primary model, test period
        "model": p["model"],
        "model_name": p["model_name"],
        "recall_pct": pc(rb["recall"]),
        "precision_pct": pc(rb["precision"]),
        "f1": f"{rb['f1']:.3f}",
        "pr_auc": f"{p['pr_auc']:.3f}",
        "roc_auc": f"{p['roc_auc']:.3f}",
        "alerts_per_1000": f"{rb['alerts_per_1000']:.1f}",
        "per_100": f"{round(100 * rb['recall'])}",
        "block_recall_pct": pc(blk["recall"]),
        "block_precision_pct": pc(blk["precision"]),
        "missed": f"{rb['confusion']['fn']:,}",
        "false_alarms": f"{rb['confusion']['fp']:,}",
        "test_fraud": f"{m['test_fraud']:,}",
        "test_rows": f"{m['test_rows']:,}",
        "test_rate_pct": f"{m['test_fraud_rate_pct']:.2f}%",
        "test_steps": m["test_steps"],
        "never_acc_test_pct": pc(m["accuracy_trap"]["never_fraud_accuracy"], 2),
        "never_acc_all_pct": f"{100 - f['fraud_rate_pct']:.2f}%",
        "thr_review": f"{meta['thresholds']['review']:.4f}",
        "thr_block": f"{meta['thresholds']['block']:.4f}",
        # model comparison (test PR-AUC)
        "pr_auc_R": f"{comp['R']['pr_auc']:.3f}",
        "pr_auc_P": f"{comp['P']['pr_auc']:.3f}",
        "pr_auc_L": f"{comp['L']['pr_auc']:.3f}",
        "pr_auc_LR": f"{comp['LogReg (R features)']['pr_auc']:.3f}",
        "prec_R_pct": pc(comp["R"]["precision"]),
        "recall_R_pct": pc(comp["R"]["recall"]),
        "alerts_R": f"{comp['R']['alerts_per_1000']:.1f}",
        "rule_recall_pct": pc(comp["isFlaggedFraud rule"]["recall"], 2),
        # validation
        "val_pr_auc_R": f"{vmod['R']['pr_auc']:.3f}",
        "val_pr_auc_P": f"{vmod['P']['pr_auc']:.3f}",
        "val_prec85_R_pct": pc(vmod["R"]["precision_at_85_recall"]),
        "val_alerts85_R": f"{vmod['R']['alerts_per_1000']:.0f}",
        "val_rb_recall_pct": pc(v["primary_validation"]["review_or_block"]["recall"]),
        "val_rb_precision_pct": pc(v["primary_validation"]["review_or_block"]["precision"]),
        "val_alerts": f"{v['primary_validation']['review_or_block']['alerts_per_1000']:.1f}",
        "rand_pr_auc_R": f"{v['random_split_check']['R']['test_pr_auc']:.3f}",
        "rand_pr_auc_P": f"{v['random_split_check']['P']['test_pr_auc']:.3f}",
        "train_steps": f"1-{v['split_steps']['train_before'] - 1}",
        "val_steps": f"{v['split_steps']['train_before']}-{v['split_steps']['test_from'] - 1}",
        "train_rows": f"{split['train']['rows']:,}",
        "train_rate_pct": f"{split['train']['fraud_rate_pct']:.2f}%",
        "val_rate_pct": f"{split['validation']['fraud_rate_pct']:.2f}%",
        "undersample": str(v["undersample_ratio"]),
        # data facts
        "rows_total": f"{f['rows_total']:,}",
        "rows_scored": f"{f['rows_transfer_cashout']:,}",
        "fraud_total": f"{f['fraud_total']:,}",
        "fraud_rate_pct": f"{f['fraud_rate_pct']:.2f}%",
        "one_in": f"{round(100 / f['fraud_rate_pct']):,}",
        "fraud_transfer": f"{f['fraud_by_type']['TRANSFER']:,}",
        "fraud_cashout": f"{f['fraud_by_type']['CASH_OUT']:,}",
        "night_fraud_pct": f"{f['night_share_fraud_pct']:.0f}%",
        "night_normal_pct": f"{f['night_share_normal_pct']:.0f}%",
        "night_rate_pct": f"{f['fraud_rate_night_pct']:.1f}%",
        "day_rate_pct": f"{f['fraud_rate_day_pct']:.2f}%",
        "late_rate_pct": f"{f['fraud_rate_steps_401_743_pct']:.2f}%",
        "early_rate_pct": f"{f['fraud_rate_steps_1_400_pct']:.2f}%",
        "median_ratio": f"{f['median_amount_fraud'] / f['median_amount_normal_scored']:.1f}",
        "at_cap": f"{f['fraud_rows_at_max_amount']}",
        "flagged_rows": f"{f['flagged_rows']}",
        "flag_recall_all_pct": f"{f['flagged_recall_pct']:.2f}%",
        "empties_fraud_pct": f"{bal['Amount equals the whole sender balance']['fraud']:.0f}%",
        "empties_normal_pct": f"{bal['Amount equals the whole sender balance']['normal']:.1f}%",
        "dest_zero_fraud_pct": f"{bal['Receiver balance 0 before and after']['fraud']:.0f}%",
        "dest_zero_normal_pct": f"{bal['Receiver balance 0 before and after']['normal']:.2f}%",
        "orig_err_normal_pct": f"{bal['Sender balances do not add up']['normal']:.0f}%",
        "orig_err_fraud_pct": f"{bal['Sender balances do not add up']['fraud']:.1f}%",
        "unique_senders": f"{f['unique_senders']:,}",
        "unique_receivers": f"{f['unique_receivers']:,}",
        # evasion
        "ev_split_pct": f"{tricks['split_amount']['pct_approved']:.0f}%",
        "ev_hist_pct": f"{tricks['receiver_with_history']['pct_approved']:.0f}%",
        "ev_day_pct": f"{tricks['daytime_hour']['pct_approved']:.0f}%",
        "ev_round_pct": f"{tricks['round_amount']['pct_approved']:.0f}%",
        # features
        "top_features": [x["label"] for x in imp["features"][:3]],
        # app
        "sample_rows": f"{presets['sample_batch']['rows']:,}",
        "sample_flagged_pct": f"{presets['sample_batch']['labeled_fraud_flagged_pct']:.1f}%",
        "sample_false_alarms": f"{presets['sample_batch']['normal_flagged']}",
        "presets": {r["key"]: r["verdict"] for r in presets["presets"]},
    }
    ff = _load("feature_facts.json")
    n.update({
        "new_recv_fraud_pct": f"{ff['new_receiver_share_fraud_pct']:.0f}%",
        "new_recv_normal_pct": f"{ff['new_receiver_share_normal_pct']:.0f}%",
        "new_recv_lift": f"{ff['new_receiver_lift']:.1f}",
        "leak_rows": f"{ff['leakage_check_rows']:,}",
        "leak_hours": str(ff["leakage_check_hours"]),
        "n_feat_R": str(ff["n_features"]["R"]),
        "n_feat_P": str(ff["n_features"]["P"]),
        "n_feat_L": str(ff["n_features"]["L"]),
    })
    return n


def presenter_for_slide(cfg: dict, slide_no: int) -> str:
    for m in cfg["team"]:
        if slide_no in m.get("slides", []):
            return m["name"]
    return cfg["team"][0]["name"]
