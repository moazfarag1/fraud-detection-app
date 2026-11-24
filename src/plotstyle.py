"""One consistent chart style for notebooks, slides and reports (matplotlib, 200 dpi).

Not used by the app (the app uses Plotly with the same colors).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from src.data import FIGURES

NAVY = "#1F4E79"
TEAL = "#2A9D8F"
RED = "#C0392B"
AMBER = "#E9A23B"
GREY = "#8A94A6"
INK = "#1B2430"
PALETTE = [NAVY, TEAL, AMBER, RED, GREY]


def apply() -> None:
    mpl.rcParams.update({
        "figure.dpi": 100,
        "savefig.dpi": 200,
        "figure.figsize": (8, 4.2),
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelcolor": INK,
        "axes.edgecolor": "#C9D1DB",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#E6EBF1",
        "grid.linewidth": 0.8,
        "axes.prop_cycle": mpl.cycler(color=PALETTE),
        "legend.frameon": False,
        "xtick.color": INK,
        "ytick.color": INK,
    })


def save(fig, name: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    return path
