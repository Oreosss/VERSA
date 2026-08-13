"""Grouped bar chart: comprehension accuracy, Raw NVD vs Summary condition.

Single-column thesis figure. No title (caption handles it in the write-up).
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "CMU Serif", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False

FIGURES_DIR = Path("figures/human_study")

COLOR_RAW = "#8c8c88"
COLOR_SUMMARY = "#4a6fa5"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

LABELS = ["Raw NVD", "Summary"]
VALUES = [83.9, 88.5]
COLORS = [COLOR_RAW, COLOR_SUMMARY]


def main():
    fig, ax = plt.subplots(figsize=(6, 4))

    bars = ax.bar(LABELS, VALUES, width=0.5, color=COLORS, zorder=3)
    for bar, value in zip(bars, VALUES):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1.5,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            color=TEXT_PRIMARY,
        )

    ax.set_ylim(0, 100)
    ax.set_ylabel("Comprehension accuracy (%)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)

    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = FIGURES_DIR / "comprehension_accuracy.pdf"
    png_path = FIGURES_DIR / "comprehension_accuracy.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Wrote:")
    print(f"  {pdf_path}")
    print(f"  {png_path}")


if __name__ == "__main__":
    main()
