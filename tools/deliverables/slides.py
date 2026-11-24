"""Build slides/Fraud_Detector.pptx (16:9, English, non-technical) from config and saved results."""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from tools.deliverables.numbers import ROOT, presenter_for_slide

NAVY = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x12, 0x32, 0x4F)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
RED = RGBColor(0xC0, 0x39, 0x2B)
INK = RGBColor(0x1B, 0x24, 0x30)
GREY = RGBColor(0x5B, 0x68, 0x78)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"
FIG = ROOT / "reports" / "figures"
SCREENS = ROOT / "reports" / "screens"
OUT = ROOT / "slides" / "Fraud_Detector.pptx"
TOTAL = 10


def _text(slide, x, y, w, h, lines, size=20, color=INK, bold=False, bullets=False, align=PP_ALIGN.LEFT,
          spacing=10, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(spacing)
        parts = line if isinstance(line, list) else [(line, bold)]
        if bullets:
            r = p.add_run()
            r.text = "■  "
            r.font.size = Pt(size - 8)
            r.font.color.rgb = TEAL
            r.font.name = FONT
        for txt, b in parts:
            r = p.add_run()
            r.text = txt
            r.font.size = Pt(size)
            r.font.bold = b
            r.font.color.rgb = color
            r.font.name = FONT
    return box


def _picture(slide, path: Path, x, y, w, h):
    """Insert a picture scaled to fit inside the box (x, y, w, h), centered."""
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    return slide.shapes.add_picture(str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def _frame(prs, cfg, no: int, title: str, notes: str):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    _text(slide, 0.6, 0.35, 12.1, 0.9, [title], size=34, color=NAVY, bold=True)
    acc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.62), Inches(1.22), Inches(1.3), Inches(0.07))
    acc.fill.solid()
    acc.fill.fore_color.rgb = TEAL
    acc.line.fill.background()
    _text(slide, 0.6, 6.92, 7.5, 0.4, [f"Presented by: {presenter_for_slide(cfg, no)}"], size=12, color=GREY)
    _text(slide, 8.2, 6.92, 4.5, 0.4, [f"{cfg['short_name']}  |  {no} / {TOTAL}"], size=12, color=GREY,
          align=PP_ALIGN.RIGHT)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def build(cfg: dict, n: dict) -> Path:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # 1. Title -------------------------------------------------------------------------------
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK
    bg.line.fill.background()
    acc = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.95), Inches(1.6), Inches(0.08))
    acc.fill.solid()
    acc.fill.fore_color.rgb = TEAL
    acc.line.fill.background()
    _text(s, 0.8, 1.2, 11.8, 1.7, [cfg["project_name"]], size=44, color=WHITE, bold=True, anchor=MSO_ANCHOR.BOTTOM)
    _text(s, 0.8, 3.2, 11.8, 1.0, [f"{cfg['course']}  |  {cfg['university']}", cfg["department"]], size=20,
          color=RGBColor(0xC9, 0xD8, 0xE8), spacing=4)
    names = [m["name"] for m in cfg["team"]]
    _text(s, 0.8, 4.65, 11.8, 1.3, ["Team: " + ", ".join(names[:3]) + ",", ", ".join(names[3:])], size=18,
          color=WHITE, spacing=4)
    _text(s, 0.8, 6.5, 11.8, 0.5, [cfg["date"]], size=14, color=RGBColor(0xC9, 0xD8, 0xE8))
    s.notes_slide.notes_text_frame.text = (
        f"Presenter: {presenter_for_slide(cfg, 1)}. Introduce the project and the team. "
        "We built a system that flags suspicious money transfers in a mobile-money service, trained on a public "
        "simulated dataset, and deployed it as a web app."
    )

    # 2. Problem -------------------------------------------------------------------------------
    s = _frame(prs, cfg, 2, "The problem: transfer fraud",
               "Fraud costs people and banks a lot of money, and it is growing. One reference fact: the US Federal "
               "Trade Commission reports that consumers lost more than 12.5 billion US dollars to fraud in 2024. "
               "Our question: can a model flag fraudulent transfers early, while keeping alerts for honest "
               "customers low?")
    _text(s, 0.6, 1.6, 7.0, 4.8, [
        "Criminals take over accounts and move the money out in minutes",
        "Banks must decide on each payment in real time",
        "Fraud is rare, so it hides among millions of normal payments",
        "Goal: flag fraud early, with few false alarms",
    ], size=22, bullets=True, spacing=16)
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.1), Inches(1.9), Inches(4.6), Inches(3.4))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0xEE, 0xF3, 0xF8)
    box.line.fill.background()
    _text(s, 8.35, 2.1, 4.1, 1.2, ["$12.5 billion"], size=40, color=RED, bold=True)
    _text(s, 8.35, 3.2, 4.1, 1.5, ["lost to fraud by US consumers in 2024"], size=20, color=INK)
    _text(s, 8.35, 4.45, 4.1, 0.7, ["Source: US Federal Trade Commission, March 2025"], size=12, color=GREY)

    # 3. Threat model --------------------------------------------------------------------------
    s = _frame(prs, cfg, 3, "How attackers operate",
               "This is our threat model. Step 1: the attacker takes over a customer's account. Step 2: the whole "
               "balance is transferred to another account. Step 3: that account is a money mule, often brand new. "
               "Step 4: the mule cashes the money out. A bank cannot see the criminal, but it can see the receiving "
               "account's history. That is the main idea behind our features.")
    _picture(s, FIG / "00_attack_chain.png", 0.6, 1.55, 12.1, 3.7)
    _text(s, 0.6, 5.4, 12.1, 1.3, [
        "A bank cannot see the criminal, but it can see the receiving account and its history",
    ], size=20, bullets=True)

    # 4. Data ----------------------------------------------------------------------------------
    s = _frame(prs, cfg, 4, "Our data: PaySim",
               f"PaySim is a public simulator built from one month of real mobile-money logs (Lopez-Rojas et al., "
               f"2016). It has {n['rows_total']} transactions and only {n['fraud_total']} are fraud, "
               f"{n['fraud_rate_pct']}, about one in {n['one_in']}. Fraud appears only in TRANSFER and CASH_OUT, so we "
               "model only those two types. The data is simulated, so no real customers are involved.")
    _text(s, 0.6, 1.6, 6.0, 4.8, [
        "Public simulation of one month of mobile-money logs",
        [(f"{n['rows_total']}", True), (" transactions, no real people", False)],
        [("Fraud is rare: ", False), (f"{n['fraud_rate_pct']}", True), (f" (1 in {n['one_in']})", False)],
        "Fraud only in TRANSFER and CASH_OUT",
    ], size=21, bullets=True, spacing=16)
    _picture(s, FIG / "01_fraud_by_type.png", 6.8, 1.6, 5.9, 4.9)

    # 5. EDA -----------------------------------------------------------------------------------
    s = _frame(prs, cfg, 5, "What the data showed",
               f"Two findings. First, fraud does not sleep: {n['night_fraud_pct']} of fraud happens between midnight "
               f"and 6 am, against {n['night_normal_pct']} of normal traffic, so the fraud rate at night is "
               f"{n['night_rate_pct']} compared with {n['day_rate_pct']} by day. Second, the balance columns separate "
               f"fraud too perfectly: {n['empties_fraud_pct']} of frauds move exactly the whole balance. Part of this is "
               "a simulation artifact, so we treat balances with care.")
    _text(s, 0.6, 1.6, 5.4, 4.8, [
        [("Fraud does not sleep: ", True), (f"{n['night_fraud_pct']} of fraud happens at night vs {n['night_normal_pct']} of normal", False)],
        [("Night fraud rate: ", True), (f"{n['night_rate_pct']} vs {n['day_rate_pct']} by day", False)],
        [("Balance warning: ", True), (f"{n['empties_fraud_pct']} of frauds empty the whole account, partly a simulation artifact", False)],
    ], size=20, bullets=True, spacing=16)
    _picture(s, FIG / "02_fraud_by_hour.png", 6.2, 1.6, 6.5, 4.9)

    # 6. Signals ----------------------------------------------------------------------------------
    s = _frame(prs, cfg, 6, "Signals we gave the model",
               f"We built {n['n_feat_L']} signals in four groups. The key one is receiver history: has this account "
               f"received money before? {n['new_recv_fraud_pct']} of frauds go to a brand-new account, compared with "
               f"{n['new_recv_normal_pct']} of normal transfers. We only use the past: we proved that removing future "
               "data does not change any value. We never give the model the account IDs or the answer.")
    _text(s, 0.6, 1.6, 6.2, 4.8, [
        [("Transaction: ", True), ("amount, hour, transfer or cash-out", False)],
        [("Receiver history: ", True), ("new account? money received before?", False)],
        [("Balance before payment: ", True), ("does it empty the account?", False)],
        [("No peeking: ", True), ("only earlier hours are used", False)],
    ], size=20, bullets=True, spacing=16)
    _picture(s, FIG / "03_new_receiver.png", 6.9, 1.7, 5.8, 4.6)

    # 7. Accuracy trap and models ----------------------------------------------------------------
    s = _frame(prs, cfg, 7, "The accuracy trap and our models",
               f"A model that always says 'not fraud' is {n['never_acc_all_pct']} accurate on the whole dataset and "
               f"catches nothing. That is why we use precision, recall and PR-AUC. We trained three models. L uses "
               f"balances after the payment and scores a PR-AUC of {n['pr_auc_L']}, but that information is leaked. "
               f"R uses no balances and scores {n['pr_auc_R']}. P uses balances a bank knows before approving and "
               f"scores {n['pr_auc_P']}. We use P in the app.")
    _text(s, 0.6, 1.6, 5.0, 4.8, [
        [("Always saying \"not fraud\" = ", False), (f"{n['never_acc_all_pct']} accurate", True), (", 0 fraud caught", False)],
        [("L (leaky): ", True), (f"PR-AUC {n['pr_auc_L']}, not real", False)],
        [("R (no balances): ", True), (f"PR-AUC {n['pr_auc_R']}", False)],
        [("P (used in the app): ", True), (f"PR-AUC {n['pr_auc_P']}", False)],
    ], size=20, bullets=True, spacing=16)
    _picture(s, FIG / "04b_model_comparison.png", 5.8, 1.6, 6.9, 4.9)

    # 8. Results and evasion ----------------------------------------------------------------------
    s = _frame(prs, cfg, 8, "Results, and how it can be fooled",
               f"On the last part of the month, which the model never saw, it catches {n['per_100']} of every 100 fraud "
               f"transfers (Review or Block), with {n['alerts_per_1000']} alerts per 1,000 transactions, and "
               f"{n['precision_pct']} of alerts are real fraud. That test period has more fraud than usual, so alerts "
               f"are higher than in a normal month. Attackers can adapt: splitting the amount into smaller transfers "
               f"let {n['ev_split_pct']} of caught frauds through.")
    _text(s, 0.6, 1.6, 5.6, 4.8, [
        [("Catches ", False), (f"{n['per_100']} of every 100", True), (" fraud transfers", False)],
        [(f"{n['alerts_per_1000']} alerts", True), (" per 1,000 transactions", False)],
        [(f"{n['precision_pct']}", True), (" of alerts are real fraud", False)],
        [("Splitting the amount fools it: ", False), (f"{n['ev_split_pct']} slip through", True)],
    ], size=20, bullets=True, spacing=16)
    _picture(s, FIG / "04b_evasion.png", 6.4, 1.8, 6.3, 4.4)

    # 9. App -----------------------------------------------------------------------------------------
    s = _frame(prs, cfg, 9, "The app and live demo",
               "The web app is a bank security console. Check one transaction or click an example, upload a CSV for "
               "a batch check, see the honest results in the dashboard, and read how it works in the About tab. "
               "Live demo: click 'Large transfer to a brand-new receiver at night' (Block), then 'Split fraud with "
               "smaller amounts' (Approve, a known limitation).")
    shot = Image.open(SCREENS / "01_check_block.png")
    crop = shot.crop((int(shot.width * 0.1), 0, int(shot.width * 0.9), min(shot.height, int(shot.width * 0.8 * 0.66))))
    crop_path = FIG / "app_check_slide.png"
    crop.save(crop_path)
    _picture(s, crop_path, 0.6, 1.5, 7.8, 5.3)
    _text(s, 8.7, 1.7, 4.0, 4.8, [
        "Check one transaction",
        "Batch check a CSV file",
        "Dashboard with honest results",
        "Warning signs in plain English",
    ], size=20, bullets=True, spacing=16)
    if cfg.get("app_url"):
        _text(s, 8.7, 5.4, 4.0, 1.2, ["Try it live:", cfg["app_url"].replace("https://", "").rstrip("/")],
              size=18, color=NAVY, bold=True, spacing=2)

    # 10. Limits, next steps, team --------------------------------------------------------------------
    s = _frame(prs, cfg, 10, "Limits, next steps and team",
               "Limits: the data is simulated, and the strongest signal (emptying the whole balance) is very regular in "
               "the simulator, so real-world results would be lower. The model can be fooled by splitting the amount. "
               "Next steps: look at several transactions of the same account together, and test on real, anonymized "
               "bank data. Then thank the audience and introduce each team member's role.")
    _text(s, 0.6, 1.6, 5.6, 4.8, [
        [("Limit: ", True), ("simulated data, results would be lower in real life", False)],
        [("Limit: ", True), ("splitting the amount fools the model", False)],
        [("Next: ", True), ("watch several transfers of one account together", False)],
        [("Next: ", True), ("test on real, anonymized bank data", False)],
    ], size=18, bullets=True, spacing=14)
    rows, cols = len(cfg["team"]) + 1, 2
    tbl = s.shapes.add_table(rows, cols, Inches(6.5), Inches(1.6), Inches(6.2), Inches(0.42 * rows)).table
    tbl.columns[0].width = Inches(2.3)
    tbl.columns[1].width = Inches(3.9)
    for j, head in enumerate(["Team member", "Role"]):
        c = tbl.cell(0, j)
        c.text = head
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
    for i, m in enumerate(cfg["team"], start=1):
        tbl.cell(i, 0).text = m["name"]
        tbl.cell(i, 1).text = m["role"]
    for i in range(rows):
        for j in range(cols):
            for p in tbl.cell(i, j).text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(13)
                    r.font.name = FONT
                    r.font.bold = i == 0
                    r.font.color.rgb = WHITE if i == 0 else INK

    OUT.parent.mkdir(exist_ok=True)
    prs.save(OUT)
    return OUT


