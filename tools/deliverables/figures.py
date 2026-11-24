"""Extra figures made from saved results only (no data, no retraining)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from src import plotstyle  # noqa: E402


def attack_chain() -> None:
    plotstyle.apply()
    fig, ax = plt.subplots(figsize=(12, 3.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    steps = [
        ("1. Account takeover", "Stolen PIN, SIM swap\nor phishing", plotstyle.NAVY),
        ("2. TRANSFER", "Victim's balance is sent\nto another account", plotstyle.AMBER),
        ("3. Mule account", "Often new, receives\nthe stolen money", plotstyle.RED),
        ("4. CASH_OUT", "Money leaves the\nsystem as cash", plotstyle.TEAL),
    ]
    w, gap, y = 2.6, 0.43, 0.7
    for i, (title, sub, color) in enumerate(steps):
        x = 0.25 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, y), w, 1.8, boxstyle="round,pad=0.02,rounding_size=0.15",
                                    facecolor=color, edgecolor="none"))
        ax.text(x + w / 2, y + 1.3, title, ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        ax.text(x + w / 2, y + 0.6, sub, ha="center", va="center", color="white", fontsize=10.5)
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.03, y + 0.9), (x + w + gap - 0.03, y + 0.9),
                                         arrowstyle="-|>", mutation_scale=22, color=plotstyle.INK, lw=2))
    ax.text(6.0, 0.22, "Where we watch: the TRANSFER and CASH_OUT step, and the history of the receiving account",
            ha="center", fontsize=11, color=plotstyle.INK, style="italic")
    plotstyle.save(fig, "00_attack_chain")
    plt.close(fig)


def build_all() -> None:
    attack_chain()
