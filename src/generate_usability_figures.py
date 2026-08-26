"""Dissertation figures for the dashboard usability (LLM-as-judge) section.

Figure 1 (usability_heuristics.png): mean judge score per Nielsen heuristic,
v1 run (baseline, before the three usability fixes) -- companion to Table 4.4.
Figure 2 (usability_before_after.png): v1 vs v2 (after fixes) grouped
comparison, ordered by improvement -- companion to Table 4.5.

Reads both aggregate files directly rather than hardcoding scores. No title
inside either figure; the caption handles it. British spelling in labels.
"""

import json
import textwrap
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "CMU Serif", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False

V1_AGGREGATE_PATH = Path("v2_bullet/judge/v1/llm_judge_usability_aggregate.json")
V2_AGGREGATE_PATH = Path("v2_bullet/judge/llm_judge_usability_aggregate.json")
FIGURES_DIR = Path("figures/usability")

COLOR_BAR = "#2f9e8f"
COLOR_BEFORE = "#9a978d"
COLOR_AFTER = "#2f9e8f"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

# British spelling, matching the project's writing convention.
HEURISTIC_LABEL = {
    "visibility_of_system_status": "Visibility of system status",
    "match_real_world": "Match between system and the real world",
    "user_control_freedom": "User control and freedom",
    "consistency_standards": "Consistency and standards",
    "error_prevention": "Error prevention",
    "recognition_not_recall": "Recognition rather than recall",
    "flexibility_efficiency": "Flexibility and efficiency of use",
    "aesthetic_minimalist": "Aesthetic and minimalist design",
    "error_recovery": "Help users recognise, diagnose, and recover from errors",
    "help_documentation": "Help and documentation",
}

# Table 4.5 order (by improvement, v1 -> v2).
IMPROVEMENT_ORDER = [
    "error_recovery",
    "match_real_world",
    "recognition_not_recall",
    "visibility_of_system_status",
    "user_control_freedom",
    "consistency_standards",
    "error_prevention",
    "flexibility_efficiency",
    "aesthetic_minimalist",
    "help_documentation",
]


def wrap(label, width=26):
    return textwrap.fill(label, width=width)


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.xaxis.grid(True, color="#e1e0d9", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.yaxis.grid(False)


def save_png(fig, name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / f"{name}.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return png_path


def fig_usability_heuristics(means):
    order = sorted(HEURISTIC_LABEL, key=lambda k: means[k])
    labels = [wrap(HEURISTIC_LABEL[k]) for k in order]
    values = [means[k] for k in order]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    y = range(len(order))
    bars = ax.barh(list(y), values, color=COLOR_BAR, edgecolor=COLOR_BAR,
                    alpha=0.85, height=0.6, zorder=3)
    for bar, value in zip(bars, values):
        ax.text(value + 0.08, bar.get_y() + bar.get_height() / 2, f"{value:.2f}",
                va="center", fontsize=9, color=TEXT_PRIMARY)

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9, color=TEXT_PRIMARY)
    ax.set_xlim(0, 5)
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.set_xlabel("Mean judge score (1-5, 6 screenshots x 3 passes)")
    style_axes(ax)
    fig.tight_layout()
    return save_png(fig, "usability_heuristics")


def fig_usability_before_after(v1_means, v2_means):
    order = IMPROVEMENT_ORDER
    labels = [wrap(HEURISTIC_LABEL[k]) for k in order]
    before_vals = [v1_means[k] for k in order]
    after_vals = [v2_means[k] for k in order]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    y = list(range(len(order)))
    height = 0.35
    ax.barh([yi + height / 2 for yi in y], before_vals, height=height,
            color=COLOR_BEFORE, edgecolor=COLOR_BEFORE, alpha=0.85,
            label="Before fixes (v1)", zorder=3)
    ax.barh([yi - height / 2 for yi in y], after_vals, height=height,
            color=COLOR_AFTER, edgecolor=COLOR_AFTER, alpha=0.85,
            label="After fixes (v2)", zorder=3)

    for yi, before, after in zip(y, before_vals, after_vals):
        delta = after - before
        delta_color = TEXT_PRIMARY if abs(delta) > 1e-9 else TEXT_SECONDARY
        ax.text(max(before, after) + 0.1, yi, f"{delta:+.2f}", va="center",
                fontsize=8.5, color=delta_color)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT_PRIMARY)
    ax.invert_yaxis()  # top row (largest improvement) at the top, matching Table 4.5
    ax.set_xlim(0, 5)
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.set_xlabel("Mean judge score (1-5, 6 screenshots x 3 passes)")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    style_axes(ax)
    fig.tight_layout()
    return save_png(fig, "usability_before_after")


def main():
    if not V1_AGGREGATE_PATH.exists():
        raise SystemExit(f"STOP: {V1_AGGREGATE_PATH} not found.")
    if not V2_AGGREGATE_PATH.exists():
        raise SystemExit(f"STOP: {V2_AGGREGATE_PATH} not found.")

    v1 = json.loads(V1_AGGREGATE_PATH.read_text())["heuristic_means"]
    v2 = json.loads(V2_AGGREGATE_PATH.read_text())["heuristic_means"]

    p1 = fig_usability_heuristics(v1)
    p2 = fig_usability_before_after(v1, v2)
    print(f"Wrote {p1}")
    print(f"Wrote {p2}")


if __name__ == "__main__":
    main()
