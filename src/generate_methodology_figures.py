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


# ---------------------------------------------------------------------------
# Figure 3: dashboard UI workflow
# ---------------------------------------------------------------------------

def side_arrow(ax, p0, p1, rad, label=None, label_pos=None):
    """Curved arrow for the two loop-back paths, offset to the right of the
    main column so they read as returns to an earlier state rather than
    another step in the linear flow."""
    a = FancyArrowPatch(
        p0,
        p1,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.1,
        color=EDGE,
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(a)
    if label:
        lx, ly = label_pos
        ax.text(lx, ly, label, ha="left", va="center", fontsize=7.5,
                color=SUBTEXT, style="italic")


def make_ui_workflow():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 9.6))
    cx = 5.0
    ax.set_xlim(0, 11.6)
    ax.set_ylim(0, 15.2)
    ax.axis("off")

    y_list = 14.0
    y_select = 11.9
    y_lookup = 9.8
    y_branch = 7.3
    y_detail = 4.4

    w_wide = 6.6
    w_narrow = 4.6
    w_branch = 4.6
    h_std = 1.05
    h_branch = 1.55
    h_detail = 2.05

    # List view
    draw_box(
        ax, cx, y_list, w_wide, h_std,
        ["List view", "browse • filter • search • sort  —  11,976-CVE corpus"],
        [10.5, 8.5],
        DATA_FILL,
        weight="bold",
    )

    # Select a CVE
    draw_box(
        ax, cx, y_select, w_narrow, h_std,
        ["Select a CVE", "“Explain” on a row, or a Similar-CVE card"],
        [10, 8],
        PROCESS_FILL,
        dashed=True,
        weight="bold",
    )

    # Cache lookup
    draw_box(
        ax, cx, y_lookup, w_narrow, h_std,
        ["Cache lookup", "get_or_generate(cve_id)"],
        [10, 8.5],
        PROCESS_FILL,
        dashed=True,
        weight="bold",
    )

    # Branch: cache hit (left) vs generate on demand (right)
    x_left, x_right = cx - 2.4, cx + 2.4
    draw_box(
        ax, x_left, y_branch, w_branch, h_branch,
        ["Cache hit", "load stored summary"],
        [9.5, 8],
        DATA_FILL,
        weight="bold",
    )
    draw_box(
        ax, x_right, y_branch, w_branch, h_branch,
        ["Cache miss — generate",
         "ChromaDB k-NN retrieval → prompt →",
         "Claude LLM call → parse → write cache"],
        [9.5, 7.5, 7.5],
        PROCESS_FILL,
        dashed=True,
        weight="bold",
    )

    # Detail view
    draw_box(
        ax, cx, y_detail, w_wide, h_detail,
        ["Detail view",
         "3-part plain-language summary (vulnerable / exploited / action)",
         "similar CVEs  •  raw NVD comparison  •  CWE, technical context, references"],
        [10.5, 8, 8],
        DATA_FILL,
        weight="bold",
    )

    # --- main-column arrows ---
    arrow(ax, (cx, y_list - h_std / 2), (cx, y_select + h_std / 2))
    arrow(ax, (cx, y_select - h_std / 2), (cx, y_lookup + h_std / 2))
    arrow(ax, (cx, y_lookup - h_std / 2), (x_left, y_branch + h_branch / 2))
    arrow(ax, (cx, y_lookup - h_std / 2), (x_right, y_branch + h_branch / 2))
    arrow(ax, (x_left, y_branch - h_branch / 2), (cx - w_wide / 2 + 0.4, y_detail + h_detail / 2))
    arrow(ax, (x_right, y_branch - h_branch / 2), (cx + w_wide / 2 - 0.4, y_detail + h_detail / 2))

    # --- loop-back arrows (right-hand side, outside the main boxes' footprint) ---
    x_edge = cx + w_wide / 2  # right edge shared by List view and Detail view
    side_arrow(
        ax,
        (x_edge, y_detail + h_detail / 2 - 0.15),
        (cx + w_narrow / 2, y_select + 0.1),
        rad=0.65,
        label="clicking a\nSimilar-CVE card",
        label_pos=(x_edge + 0.15, y_lookup + 0.1),
    )
    side_arrow(
        ax,
        (x_edge, y_detail - h_detail / 2 + 0.2),
        (x_edge, y_list - 0.1),
        rad=0.45,
        label="“Back to list”",
        label_pos=(x_edge + 1.2, y_list - 1.55),
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

    fig3 = make_ui_workflow()
    p3_pdf, p3_png = save(fig3, "ui_workflow")
    w3, h3 = fig3.get_size_inches()

    print(f"pipeline_flow: figsize {w1:.2f}in x {h1:.2f}in (pre-crop)")
    print(f"  {p1_pdf}")
    print(f"  {p1_png}")
    print(f"eval_matrix: figsize {w2:.2f}in x {h2:.2f}in (pre-crop)")
    print(f"  {p2_pdf}")
    print(f"  {p2_png}")
    print(f"ui_workflow: figsize {w3:.2f}in x {h3:.2f}in (pre-crop)")
    print(f"  {p3_pdf}")
    print(f"  {p3_png}")
