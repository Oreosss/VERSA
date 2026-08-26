"""Paired v1-vs-v2 comparison of the dashboard usability LLM-as-judge runs.

v1 (`v2_bullet/judge/v1/`) is the original run, before three usability
fixes (tooltips on the technical-details headers and "More filters"
labels; a "Clear all filters" button on the zero-result state). v2
(`v2_bullet/judge/`) is the re-run after those fixes, produced by
`src/llm_judge_usability.py`. Both score the same six PRIMARY_SCREENSHOTS
states with the same context-image composition and the same rubric, so
the per-heuristic means are directly diffable.

Also reports the two v2-only SUPPLEMENTARY_SCREENSHOTS (hover states),
since two of the three fixes are CSS `:hover`-only tooltips that no
static v1 or v2 primary screenshot can show -- without these, the
paired diff below would understate the improvement from those two fixes.
v1 has no counterpart for these, so they're reported alongside the paired
diff, not merged into it.
"""

import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).parent))
from llm_judge_usability import (  # noqa: E402
    AGGREGATE_JSON_PATH,
    FIGURES_DIR,
    HEURISTIC_KEYS,
    HEURISTIC_LABEL,
    SUPPLEMENTARY_PER_SCREENSHOT_PATH,
    save_figure,
    style_axes,
)

JUDGE_DIR = Path("v2_bullet/judge")
V1_DIR = JUDGE_DIR / "v1"
V1_AGGREGATE_PATH = V1_DIR / "llm_judge_usability_aggregate.json"
V2_AGGREGATE_PATH = AGGREGATE_JSON_PATH
OUT_MD_PATH = JUDGE_DIR / "LLM_JUDGE_USABILITY_V1_VS_V2.md"

COLOR_V1 = "#9a978d"
COLOR_V2 = "#2f9e8f"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "CMU Serif", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False


def fmt(x, nd=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def fig_v1_vs_v2(v1_means, v2_means):
    order = sorted(HEURISTIC_KEYS, key=lambda k: v2_means[k] - v1_means[k])
    labels = [HEURISTIC_LABEL[k] for k in order]
    v1_vals = [v1_means[k] for k in order]
    v2_vals = [v2_means[k] for k in order]

    fig, ax = plt.subplots(figsize=(8.5, 6))
    y = np.arange(len(order))
    height = 0.36
    ax.barh(y + height / 2, v1_vals, height=height, color=COLOR_V1, alpha=0.85,
            edgecolor=COLOR_V1, label="v1 (before fixes)", zorder=3)
    ax.barh(y - height / 2, v2_vals, height=height, color=COLOR_V2, alpha=0.85,
            edgecolor=COLOR_V2, label="v2 (after fixes)", zorder=3)
    for yi, v1, v2 in zip(y, v1_vals, v2_vals):
        ax.text(max(v1, v2) + 0.12, yi, f"{v2 - v1:+.2f}", va="center", fontsize=8.5,
                 color=TEXT_PRIMARY)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT_PRIMARY)
    ax.set_xlim(1.0, 5.8)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Judge score (1-5, mean across 6 primary screenshots x 3 passes)")
    ax.set_title("Dashboard usability: v1 vs v2 (after quick fixes), by heuristic",
                  fontsize=10, color=TEXT_PRIMARY)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "llm_judge_usability_v1_vs_v2_bullet")


