"""Standalone comprehension-only figure, split out from the combined
comprehension+faithfulness panel (`llm_judge_scores_bullet`) produced by
`src/llm_judge.py`.

No new judge calls: reads the comprehension rows already computed in
`v2_bullet/judge/llm_judge_per_text.csv` (Stage 6e) and re-plots just that
dimension on its own, using the same style (colours, serif font, bar +
error-bar) as `src/llm_judge.py`'s current figure so it sits visually
consistent with the rest of the dissertation's figures.
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "CMU Serif", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False

PER_TEXT_PATH = "v2_bullet/judge/llm_judge_per_text.csv"
FIGURES_DIR = Path("v2_bullet/figures")

COLOR_NVD = "#2a78d6"
COLOR_PERSONA = "#008300"
COLOR_BASELINE = "#4a3aa7"
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

ARM_DISPLAY = {"nvd": "Raw NVD", "persona": "Persona", "baseline": "Baseline"}
ARM_COLOR = {"nvd": COLOR_NVD, "persona": COLOR_PERSONA, "baseline": COLOR_BASELINE}
FIGURE_ARM_ORDER = ("persona", "baseline", "nvd")


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)


def save_figure(fig, name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / f"{name}.png"
    svg_path = FIGURES_DIR / f"{name}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    return [str(png_path), str(svg_path)]


def main():
    df = pd.read_csv(PER_TEXT_PATH)
    comp = df[df["dimension"] == "comprehension"]

    stats = {}
    for arm in FIGURE_ARM_ORDER:
        arr = comp.loc[comp["arm"] == arm, "mean_score"].to_numpy(dtype=float)
        stats[arm] = {
            "mean": float(np.mean(arr)),
            "sd": float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan"),
        }

    # See src/llm_judge.py's fig_judge_scores for why ylim extends past 5.0
    # (headroom for ceiling-bar labels) while ticks stay pinned to 1-5.
    y_lo, y_hi = 1.0, 5.35

    fig, ax = plt.subplots(figsize=(5, 4.5))
    x = np.arange(len(FIGURE_ARM_ORDER))
    means = [stats[arm]["mean"] for arm in FIGURE_ARM_ORDER]
    sds = [stats[arm]["sd"] for arm in FIGURE_ARM_ORDER]
    colors = [ARM_COLOR[arm] for arm in FIGURE_ARM_ORDER]
    bars = ax.bar(x, means, width=0.55, yerr=sds, capsize=3, color=colors, alpha=0.75, edgecolor=colors, zorder=3)
    for bar, mean, sd in zip(bars, means, sds):
        top_of_errorbar = mean + (sd if not np.isnan(sd) else 0.0)
        ax.text(bar.get_x() + bar.get_width() / 2, top_of_errorbar + 0.08, f"{mean:.2f}",
                 ha="center", va="bottom", fontsize=9, color=TEXT_PRIMARY)
    ax.set_xticks(x)
    ax.set_xticklabels([ARM_DISPLAY[arm] for arm in FIGURE_ARM_ORDER])
    ax.set_ylim(y_lo, y_hi)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel("Judge score (1-5, mean of 3 passes)")
    ax.set_title("Comprehension support, by text", fontsize=11, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()

    print("Comprehension means and SDs (n=24 per arm):")
    for arm in FIGURE_ARM_ORDER:
        s = stats[arm]
        print(f"  {ARM_DISPLAY[arm]:<10} mean={s['mean']:.2f}  sd={s['sd']:.2f}")

    written = save_figure(fig, "llm_judge_comprehension_bullet")
    print("Wrote:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
