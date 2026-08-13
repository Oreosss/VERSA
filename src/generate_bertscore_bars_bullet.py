"""Generate the BERTScore grouped bar chart (mean +/- SD, persona vs. baseline)
for the v2 bullet-format run. Companion to the existing BERTScore box plot
(`bertscore_persona_vs_baseline_bullet`, produced by src/compute_metrics_bullet.py);
this one shows means with error bars and printed values instead of distributions,
since the finding here is that the two arms are near-identical and the box plot
alone doesn't make the exact numbers legible.

Reads v2_bullet/metrics/metrics_per_summary_bullet.csv (already computed by
compute_metrics_bullet.py) -- no metrics are recomputed here.
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

METRICS_CSV = "v2_bullet/metrics/metrics_per_summary_bullet.csv"
FIGURES_DIR = Path("v2_bullet/figures")

# Same palette as the other v2_bullet figures (src/compute_metrics_bullet.py).
COLOR_PERSONA = "#008300"   # green
COLOR_BASELINE = "#4a3aa7"  # violet
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"


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
    png_path = FIGURES_DIR / f"{name}_bullet.png"
    svg_path = FIGURES_DIR / f"{name}_bullet.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    return [str(png_path), str(svg_path)]


def main():
    df = pd.read_csv(METRICS_CSV)

    metrics = ["bertscore_f1", "bertscore_precision"]
    metric_labels = ["BERTScore F1", "BERTScore precision"]

    stats = {}
    for arm in ["persona", "baseline"]:
        sub = df.loc[df["arm"] == arm]
        for metric in metrics:
            stats[(arm, metric)] = {
                "mean": float(sub[metric].mean()),
                "sd": float(sub[metric].std(ddof=1)),
            }

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    x = np.arange(len(metrics))
    width = 0.32

    for offset, arm, color in [
        (-width / 2, "persona", COLOR_PERSONA),
        (width / 2, "baseline", COLOR_BASELINE),
    ]:
        means = [stats[(arm, m)]["mean"] for m in metrics]
        sds = [stats[(arm, m)]["sd"] for m in metrics]
        bars = ax.bar(
            x + offset,
            means,
            width=width,
            yerr=sds,
            capsize=3,
            color=color,
            alpha=0.75,
            edgecolor=color,
            label=arm.capitalize(),
            zorder=3,
        )
        for bar, mean in zip(bars, means):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"{mean:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                color=TEXT_PRIMARY,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score (mean ± SD)")
    ax.set_title("BERTScore, by prompt condition", fontsize=11, color=TEXT_PRIMARY)
    ax.legend(frameon=False, fontsize=9)
    style_axes(ax)
    fig.tight_layout()

    figures_written = save_figure(fig, "bertscore_bars_persona_vs_baseline")

    print("Figures written:")
    for p in figures_written:
        print(f"  {p}")
    print()
    print("Persona BERTScore F1:        mean={:.4f}  sd={:.4f}".format(
        stats[("persona", "bertscore_f1")]["mean"], stats[("persona", "bertscore_f1")]["sd"]
    ))
    print("Baseline BERTScore F1:       mean={:.4f}  sd={:.4f}".format(
        stats[("baseline", "bertscore_f1")]["mean"], stats[("baseline", "bertscore_f1")]["sd"]
    ))
    print("Persona BERTScore precision:  mean={:.4f}  sd={:.4f}".format(
        stats[("persona", "bertscore_precision")]["mean"], stats[("persona", "bertscore_precision")]["sd"]
    ))
    print("Baseline BERTScore precision: mean={:.4f}  sd={:.4f}".format(
        stats[("baseline", "bertscore_precision")]["mean"], stats[("baseline", "bertscore_precision")]["sd"]
    ))


if __name__ == "__main__":
    main()
