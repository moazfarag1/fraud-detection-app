"""Start the app locally, open it in headless Chromium and save a screenshot of every tab.

Usage: .venv\\Scripts\\python tools\\screenshot_app.py
Output: reports/screens/*.png
"""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screens"
PORT = 8599
URL = f"http://localhost:{PORT}"


def wait_for_server(timeout: float = 60) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(URL + "/_stcore/health", timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Streamlit did not start")


def settle(page, seconds: float = 2.5) -> None:
    page.wait_for_load_state("networkidle")
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=20_000)
    except Exception:
        pass
    time.sleep(seconds)


def crop_bottom(path: Path, margin: int = 40) -> None:
    """Remove the empty page background below the last content row."""
    img = Image.open(path).convert("RGB")
    bg = img.getpixel((5, img.height - 5))
    w, h = img.size
    px = img.load()
    last = h - 1
    for y in range(h - 1, 0, -4):
        if any(px[x, y] != bg for x in range(0, w, 6)):
            last = y
            break
    img.crop((0, 0, w, min(h, last + margin))).save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"), "--server.port", str(PORT),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 2300}, device_scale_factor=1.25)
            page.goto(URL)
            page.wait_for_selector("text=Try an example", timeout=60_000)
            settle(page, 3)

            page.get_by_role("button", name="Large transfer to a brand-new receiver at night").click()
            settle(page)
            page.screenshot(path=str(OUT / "01_check_block.png"), full_page=False)

            page.get_by_role("button", name="Normal small transfer").click()
            settle(page)
            page.screenshot(path=str(OUT / "02_check_approve.png"), full_page=False)

            page.get_by_role("button", name="Split fraud with smaller amounts").click()
            settle(page)
            page.screenshot(path=str(OUT / "03_check_split_limitation.png"), full_page=False)

            page.get_by_role("tab", name="Batch check").click()
            settle(page, 1)
            page.get_by_role("button", name="Run on the sample file").click()
            page.wait_for_selector("text=Download results (CSV)", timeout=60_000)
            settle(page)
            page.screenshot(path=str(OUT / "04_batch.png"), full_page=False)

            page.get_by_role("tab", name="Dashboard").click()
            settle(page, 3)
            page.screenshot(path=str(OUT / "05_dashboard.png"), full_page=False)

            page.get_by_role("tab", name="About").click()
            settle(page, 2)
            page.screenshot(path=str(OUT / "06_about.png"), full_page=False)
            browser.close()
        for png in OUT.glob("*.png"):
            crop_bottom(png)
        print("Screenshots saved to", OUT)
    finally:
        server.terminate()
        server.wait(timeout=20)


if __name__ == "__main__":
    main()
