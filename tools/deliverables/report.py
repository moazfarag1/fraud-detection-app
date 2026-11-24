"""Build reports/Report_EN.pdf and reports/Report_AR.pdf (HTML + CSS printed by Playwright Chromium)."""
from __future__ import annotations

import html
from pathlib import Path

from playwright.sync_api import sync_playwright

from tools.deliverables.numbers import ROOT

FONTS = ROOT / "assets" / "fonts"
FIG = ROOT / "reports" / "figures"
SCREENS = ROOT / "reports" / "screens"
BUILD = ROOT / "tmp" / "report_build"

CSS = """
@font-face { font-family: 'Noto Sans'; src: url('{noto}') format('truetype'); font-weight: 100 900; }
@font-face { font-family: 'Cairo'; src: url('{cairo}') format('truetype'); font-weight: 200 1000; }
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: {family}; color: #1B2430; font-size: 10.5pt; line-height: {lh}; margin: 0; }
h1, h2, h3 { color: #1F4E79; line-height: 1.3; }
h2 { font-size: 16pt; margin: 0 0 8pt 0; padding-bottom: 4pt; border-bottom: 2px solid #2A9D8F; break-after: avoid; }
h3 { font-size: 12pt; margin: 12pt 0 4pt 0; break-after: avoid; }
p { margin: 0 0 7pt 0; text-align: justify; }
ul, ol { margin: 0 0 8pt 0; padding-inline-start: 18pt; }
li { margin-bottom: 3pt; }
section { break-before: page; }
section.flow { break-before: auto; margin-top: 18pt; }
.cover { height: 255mm; display: flex; flex-direction: column; justify-content: space-between; break-after: page; }
.cover .band { background: linear-gradient(120deg, #12324F, #1F4E79); color: #fff; padding: 34mm 14mm 16mm 14mm; border-radius: 6px; }
.cover .band .kicker { color: #9EC5E8; font-size: 11pt; letter-spacing: 1.5px; text-transform: uppercase; }
.cover .band h1 { color: #fff; font-size: 30pt; margin: 6pt 0 10pt 0; }
.cover .band .sub { color: #DDE9F5; font-size: 12.5pt; }
.cover table.meta { width: 100%; border-collapse: collapse; font-size: 11pt; }
.cover table.meta td { padding: 5pt 6pt; border-bottom: 1px solid #DCE3EB; vertical-align: top; }
.cover table.meta td.k { color: #5B6878; width: 30%; }
.cover .note { font-size: 9.5pt; color: #5B6878; }
.toc { break-after: page; }
.toc ol { list-style: none; padding: 0; font-size: 11.5pt; }
.toc li { display: flex; border-bottom: 1px dotted #B8C3CF; padding: 5pt 0; }
.toc li span.n { width: 26pt; color: #1F4E79; font-weight: 700; }
figure { margin: 8pt 0 12pt 0; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; max-height: 92mm; border: 1px solid #E1E7EE; border-radius: 4px; }
figure img.screen { max-height: 120mm; }
figcaption { font-size: 9pt; color: #5B6878; margin-top: 4pt; }
table.data { width: 100%; border-collapse: collapse; margin: 6pt 0 12pt 0; font-size: 9.5pt; break-inside: avoid; }
table.data th { background: #1F4E79; color: #fff; padding: 5pt 6pt; text-align: start; font-weight: 600; }
table.data td { padding: 4.5pt 6pt; border-bottom: 1px solid #DCE3EB; text-align: start; vertical-align: top; }
table.data tr:nth-child(even) td { background: #F4F7FA; }
table.data td.num, table.data th.num { text-align: end; }
.box { background: #EEF3F8; border-inline-start: 4px solid #1F4E79; padding: 7pt 10pt; margin: 6pt 0 10pt 0; border-radius: 3px; break-inside: avoid; }
.warn { background: #FDECEA; border-inline-start: 4px solid #C0392B; }
.kpis { display: flex; gap: 8pt; margin: 8pt 0 12pt 0; }
.kpi { flex: 1; border: 1px solid #DCE3EB; border-radius: 5px; padding: 7pt; text-align: center; }
.kpi .v { font-size: 17pt; font-weight: 700; color: #1F4E79; }
.kpi .l { font-size: 8.5pt; color: #5B6878; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #F1F4F8; padding: 0 2pt; border-radius: 2px; }
pre { font-family: Consolas, monospace; font-size: 8.5pt; background: #F4F7FA; padding: 6pt; border-radius: 3px; direction: ltr; text-align: left; }
.refs li { margin-bottom: 6pt; }
bdi { unicode-bidi: isolate; }
"""


