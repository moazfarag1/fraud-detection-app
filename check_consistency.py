"""Check that the slides and both PDF reports quote the same key numbers as reports/metrics.json,
and that every team member's name appears. Fails loudly (exit code 1) on any mismatch.

    .venv\Scripts\python check_consistency.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf
from pptx import Presentation

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.deliverables.numbers import key_numbers, load_config  # noqa: E402

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")


def pdf_text(path: Path) -> str:
    with pymupdf.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def pptx_text(path: Path) -> str:
    prs = Presentation(path)
    parts = []
    for slide in prs.slides:
        for sh in slide.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if sh.has_table:
                parts.extend(c.text for row in sh.table.rows for c in row.cells)
    return "\n".join(parts)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def main() -> int:
    cfg = load_config()
    n = key_numbers()
    metrics = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))
    rb = metrics["primary"]["review_or_block"]

    # the formatted numbers must themselves match metrics.json after rounding
    expected = {
        "precision": f"{100 * rb['precision']:.1f}",
        "recall": f"{100 * rb['recall']:.1f}",
        "pr_auc": f"{metrics['primary']['pr_auc']:.3f}",
        "alerts_per_1000": f"{rb['alerts_per_1000']:.1f}",
    }
    assert n["precision_pct"].rstrip("%") == expected["precision"]
    assert n["recall_pct"].rstrip("%") == expected["recall"]
    assert n["pr_auc"] == expected["pr_auc"]
    assert n["alerts_per_1000"] == expected["alerts_per_1000"]

    docs = {
        "slides/Fraud_Detector.pptx": pptx_text(ROOT / "slides" / "Fraud_Detector.pptx"),
        "reports/Report_EN.pdf": pdf_text(ROOT / "reports" / "Report_EN.pdf"),
        "reports/Report_AR.pdf": pdf_text(ROOT / "reports" / "Report_AR.pdf"),
        "reports/Demo_Script.md": (ROOT / "reports" / "Demo_Script.md").read_text(encoding="utf-8"),
        "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
    }
    required_numbers = {
        "slides/Fraud_Detector.pptx": ["precision", "alerts_per_1000", "pr_auc"],
        "reports/Report_EN.pdf": ["precision", "recall", "pr_auc", "alerts_per_1000"],
        "reports/Report_AR.pdf": ["precision", "recall", "pr_auc", "alerts_per_1000"],
        "reports/Demo_Script.md": ["precision", "alerts_per_1000"],
        "README.md": ["precision", "recall", "pr_auc", "alerts_per_1000"],
    }
    failures = []
    for name, text in docs.items():
        t = norm(text)
        for key in required_numbers[name]:
            if expected[key] not in t:
                failures.append(f"{name}: missing {key} = {expected[key]}")
        # slides quote recall as "X of every 100"
        if name.endswith(".pptx") and f"{n['per_100']} of every 100" not in t:
            failures.append(f"{name}: missing '{n['per_100']} of every 100'")
        for m in cfg["team"]:
            if m["name"] not in t:
                failures.append(f"{name}: team member '{m['name']}' not found")
        if EMOJI.search(text):
            failures.append(f"{name}: contains an emoji")

    for name in docs:
        print(f"checked {name}")
    if failures:
        print("\nCONSISTENCY CHECK FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"\nOK: precision {expected['precision']}%, recall {expected['recall']}%, PR-AUC {expected['pr_auc']}, "
          f"{expected['alerts_per_1000']} alerts per 1,000, and all {len(cfg['team'])} team names found everywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
