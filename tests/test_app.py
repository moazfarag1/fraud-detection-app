"""Smoke tests for app.py with Streamlit's AppTest (no browser needed)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.presets import PRESETS

APP = str(Path(__file__).resolve().parents[1] / "app.py")
EXPECTED = {
    "normal_payment": "LOW RISK",
    "small_transfer": "APPROVE",
    "night_new_receiver": "BLOCK",
    "cash_out_after_receiving": "BLOCK",
    "mule_many_transfers": "APPROVE",
    "split_fraud": "APPROVE",
}


def verdict_text(at: AppTest) -> str:
    html = " ".join(m.value for m in at.markdown)
    for word in ["LOW RISK", "APPROVE", "REVIEW", "BLOCK"]:
        if f'<div class="big">{word}</div>' in html:
            return word
    return ""


def test_app_compiles():
    compile(Path(APP).read_text(encoding="utf-8"), APP, "exec")


def test_app_starts_without_errors():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert len(at.tabs) == 4


@pytest.mark.parametrize("preset", PRESETS, ids=[p["key"] for p in PRESETS])
def test_every_preset(preset):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.button(key=f"btn_{preset['key']}").click().run()
    assert not at.exception
    assert verdict_text(at) == EXPECTED[preset["key"]]


def test_batch_on_sample_file():
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.button(key="run_sample").click().run()
    assert not at.exception
    assert not at.error
    assert len(at.dataframe) >= 1