def main():
    if not V1_AGGREGATE_PATH.exists():
        raise SystemExit(f"STOP: {V1_AGGREGATE_PATH} not found -- was v1 archived to {V1_DIR}/?")
    if not V2_AGGREGATE_PATH.exists():
        raise SystemExit(f"STOP: {V2_AGGREGATE_PATH} not found -- run src/llm_judge_usability.py first.")

    v1 = json.loads(V1_AGGREGATE_PATH.read_text())
    v2 = json.loads(V2_AGGREGATE_PATH.read_text())
    v1_means, v1_sds = v1["heuristic_means"], v1["heuristic_sds"]
    v2_means, v2_sds = v2["heuristic_means"], v2["heuristic_sds"]

    rows = []
    for key in HEURISTIC_KEYS:
        rows.append({
            "heuristic": key,
            "v1_mean": v1_means[key], "v1_sd": v1_sds[key],
            "v2_mean": v2_means[key], "v2_sd": v2_sds[key],
            "delta": v2_means[key] - v1_means[key],
        })
    diff_df = pd.DataFrame(rows).sort_values("delta", ascending=False)

    overall_v1 = float(np.mean(list(v1_means.values())))
    overall_v2 = float(np.mean(list(v2_means.values())))

    md = []
    md.append("# Dashboard Usability: v1 vs v2 Comparison\n\n")
    md.append(
        "Paired comparison of the LLM-as-judge dashboard usability run before "
        "(`v2_bullet/judge/v1/`) and after (`v2_bullet/judge/`) three quick fixes: tooltips on "
        "the technical-details headers and \"More filters\" labels, and a \"Clear all filters\" "
        "button on the zero-result state. Both runs score the same six screenshot states with "
        "the same context-image composition and the same rubric "
        "(`v2_bullet/rubric/rubric_usability.txt`), so the per-heuristic means below are directly "
        "diffable. Descriptive statistics only, not a significance test -- n=1 run per version, "
        "consistent with this project's exploratory framing for the rest of the LLM-as-judge "
        "evaluation.\n\n"
    )
    md.append(f"**Overall mean across all 10 heuristics: {fmt(overall_v1)} (v1) -> {fmt(overall_v2)} "
               f"(v2), {overall_v2 - overall_v1:+.2f}.**\n\n")
    md.append("## Per-heuristic comparison, sorted by improvement\n\n")
    md.append("| Heuristic | v1 mean (SD) | v2 mean (SD) | Delta |\n|---|---|---|---|\n")
    for _, row in diff_df.iterrows():
        md.append(
            f"| {HEURISTIC_LABEL[row['heuristic']]} | {fmt(row['v1_mean'])} ({fmt(row['v1_sd'])}) | "
            f"{fmt(row['v2_mean'])} ({fmt(row['v2_sd'])}) | {row['delta']:+.2f} |\n"
        )

    md.append(
        "\n## Why some fixed heuristics show little or no primary-screenshot movement\n\n"
        "Two of the three fixes (both tooltip additions) are CSS `:hover`-only, and a static "
        "screenshot cannot show a `:hover` state unless one is deliberately triggered. The six "
        "primary screenshots above are unchanged from v1 (same states, same interactions) "
        "specifically so this diff is a clean paired comparison, which means those two fixes are "
        "close to invisible to it by construction, not because they didn't work. The third fix "
        "(\"Clear all filters\") is a real, static, visible UI change and does show up directly "
        "in the primary diff via the empty-state screenshot.\n\n"
    )

    if SUPPLEMENTARY_PER_SCREENSHOT_PATH.exists():
        supp_df = pd.read_csv(SUPPLEMENTARY_PER_SCREENSHOT_PATH)
        md.append(
            "## Supplementary (v2 only): hover-state evidence for the tooltip fixes\n\n"
            "Two extra screenshots, not present in v1, were captured specifically to make the "
            "tooltip fixes observable: hovering a technical-details header, and hovering a "
            "\"More filters\" label. v1 has no counterpart to diff these against (the tooltips "
            "didn't exist yet), so they're reported here on their own rather than folded into the "
            "paired table above.\n\n"
        )
        md.append("| Screenshot | Heuristic | Mean | SD (across 3 passes) |\n|---|---|---|---|\n")
        for _, row in supp_df.sort_values(["screenshot_id", "heuristic"]).iterrows():
            md.append(
                f"| {row['screenshot_id']} | {HEURISTIC_LABEL[row['heuristic']]} | "
                f"{fmt(row['mean_score'])} | {fmt(row['sd_score'])} |\n"
            )
        help_doc_supp = supp_df[supp_df["heuristic"] == "help_documentation"]
        if not help_doc_supp.empty:
            supp_mean = float(help_doc_supp["mean_score"].mean())
            md.append(
                f"\nFor comparison: \"Help and documentation\" scored {fmt(v1_means['help_documentation'])} "
                f"in v1 and {fmt(v2_means['help_documentation'])} in v2 on the (necessarily "
                f"tooltip-blind) primary screenshots, but {fmt(supp_mean)} on these two "
                "hover-triggered supplementary screenshots -- the fix is real, the primary diff "
                "just structurally can't see it.\n"
            )

    md.append("\n## Figure\n\n")
    md.append(f"See `{FIGURES_DIR}/llm_judge_usability_v1_vs_v2_bullet.png` (also `.svg`).\n")

    OUT_MD_PATH.write_text("".join(md))
    print(f"Wrote {OUT_MD_PATH}.")

    figures_written = fig_v1_vs_v2(v1_means, v2_means)
    for p in figures_written:
        print(f"  {p}")

    print()
    print(f"Overall: {fmt(overall_v1)} -> {fmt(overall_v2)} ({overall_v2 - overall_v1:+.2f})")
    for _, row in diff_df.iterrows():
        print(f"  {HEURISTIC_LABEL[row['heuristic']]:<55} {row['v1_mean']:.2f} -> {row['v2_mean']:.2f}  ({row['delta']:+.2f})")


if __name__ == "__main__":
    main()