class Doc:
    """Collects sections and numbers figures and tables automatically."""

    def __init__(self, lang: str):
        self.lang = lang
        self.sections: list[tuple[str, str, str]] = []
        self.fig_no = 0
        self.tab_no = 0

    def fig(self, path: Path, caption: str, cls: str = "") -> str:
        self.fig_no += 1
        label = "Figure" if self.lang == "en" else "شكل"
        return (f'<figure><img class="{cls}" src="{path.as_uri()}">'
                f"<figcaption><b>{label} {self.fig_no}.</b> {caption}</figcaption></figure>")

    def table(self, head: list[str], rows: list[list[str]], num_cols: tuple[int, ...] = (), caption: str = "") -> str:
        self.tab_no += 1
        label = "Table" if self.lang == "en" else "جدول"
        th = "".join(f'<th class="{"num" if i in num_cols else ""}">{h}</th>' for i, h in enumerate(head))
        body = "".join(
            "<tr>" + "".join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
            for r in rows
        )
        cap = f'<figcaption style="text-align:start"><b>{label} {self.tab_no}.</b> {caption}</figcaption>' if caption else ""
        return f'<div style="break-inside:avoid">{cap}<table class="data"><tr>{th}</tr>{body}</table></div>'

    def add(self, title: str, body: str, new_page: bool = True) -> None:
        self.sections.append((title, body, "" if new_page else "flow"))


def page_html(doc: Doc, cover: str, toc_title: str) -> str:
    rtl = doc.lang == "ar"
    family = "'Cairo', 'Noto Sans', sans-serif" if rtl else "'Noto Sans', sans-serif"
    css = (CSS.replace("{noto}", (FONTS / "NotoSans.ttf").as_uri())
              .replace("{cairo}", (FONTS / "Cairo.ttf").as_uri())
              .replace("{family}", family)
              .replace("{lh}", "1.75" if rtl else "1.5"))
    toc_items = "".join(f'<li><span class="n">{i}.</span><span>{t}</span></li>' for i, (t, _, _) in enumerate(doc.sections, 1))
    body = "".join(
        f'<section class="{cls}"><h2>{i}. {t}</h2>{b}</section>' for i, (t, b, cls) in enumerate(doc.sections, 1)
    )
    return (f'<!doctype html><html lang="{doc.lang}" dir="{"rtl" if rtl else "ltr"}"><head><meta charset="utf-8">'
            f"<style>{css}</style></head><body>{cover}"
            f'<div class="toc"><h2>{toc_title}</h2><ol>{toc_items}</ol></div>{body}</body></html>')


def render(html_text: str, out_pdf: Path, footer_label: str) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    src = BUILD / (out_pdf.stem + ".html")
    src.write_text(html_text, encoding="utf-8")
    footer = (
        '<div style="width:100%; font-size:8px; color:#8A94A6; padding:0 18mm; display:flex; '
        'justify-content:space-between; font-family:Arial, sans-serif;">'
        f'<span>{html.escape(footer_label)}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(src.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(out_pdf), format="A4", print_background=True, display_header_footer=True,
                 header_template="<div></div>", footer_template=footer,
                 margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
        browser.close()


def cover_html(cfg: dict, title_kicker: str, subtitle: str, labels: dict, note: str) -> str:
    team = "<br>".join(f"<bdi>{m['name']}</bdi>" for m in cfg["team"])
    return f"""
<div class="cover">
  <div class="band">
    <div class="kicker">{title_kicker}</div>
    <h1><bdi>{cfg['project_name']}</bdi></h1>
    <div class="sub">{subtitle}</div>
  </div>
  <table class="meta">
    <tr><td class="k">{labels['course']}</td><td><bdi>{cfg['course']}</bdi></td></tr>
    <tr><td class="k">{labels['university']}</td><td><bdi>{cfg['university']}</bdi><br><bdi>{cfg['faculty']}</bdi><br><bdi>{cfg['department']}</bdi></td></tr>
    <tr><td class="k">{labels['team']}</td><td>{team}</td></tr>
    <tr><td class="k">{labels['date']}</td><td><bdi>{cfg['date']}</bdi></td></tr>
  </table>
  <div class="note">{note}</div>
</div>"""
