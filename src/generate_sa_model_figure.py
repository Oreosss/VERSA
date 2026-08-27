"""Endsley's three-level Situational Awareness model, applied to vulnerability
comprehension, for the dissertation introduction.

Saves vector PDF (for \\includegraphics) and 300 dpi PNG to
figures/introduction/sa_model.
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

matplotlib.use("Agg")

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = Path("figures/introduction")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIG_WIDTH = 6.3  # inches, matches this project's other A4-text-width figures

# Muted, print-safe, flat colours -- no gradients, no shadows.
BLUE = "#3f6c9e"       # Level 1 and Level 3 (perception, projection)
WARM = "#c96a3e"       # Level 2 (comprehension) -- the failure point
EDGE = "#333333"       # flow arrows between stages
RED = "#a83232"        # breakdown annotation
TEAL = "#2f9e8f"       # callout accent, matches the tool's dashboard palette
TEAL_FILL = "#e6f4f2"
TEXT_ON_FILL = "#ffffff"
TEXT_PRIMARY = "#1a1a1a"


def stage_box(ax, cx, cy, w, h, level_line, quote_line, fill):
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.12",
        linewidth=0, facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(cx, cy + h * 0.19, level_line, ha="center", va="center",
             fontsize=9.8, color=TEXT_ON_FILL, weight="bold")
    ax.text(cx, cy - h * 0.20, quote_line, ha="center", va="center",
             fontsize=9, color=TEXT_ON_FILL, style="italic", linespacing=1.4)


def flow_arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=14,
        linewidth=1.3, color=EDGE, shrinkA=0, shrinkB=0,
    ))


def make_figure():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0.4, 7.4)
    ax.axis("off")

    y_box = 4.1
    box_w, box_h = 3.6, 1.5
    x1, x2, x3 = 2.0, 6.3, 10.6

    # --- three stages ---
    stage_box(ax, x1, y_box, box_w, box_h,
              "Level 1: Perception", "“A vulnerability record\nis seen”", BLUE)
    stage_box(ax, x2, y_box, box_w, box_h,
              "Level 2: Comprehension", "“Its meaning is\nsynthesised”", WARM)
    stage_box(ax, x3, y_box, box_w, box_h,
              "Level 3: Projection", "“Its impact is projected\nand acted on”", BLUE)

    # --- flow arrows between stages ---
    flow_arrow(ax, (x1 + box_w / 2, y_box), (x2 - box_w / 2, y_box))
    flow_arrow(ax, (x2 + box_w / 2, y_box), (x3 - box_w / 2, y_box))

    # --- teal callout, above, pointing down into Level 2 ---
    callout_w, callout_h = 6.6, 1.15
    callout_cy = 6.55
    callout = FancyBboxPatch(
        (x2 - callout_w / 2, callout_cy - callout_h / 2), callout_w, callout_h,
        boxstyle="round,pad=0.05,rounding_size=0.12",
        linewidth=1.4, edgecolor=TEAL, facecolor=TEAL_FILL,
    )
    ax.add_patch(callout)
    ax.text(x2, callout_cy, "Plain-language summary intervenes at Level 2",
             ha="center", va="center", fontsize=9.5, color=TEXT_PRIMARY, weight="bold")
    ax.add_patch(FancyArrowPatch(
        (x2, callout_cy - callout_h / 2), (x2, y_box + box_h / 2 + 0.08),
        arrowstyle="-|>", mutation_scale=13, linewidth=1.4, color=TEAL,
        shrinkA=0, shrinkB=0,
    ))

    # --- red breakdown annotation, below, pointing up into Level 2 ---
    annotation_y = 1.55
    ax.add_patch(FancyArrowPatch(
        (x2, annotation_y + 0.42), (x2, y_box - box_h / 2 - 0.08),
        arrowstyle="-|>", mutation_scale=12, linewidth=1.2, color=RED,
        shrinkA=0, shrinkB=0,
    ))
    ax.text(x2, annotation_y, "Breakdown occurs here:\nperceived but not understood",
             ha="center", va="center", fontsize=8.5, color=RED, weight="bold",
             linespacing=1.4)

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig


def main():
    fig = make_figure()
    pdf_path = OUT_DIR / "sa_model.pdf"
    png_path = OUT_DIR / "sa_model.png"
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {pdf_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
