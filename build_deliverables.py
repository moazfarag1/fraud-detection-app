"""Rebuild every deliverable from config/project.json and the saved results in reports/.

Does NOT retrain models or re-execute notebooks. Run after editing config/project.json:

    .venv\\Scripts\\python build_deliverables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.deliverables import demo, figures, readme, report, report_ar, report_en, slides  # noqa: E402
from tools.deliverables.numbers import key_numbers, load_config  # noqa: E402
from tools.stamp_notebooks import stamp  # noqa: E402


def main() -> None:
    cfg = load_config()
    n = key_numbers()

    stamp(verbose=False)
    print("notebook headers and findings stamped")

    figures.build_all()
    print("figures built")

    path = slides.build(cfg, n)
    problems = slides.check_bounds(path)
    print(f"slides: {path.relative_to(ROOT)}" + ("" if not problems else f"  WARNINGS: {problems}"))

    footer = f"{cfg['project_name']}  |  {cfg['course']}, {cfg['university']}"
    for lang, module, name, toc in [("en", report_en, "Report_EN.pdf", "Contents"),
                                    ("ar", report_ar, "Report_AR.pdf", "المحتويات")]:
        doc, cover = module.build(cfg, n)
        out = ROOT / "reports" / name
        report.render(report.page_html(doc, cover, toc), out, footer)
        print(f"report: {out.relative_to(ROOT)}")

    demo.build(cfg, n)
    print("demo script: reports/Demo_Script.md")
    readme.build(cfg, n)
    print("README.md")


if __name__ == "__main__":
    main()
