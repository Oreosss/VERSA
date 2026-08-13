"""
Generate the two methodology-chapter figures (pipeline flow, eval sampling matrix).
Saves vector PDF + 300 dpi PNG to figures/methodology/.
"""

import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "figures", "methodology")
os.makedirs(OUT_DIR, exist_ok=True)

# Serif font to sit closer to LaTeX body text, with fallbacks.
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = [
    "Times New Roman",
    "Times",
    "CMU Serif",
    "DejaVu Serif",
]
plt.rcParams["axes.unicode_minus"] = False

FIG_WIDTH = 6.3  # inches, A4 text width

# Restrained, print-friendly greyscale palette.
DATA_FILL = "#eeeeee"
PROCESS_FILL = "#ffffff"
EDGE = "#333333"
TEXT = "#1a1a1a"
SUBTEXT = "#444444"


def save(fig, name):
    pdf_path = os.path.join(OUT_DIR, f"{name}.pdf")
    png_path = os.path.join(OUT_DIR, f"{name}.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def draw_box(ax, cx, cy, w, h, lines, sizes, fill, dashed=False, weight="normal"):
    style = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.06,rounding_size=0.08",
        linewidth=1.1,
        edgecolor=EDGE,
        facecolor=fill,
        linestyle="dashed" if dashed else "solid",
    )
    ax.add_patch(style)

    n = len(lines)
    # Distribute lines vertically within the box, first line slightly above centre.
    if n == 1:
        offsets = [0]
    else:
        span = h * 0.32
        offsets = [span - i * (2 * span / (n - 1)) for i in range(n)]

    for line, size, off in zip(lines, sizes, offsets):
        ax.text(
            cx,
            cy + off,
            line,
            ha="center",
            va="center",
            fontsize=size,
            color=TEXT,
            weight=weight if size == sizes[0] else "normal",
        )


def arrow(ax, p0, p1):
    a = FancyArrowPatch(
        p0,
        p1,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.1,
        color=EDGE,
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(a)


# ---------------------------------------------------------------------------
# Figure 1: pipeline flow
# ---------------------------------------------------------------------------

def make_pipeline_flow():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 8.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 15.5)
    ax.axis("off")

    # --- levels (top to bottom) ---
    y_raw = 14.6
    y_gate = 12.4
    y_pool = 10.4
    y_branch = 7.9
    y_merge = 5.2
    y_final = 3.0

    w_wide = 6.3
    w_narrow = 4.6
    w_branch = 4.3
    h_std = 1.05
    h_gate = 1.7
    h_merge = 1.35

    # Raw NVD feeds
    draw_box(
        ax, 5, y_raw, w_wide, h_std,
        ["Raw NVD annual feeds, 2020–2026", "n = 213,085 records"],
        [10.5, 8.5],
        DATA_FILL,
        weight="bold",
    )

    # Filter gate (single process step, no intermediate counts)
    w_gate = 7.6
    draw_box(
        ax, 5, y_gate, w_gate, h_gate,
        [
            "Filter gate",
            "CVSS v3.1 present  •  description ≥ 100 characters  •  ≥ 1 CPE entry",
        ],
        [9.5, 8.5],
        PROCESS_FILL,
        dashed=True,
        weight="bold",
    )

    # Filtered pool
    draw_box(
        ax, 5, y_pool, w_narrow, h_std,
        ["Filtered pool", "n = 156,084 records"],
        [10.5, 8.5],
        DATA_FILL,
        weight="bold",
    )

    # Branch: retrieval corpus (left) and evaluation sample (right)
    x_left, x_right = 2.6, 7.4
    draw_box(
        ax, x_left, y_branch, w_branch, 1.5,
        ["Retrieval corpus", "proportional stratified sample", "n = 12,000 records"],
        [9.5, 7.5, 8.5],
        DATA_FILL,
        weight="bold",
    )
    draw_box(
        ax, x_right, y_branch, w_branch, 1.5,
        ["Evaluation sample", "purposive 3×2 matrix", "n = 24 CVEs"],
        [9.5, 7.5, 8.5],
        DATA_FILL,
        weight="bold",
    )

    # Removal / merge step
    draw_box(
        ax, 5, y_merge, w_narrow + 0.3, h_merge,
        ["Remove evaluation CVEs from corpus", "12,000 − 24"],
        [9.5, 8],
        PROCESS_FILL,
        dashed=True,
        weight="bold",
    )

    # Final indexed corpus
    draw_box(
        ax, 5, y_final, w_wide - 0.4, h_std,
        ["Indexed ChromaDB corpus (embedded descriptions)", "n = 11,976 records"],
        [10, 8.5],
        DATA_FILL,
        weight="bold",
    )

    # --- arrows ---
    arrow(ax, (5, y_raw - h_std / 2), (5, y_gate + h_gate / 2))
    arrow(ax, (5, y_gate - h_gate / 2), (5, y_pool + h_std / 2))

    # branch out of filtered pool
    arrow(ax, (5, y_pool - h_std / 2), (x_left, y_branch + 1.5 / 2))
    arrow(ax, (5, y_pool - h_std / 2), (x_right, y_branch + 1.5 / 2))

    # rejoin into removal step
    arrow(ax, (x_left, y_branch - 1.5 / 2), (5 - (w_narrow + 0.3) / 2 + 0.4, y_merge + h_merge / 2))
    arrow(ax, (x_right, y_branch - 1.5 / 2), (5 + (w_narrow + 0.3) / 2 - 0.4, y_merge + h_merge / 2))

    arrow(ax, (5, y_merge - h_merge / 2), (5, y_final + h_std / 2))

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig


# ---------------------------------------------------------------------------
# Figure 2: evaluation sampling matrix
# ---------------------------------------------------------------------------

def make_eval_matrix():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.2)
    ax.axis("off")

    rows = ["CRITICAL", "HIGH", "MEDIUM"]
    cols = ["Lower exploitability", "Higher exploitability"]
    cell_letters = [["A", "B"], ["C", "D"], ["E", "F"]]

    row_label_w = 2.0
    grid_x0 = row_label_w
    grid_w = 10 - row_label_w
    col_w = grid_w / 2
    col_header_h = 0.9
    grid_top = 7.7
    grid_bottom = 1.6
    row_h = (grid_top - col_header_h - grid_bottom) / 3

    # Column headers
    for j, col in enumerate(cols):
        cx = grid_x0 + col_w * (j + 0.5)
        ax.text(
            cx, grid_top - col_header_h / 2, col,
            ha="center", va="center", fontsize=10.5, color=TEXT, weight="bold",
        )

    grid_top_cells = grid_top - col_header_h

    for i, row in enumerate(rows):
        cy = grid_top_cells - row_h * (i + 0.5)
        # Row label
        ax.text(
            row_label_w / 2, cy, row,
            ha="center", va="center", fontsize=10, color=TEXT, weight="bold",
        )
        for j in range(2):
            cx = grid_x0 + col_w * (j + 0.5)
            rect = FancyBboxPatch(
                (grid_x0 + col_w * j + 0.08, cy - row_h / 2 + 0.08),
                col_w - 0.16,
                row_h - 0.16,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                linewidth=1.1,
                edgecolor=EDGE,
                facecolor=DATA_FILL,
            )
            ax.add_patch(rect)
            ax.text(
                cx, cy + 0.18, cell_letters[i][j],
                ha="center", va="center", fontsize=17, color=TEXT, weight="bold",
            )
            ax.text(
                cx, cy - 0.32, "4 CVEs",
                ha="center", va="center", fontsize=9, color=SUBTEXT,
            )

    # Definition line beneath the grid
    def_y1 = 0.85
    def_y2 = 0.35
    ax.text(
        5, def_y1,
        "Higher exploitability: EPSS ≥ 0.5 or KEV-listed.   Lower exploitability: EPSS < 0.5 and not KEV-listed.",
        ha="center", va="center", fontsize=8.5, color=SUBTEXT,
    )
    ax.text(
        5, def_y2,
        "All 12 higher-exploitability records are KEV-listed.",
        ha="center", va="center", fontsize=8.5, color=SUBTEXT,
    )

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig


if __name__ == "__main__":
    fig1 = make_pipeline_flow()
    p1_pdf, p1_png = save(fig1, "pipeline_flow")
    w1, h1 = fig1.get_size_inches()

    fig2 = make_eval_matrix()
    p2_pdf, p2_png = save(fig2, "eval_matrix")
    w2, h2 = fig2.get_size_inches()

    print(f"pipeline_flow: figsize {w1:.2f}in x {h1:.2f}in (pre-crop)")
    print(f"  {p1_pdf}")
    print(f"  {p1_png}")
    print(f"eval_matrix: figsize {w2:.2f}in x {h2:.2f}in (pre-crop)")
    print(f"  {p2_pdf}")
    print(f"  {p2_png}")