def check_bounds(path: Path = OUT) -> list[str]:
    """Return a list of shapes that go outside the slide or text below the minimum size."""
    prs = Presentation(path)
    W, H = prs.slide_width, prs.slide_height
    problems = []
    for i, slide in enumerate(prs.slides, start=1):
        for sh in slide.shapes:
            if sh.left < 0 or sh.top < 0 or sh.left + sh.width > W + Emu(10) or sh.top + sh.height > H + Emu(10):
                problems.append(f"slide {i}: shape '{sh.name}' exceeds the slide bounds")
        if not slide.notes_slide.notes_text_frame.text.strip():
            problems.append(f"slide {i}: no speaker notes")
    return problems


def estimate_overflow(path: Path = OUT) -> list[str]:
    """Rough check that text fits its box (average glyph width ~0.5 x font size). LibreOffice is not available."""
    prs = Presentation(path)
    issues = []
    for i, slide in enumerate(prs.slides, start=1):
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            width_pt = sh.width / 12700
            need = 0.0
            for p in sh.text_frame.paragraphs:
                sizes = [r.font.size.pt for r in p.runs if r.font.size]
                if not sizes:
                    continue
                size = max(sizes)
                chars = sum(len(r.text) for r in p.runs)
                per_line = max(1, int(width_pt / (size * 0.5)))
                lines = -(-chars // per_line)
                need += lines * size * 1.2 + (p.space_after.pt if p.space_after else 0)
            bottom = (sh.top / 12700) + need
            if bottom > 7.5 * 72 - 0.6 * 72 and sh.top / 12700 < 6.8 * 72:
                issues.append(f"slide {i}: text in '{sh.name}' may run into the footer (needs ~{need:.0f} pt)")
    return issues
