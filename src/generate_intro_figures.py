"""Generate standalone dissertation figures for the introduction/motivation section.

Figure 1: annual reported CVE growth (2024-2026, 2026 projected).
Figure 2: NVD enrichment shortfall for newly reported vulnerabilities.

Both figures are saved as vector PDFs (for the dissertation) and 300 DPI
PNGs (for slides/docs) to figures/.
"""

import matplotlib.pyplot as plt

# Muted, print-safe colours (blue = actual/primary, lighter blue = projected).
COLOR_ACTUAL = "#2a78d6"
COLOR_PROJECTED = "#9ec5f4"
COLOR_ENRICHED = "#2a78d6"
COLOR_NOT_ENRICHED = "#eb6834"
COLOR_INK = "#0b0b0b"
COLOR_MUTED = "#52514e"
COLOR_BASELINE = "#c3c2b7"

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": COLOR_BASELINE,
    "axes.labelcolor": COLOR_INK,
    "xtick.color": COLOR_MUTED,
    "ytick.color": COLOR_MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "sans-serif",
})


def make_fig1():
    years = ["2024", "2025", "2026"]
    values = [40009, 48185, 59427]
    colors = [COLOR_ACTUAL, COLOR_ACTUAL, COLOR_PROJECTED]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        years,
        values,
        color=colors,
        edgecolor=COLOR_INK,
        linewidth=0.5,
        width=0.6,
        zorder=3,
    )
    # Hatch the projected bar so it reads clearly in greyscale print.
    bars[2].set_hatch("//")
    bars[2].set_edgecolor(COLOR_MUTED)

    ax.set_ylim(0, 76000)
    ax.set_ylabel("Reported CVEs")
    ax.set_xlabel("Year")

    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:,}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLOR_INK,
        )

    # Annotate 2026 as first year projected to cross 50,000. Placed in the
    # empty margin above the bar, clear of both the value label and the fill.
    ax.annotate(
        "First year projected\nto exceed 50,000",
        xy=(bars[2].get_x() + bars[2].get_width() / 2, 70000),
        ha="center",
        va="center",
        fontsize=8,
        color=COLOR_MUTED,
    )

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=COLOR_ACTUAL, edgecolor=COLOR_INK, linewidth=0.5),
        plt.Rectangle((0, 0), 1, 1, facecolor=COLOR_PROJECTED, edgecolor=COLOR_MUTED, linewidth=0.5, hatch="//"),
    ]
    ax.legend(
        legend_handles,
        ["Actual", "Projected"],
        frameon=False,
        loc="upper left",
        fontsize=9,
    )

    ax.grid(False)
    fig.tight_layout()
    out_path = "figures/fig1_1_cve_growth.pdf"
    fig.savefig(out_path, bbox_inches="tight")
    fig.savefig(out_path.replace(".pdf", ".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out_path


def make_fig2():
    categories = ["Enriched", "Not sufficiently\nenriched"]
    values = [17.5, 82.5]
    colors = [COLOR_ENRICHED, COLOR_NOT_ENRICHED]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        categories,
        values,
        color=colors,
        edgecolor=COLOR_INK,
        linewidth=0.5,
        width=0.5,
        zorder=3,
    )

    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage of newly reported vulnerabilities")

    ax.annotate(
        "15–20%",
        xy=(bars[0].get_x() + bars[0].get_width() / 2, bars[0].get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color=COLOR_INK,
    )
    ax.annotate(
        f"{values[1]:.1f}%",
        xy=(bars[1].get_x() + bars[1].get_width() / 2, bars[1].get_height()),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color=COLOR_INK,
    )

    ax.grid(False)
    fig.tight_layout()
    out_path = "figures/fig1_1_enrichment_gap.pdf"
    fig.savefig(out_path, bbox_inches="tight")
    fig.savefig(out_path.replace(".pdf", ".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    p1 = make_fig1()
    p2 = make_fig2()
    print(p1)
    print(p2)
