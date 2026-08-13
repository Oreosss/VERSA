"""
Fresh analysis of the human comprehension study at n=18 raw responses (up from
the n=15/17 used in HUMAN_STUDY_FINDINGS.md / HUMAN_STUDY_DEMOGRAPHICS.md).

Works only from the three derived CSVs in data/human_study/ (response_summary.csv,
comprehension_long.csv, likert_long.csv), which src/analyze_human_study.py
regenerates from the raw Qualtrics exports. Does not read or assume anything
from the prior write-ups.

Population definition (fixed by the brief, not re-derived here):
    - Exclude S1=No entirely (outside the thesis's target population).
    - Primary group: S1=Yes AND S2=No (technical, no formal security training).
    - Contrast group: S1=Yes AND S2=Yes.
    - "Analysis sample" = S1=Yes respondents who answered at least one item.

Question-type mapping (verified against data/human_study/survey_source.txt,
not assumed): Q1 always asks which component/software is affected ("what's
vulnerable"), Q2 always asks what an attacker needs/does ("how exploited"),
Q3 always asks about affected/fixed versions ("what action to take" /
remediation) -- this matches the thesis's three-part summary structure for
every one of the 12 CVEs.

Outputs:
    data/human_study/18p_tables/*.csv   -- one CSV per table below
    figures/human_study_18p/*.png       -- one PNG per figure below
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_human_study import BLOCK_SLOTS  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "CMU Serif", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "human_study"
TABLES_DIR = DATA_DIR / "18p_tables"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures" / "human_study_18p"

COLOR_RAW = "#8c8c88"
COLOR_SUMMARY = "#4a6fa5"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

QUESTION_TYPE = {1: "what_vulnerable", 2: "how_exploited", 3: "remediation"}
QUESTION_TYPE_LABEL = {
    "what_vulnerable": "Q1: what's vulnerable",
    "how_exploited": "Q2: how exploited",
    "remediation": "Q3: what action to take",
}

SLOT_MAP = {
    (block, cve): i + 1
    for block, entries in BLOCK_SLOTS.items()
    for i, (_, cve) in enumerate(entries)
}

RUSHED_RESPONSE_IDS = {"R_3dWEiMCm5OvAjyG"}  # see integrity-check section: >4x faster than the next-fastest full block

N_BOOT = 10000
RNG = np.random.default_rng(42)


def clearer_bound(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def bootstrap_condition_gap(comp: pd.DataFrame, group_col: str = None, group_val=None, n_boot: int = N_BOOT):
    """Bootstrap CI for (Summary accuracy - NVD accuracy), resampling respondents with replacement."""
    df = comp if group_col is None else comp[comp[group_col] == group_val]
    resp_ids = df["response_id"].unique()
    if len(resp_ids) < 2:
        return None
    by_resp = {rid: df[df["response_id"] == rid] for rid in resp_ids}

    point_nvd = df.loc[df["condition"] == "NVD", "is_correct"].mean()
    point_summary = df.loc[df["condition"] == "Summary", "is_correct"].mean()
    point_gap = point_summary - point_nvd

    diffs = np.empty(n_boot)
    for b in range(n_boot):
        sample_ids = RNG.choice(resp_ids, size=len(resp_ids), replace=True)
        parts = [by_resp[rid] for rid in sample_ids]
        boot = pd.concat(parts, ignore_index=True)
        nvd_acc = boot.loc[boot["condition"] == "NVD", "is_correct"].mean()
        sum_acc = boot.loc[boot["condition"] == "Summary", "is_correct"].mean()
        diffs[b] = sum_acc - nvd_acc

    ci_lo, ci_hi = np.nanpercentile(diffs, [2.5, 97.5])
    return {
        "n_respondents": len(resp_ids),
        "n_items": len(df),
        "nvd_acc": point_nvd,
        "summary_acc": point_summary,
        "gap": point_gap,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
    }


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    response_summary = pd.read_csv(DATA_DIR / "response_summary.csv")
    comprehension_long = pd.read_csv(DATA_DIR / "comprehension_long.csv")
    likert_long = pd.read_csv(DATA_DIR / "likert_long.csv")

    # ================= STEP 1: SCHEMA =================
    print("=" * 80)
    print("STEP 1: SCHEMA")
    print("=" * 80)
    for name, df in [("response_summary.csv", response_summary),
                      ("comprehension_long.csv", comprehension_long),
                      ("likert_long.csv", likert_long)]:
        print(f"\n--- {name} ---")
        print("columns/dtypes:")
        print(df.dtypes)
        print("5 sample rows:")
        print(df.head(5).to_string())

    print("\njoin key: response_id (present in all three; comprehension_long/likert_long "
          "additionally key on cve_id + condition, and comprehension_long further on question_num)")
    print("condition encoding: comprehension_long/likert_long 'condition' column, values 'NVD'|'Summary'")
    print("CVE ID encoding: 'cve_id' column, e.g. 'CVE-2020-8010'")
    print("question number encoding: comprehension_long 'question_num' column, values 1/2/3 "
          "(verified against survey_source.txt: Q1=what's vulnerable, Q2=how exploited, Q3=remediation, "
          "for all 12 CVEs -- see module docstring)")
    print("S1/S2/S3: response_summary.csv columns 's1_technical_background' (Yes/No), "
          "'s2_security_training' (Yes/No), 's3_cve_familiarity' (free-text 4-point scale, value set below)")
    print("S3 value set:", sorted(response_summary["s3_cve_familiarity"].dropna().unique().tolist()))

    # ---- exclusion ----
    n_raw = len(response_summary)
    excluded_s1no = response_summary[response_summary["s1_technical_background"] == "No"]
    kept = response_summary[response_summary["s1_technical_background"] != "No"]
    print(f"\nS1=No exclusion: raw pool n={n_raw}, excluded (S1=No) n={len(excluded_s1no)} "
          f"({sorted(excluded_s1no['response_id'].tolist())}), remaining (S1=Yes or unanswered) n={len(kept)}")

    analysis_sample = response_summary[
        (response_summary["s1_technical_background"] == "Yes")
        & (response_summary["n_items_answered_of_20"] > 0)
    ].copy()
    primary_ids = set(analysis_sample.loc[analysis_sample["s2_security_training"] == "No", "response_id"])
    contrast_ids = set(analysis_sample.loc[analysis_sample["s2_security_training"] == "Yes", "response_id"])
    print(f"\nAnalysis sample (S1=Yes, reached >=1 item): n={len(analysis_sample)}")
    print(f"  primary group (S1=Yes, S2=No): n={len(primary_ids)}")
    print(f"  contrast group (S1=Yes, S2=Yes): n={len(contrast_ids)}")

    comp = comprehension_long[comprehension_long["response_id"].isin(analysis_sample["response_id"])].dropna(subset=["is_correct"]).copy()
    comp["is_correct"] = comp["is_correct"].astype(bool).astype(float)
    lik = likert_long[likert_long["response_id"].isin(analysis_sample["response_id"])].dropna(subset=["clarity_score", "confidence_score"], how="all").copy()
    comp["question_type"] = comp["question_num"].map(QUESTION_TYPE)
    demo_cols = analysis_sample[["response_id", "s2_security_training", "s3_cve_familiarity", "duration_seconds"]]
    comp = comp.merge(demo_cols, on="response_id", how="left")
    lik = lik.merge(demo_cols, on="response_id", how="left")

    print(f"\nscored comprehension items in analysis sample: {len(comp)}")
    print(f"likert entries in analysis sample: {len(lik)}")

    not_answerable = []

    # ================= PROBE 1: SAMPLE CHARACTERISATION =================
    print("\n" + "=" * 80)
    print("PROBE 1: SAMPLE CHARACTERISATION")
    print("=" * 80)

    s1_counts = response_summary["s1_technical_background"].value_counts(dropna=False)
    s2_counts = analysis_sample["s2_security_training"].value_counts(dropna=False)
    s3_counts = analysis_sample["s3_cve_familiarity"].value_counts(dropna=False)
    print("\nS1 distribution (full raw pool, n={}):".format(n_raw))
    print(s1_counts)
    print(f"\nS2 distribution (analysis sample, n={len(analysis_sample)}):")
    print(s2_counts)
    print(f"\nS3 distribution (analysis sample, n={len(analysis_sample)}):")
    print(s3_counts)

    s2_s3_crosstab = pd.crosstab(analysis_sample["s2_security_training"], analysis_sample["s3_cve_familiarity"])
    print("\nS2 x S3 crosstab:")
    print(s2_s3_crosstab)
    s2_s3_crosstab.to_csv(TABLES_DIR / "p1_s2_x_s3_crosstab.csv")

    composition = pd.DataFrame({
        "group": ["raw_pool_total", "excluded_S1_No", "analysis_sample_S1_Yes_reached_content",
                   "primary_S1Yes_S2No", "contrast_S1Yes_S2Yes"],
        "n": [n_raw, len(excluded_s1no), len(analysis_sample), len(primary_ids), len(contrast_ids)],
    })
    composition.to_csv(TABLES_DIR / "p1_composition_counts.csv", index=False)
    print("\nComposition counts:")
    print(composition.to_string(index=False))

    baseline_nvd = comp[comp["condition"] == "NVD"]
    baseline_by_s2 = baseline_nvd.groupby("s2_security_training")["is_correct"].agg(["mean", "count"])
    baseline_by_s3 = baseline_nvd.groupby("s3_cve_familiarity")["is_correct"].agg(["mean", "count"])
    print("\nBaseline NVD-only accuracy by S2:")
    print(baseline_by_s2)
    print("\nBaseline NVD-only accuracy by S3:")
    print(baseline_by_s3)
    baseline_by_s2.to_csv(TABLES_DIR / "p1_baseline_nvd_accuracy_by_s2.csv")
    baseline_by_s3.to_csv(TABLES_DIR / "p1_baseline_nvd_accuracy_by_s3.csv")

    # Figure: S3 histogram
    s3_order = ["I have never worked with them", "I have seen them occasionally but do not work with them regularly",
                "I work with them from time to time as part of my role", "I work with them regularly"]
    s3_short = ["Never", "Seen\noccasionally", "Time to time\n(role)", "Regularly"]
    s3_vals = [s3_counts.get(lvl, 0) for lvl in s3_order]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(s3_short, s3_vals, width=0.55, color=COLOR_SUMMARY, zorder=3)
    for bar, v in zip(bars, s3_vals):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.1, str(v), ha="center", va="bottom", fontsize=10, color=TEXT_PRIMARY)
    ax.set_ylabel(f"Respondents (n={len(analysis_sample)})")
    ax.set_ylim(0, max(s3_vals) + 2)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "p1_s3_histogram.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ================= PROBE 2: DID THE SUMMARY HELP =================
    print("\n" + "=" * 80)
    print("PROBE 2: DID THE SUMMARY HELP")
    print("=" * 80)

    overall = bootstrap_condition_gap(comp)
    print(f"\nOverall: NVD={overall['nvd_acc']:.3f} Summary={overall['summary_acc']:.3f} "
          f"gap={overall['gap']:+.3f} 95% CI=[{overall['ci_lo']:+.3f}, {overall['ci_hi']:+.3f}] "
          f"(n_respondents={overall['n_respondents']}, n_items={overall['n_items']})")

    qtype_rows = [{"question_type": "overall", **overall}]
    for qt in ["what_vulnerable", "how_exploited", "remediation"]:
        res = bootstrap_condition_gap(comp[comp["question_type"] == qt])
        res["question_type"] = qt
        qtype_rows.append(res)
        print(f"{qt}: NVD={res['nvd_acc']:.3f} Summary={res['summary_acc']:.3f} gap={res['gap']:+.3f} "
              f"95% CI=[{res['ci_lo']:+.3f}, {res['ci_hi']:+.3f}] (n_items={res['n_items']})")

    qtype_df = pd.DataFrame(qtype_rows)[["question_type", "n_respondents", "n_items", "nvd_acc", "summary_acc", "gap", "ci_lo", "ci_hi"]]
    qtype_df.to_csv(TABLES_DIR / "p2_condition_x_questiontype_bootstrap.csv", index=False)

    cell_n = comp.groupby(["condition", "question_type"]).size().unstack()
    print("\ncondition x question_type cell n:")
    print(cell_n)
    cell_n.to_csv(TABLES_DIR / "p2_condition_x_questiontype_n.csv")

    # Figure: grouped bars condition x question type with CI whiskers
    qt_order = ["what_vulnerable", "how_exploited", "remediation"]
    x = np.arange(len(qt_order))
    width = 0.35
    nvd_means, sum_means, nvd_err, sum_err = [], [], [], []
    for qt in qt_order:
        row = qtype_df[qtype_df["question_type"] == qt].iloc[0]
        nvd_means.append(row["nvd_acc"] * 100)
        sum_means.append(row["summary_acc"] * 100)
    overall_row = qtype_df[qtype_df["question_type"] == "overall"].iloc[0]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    b1 = ax.bar(x - width / 2, nvd_means, width, label="Raw NVD", color=COLOR_RAW, zorder=3)
    b2 = ax.bar(x + width / 2, sum_means, width, label="Summary", color=COLOR_SUMMARY, zorder=3)
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{bar.get_height():.0f}%",
                    ha="center", va="bottom", fontsize=9, color=TEXT_PRIMARY)
    ax.set_xticks(x)
    ax.set_xticklabels([QUESTION_TYPE_LABEL[qt].replace(": ", ":\n") for qt in qt_order], fontsize=9)
    ax.set_ylabel("Comprehension accuracy (%)")
    ax.set_ylim(0, 110)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "p2_condition_x_questiontype.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ================= PROBE 3: FELT VS DEMONSTRATED =================
    print("\n" + "=" * 80)
    print("PROBE 3: FELT VS DEMONSTRATED UNDERSTANDING")
    print("=" * 80)

    clarity_conf_by_cond = lik.groupby("condition")[["clarity_score", "confidence_score"]].agg(["mean", "count"])
    print("\nClarity/confidence means by condition:")
    print(clarity_conf_by_cond)
    clarity_conf_by_cond.to_csv(TABLES_DIR / "p3_clarity_confidence_by_condition.csv")

    per_resp_clarity = lik.pivot_table(index="response_id", columns="condition", values="clarity_score", aggfunc="mean")
    per_resp_clarity = per_resp_clarity.dropna()
    nvd_clearer = (per_resp_clarity["NVD"] > per_resp_clarity["Summary"]).sum()
    sum_clearer = (per_resp_clarity["Summary"] > per_resp_clarity["NVD"]).sum()
    tied = (per_resp_clarity["NVD"] == per_resp_clarity["Summary"]).sum()
    clearer_tally = pd.DataFrame({
        "rating": ["NVD clearer", "Summary clearer", "Equal"],
        "n_participants": [nvd_clearer, sum_clearer, tied],
    })
    print(f"\nParticipant clarity preference (n={len(per_resp_clarity)} with both conditions rated):")
    print(clearer_tally.to_string(index=False))
    clearer_tally.to_csv(TABLES_DIR / "p3_clearer_tally.csv", index=False)

    cve_acc = comp.groupby("cve_id")["is_correct"].mean()
    cve_clarity = lik.groupby("cve_id")["clarity_score"].mean()
    cve_join = pd.DataFrame({"accuracy": cve_acc, "clarity": cve_clarity}).dropna()
    rho, pval = stats.spearmanr(cve_join["accuracy"], cve_join["clarity"])
    print(f"\nPer-CVE rank correlation (clarity vs accuracy), n_CVEs={len(cve_join)}: "
          f"Spearman rho={rho:.3f}, p={pval:.3f}")
    cve_join["condition_note"] = "pooled across both conditions"
    cve_join.to_csv(TABLES_DIR / "p3_cve_clarity_vs_accuracy.csv")

    entry_acc = comp.groupby(["response_id", "cve_id", "condition"])["is_correct"].mean().rename("entry_accuracy").reset_index()
    calib = entry_acc.merge(lik[["response_id", "cve_id", "condition", "confidence_score"]], on=["response_id", "cve_id", "condition"])
    calib["fully_correct"] = calib["entry_accuracy"] == 1.0
    conf_by_correct_cond = calib.groupby(["condition", "fully_correct"])["confidence_score"].agg(["mean", "count"])
    print("\nConfidence by (condition, fully-correct-entry):")
    print(conf_by_correct_cond)
    conf_by_correct_cond.to_csv(TABLES_DIR / "p3_confidence_correct_vs_incorrect.csv")

    calib["overconfident"] = (calib["confidence_score"] >= 4) & (~calib["fully_correct"])
    hc_wrong = calib.groupby("condition")["overconfident"].agg(["sum", "count", "mean"])
    print("\nHigh-confidence-wrong (confidence>=4, not all correct) by condition:")
    print(hc_wrong)
    hc_wrong.to_csv(TABLES_DIR / "p3_high_confidence_wrong_by_condition.csv")

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for cond, color, marker in [("NVD", COLOR_RAW, "o"), ("Summary", COLOR_SUMMARY, "^")]:
        sub = cve_join if False else None
    # scatter needs per-CVE-per-condition points, not pooled
    cve_cond_acc = comp.groupby(["cve_id", "condition"])["is_correct"].mean().rename("accuracy").reset_index()
    cve_cond_clarity = lik.groupby(["cve_id", "condition"])["clarity_score"].mean().rename("clarity").reset_index()
    scatter_df = cve_cond_acc.merge(cve_cond_clarity, on=["cve_id", "condition"])
    scatter_df.to_csv(TABLES_DIR / "p3_cve_x_condition_clarity_vs_accuracy.csv", index=False)
    for cond, color, marker in [("NVD", COLOR_RAW, "o"), ("Summary", COLOR_SUMMARY, "^")]:
        sub = scatter_df[scatter_df["condition"] == cond]
        ax.scatter(sub["accuracy"] * 100, sub["clarity"], color=color, marker=marker, s=70, label=cond, zorder=3, edgecolors="white", linewidths=0.5)
    ax.set_xlabel("Comprehension accuracy (%)")
    ax.set_ylabel("Mean clarity rating (1-5)")
    ax.set_xlim(0, 105)
    ax.set_ylim(1, 5.5)
    ax.legend(frameon=False, fontsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "p3_clarity_vs_accuracy_scatter.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ================= PROBE 4: WHO DOES IT HELP =================
    print("\n" + "=" * 80)
    print("PROBE 4: WHO DOES IT HELP -- CORE SUBGROUP TEST")
    print("=" * 80)

    primary_res = bootstrap_condition_gap(comp, "s2_security_training", "No")
    contrast_res = bootstrap_condition_gap(comp, "s2_security_training", "Yes")
    print(f"\nPrimary (S1=Yes,S2=No): NVD={primary_res['nvd_acc']:.3f} Summary={primary_res['summary_acc']:.3f} "
          f"gain={primary_res['gap']:+.3f} 95% CI=[{primary_res['ci_lo']:+.3f},{primary_res['ci_hi']:+.3f}] "
          f"(n_respondents={primary_res['n_respondents']})")
    print(f"Contrast (S1=Yes,S2=Yes): NVD={contrast_res['nvd_acc']:.3f} Summary={contrast_res['summary_acc']:.3f} "
          f"gain={contrast_res['gap']:+.3f} 95% CI=[{contrast_res['ci_lo']:+.3f},{contrast_res['ci_hi']:+.3f}] "
          f"(n_respondents={contrast_res['n_respondents']})")

    subgroup_gain_rows = [
        {"subgroup": "primary_S1Yes_S2No", **primary_res},
        {"subgroup": "contrast_S1Yes_S2Yes", **contrast_res},
    ]

    s3_levels_present = [lvl for lvl in s3_order if lvl in analysis_sample["s3_cve_familiarity"].values]
    for lvl in s3_levels_present:
        res = bootstrap_condition_gap(comp, "s3_cve_familiarity", lvl)
        if res:
            res["subgroup"] = f"S3={lvl}"
            subgroup_gain_rows.append(res)
            print(f"S3='{lvl}': gain={res['gap']:+.3f} 95% CI=[{res['ci_lo']:+.3f},{res['ci_hi']:+.3f}] "
                  f"(n_respondents={res['n_respondents']})")

    subgroup_gain_df = pd.DataFrame(subgroup_gain_rows)[["subgroup", "n_respondents", "n_items", "nvd_acc", "summary_acc", "gap", "ci_lo", "ci_hi"]]
    subgroup_gain_df.to_csv(TABLES_DIR / "p4_subgroup_gain.csv", index=False)

    worse_off = subgroup_gain_df[subgroup_gain_df["gap"] < 0]
    print(f"\nSubgroups where Summary accuracy < NVD accuracy (gap<0): {worse_off['subgroup'].tolist() if len(worse_off) else 'none'}")
    worse_off.to_csv(TABLES_DIR / "p4_worse_off_subgroups.csv", index=False)

    s3_rank_map = {lvl: i for i, lvl in enumerate(s3_order)}
    per_resp_acc = comp.groupby("response_id")["is_correct"].mean().rename("accuracy").reset_index()
    per_resp_acc = per_resp_acc.merge(demo_cols, on="response_id")
    per_resp_acc["s3_rank"] = per_resp_acc["s3_cve_familiarity"].map(s3_rank_map)
    rho_s3, p_s3 = stats.spearmanr(per_resp_acc["s3_rank"], per_resp_acc["accuracy"])
    print(f"\nS3 self-report-bias check: Spearman(S3 ordinal rank, per-respondent accuracy) = {rho_s3:.3f}, p={p_s3:.3f} (n={len(per_resp_acc)})")
    per_resp_acc.to_csv(TABLES_DIR / "p4_per_respondent_accuracy_vs_s3.csv", index=False)

    accuracy_by_cond_s2 = comp.groupby(["condition", "s2_security_training"])["is_correct"].agg(["mean", "count"])
    accuracy_by_cond_s3 = comp.groupby(["condition", "s3_cve_familiarity"])["is_correct"].agg(["mean", "count"])
    accuracy_by_cond_s2.to_csv(TABLES_DIR / "p4_accuracy_by_condition_x_s2.csv")
    accuracy_by_cond_s3.to_csv(TABLES_DIR / "p4_accuracy_by_condition_x_s3.csv")
    print("\naccuracy by condition x S2:")
    print(accuracy_by_cond_s2)
    print("\naccuracy by condition x S3:")
    print(accuracy_by_cond_s3)

    # Figure: gain across S3 levels + bar for S2 split
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    s3_gain_rows = subgroup_gain_df[subgroup_gain_df["subgroup"].str.startswith("S3=")]
    s3_labels = [s.replace("S3=", "") for s in s3_gain_rows["subgroup"]]
    s3_labels_short = {"I have never worked with them": "Never",
                        "I have seen them occasionally but do not work with them regularly": "Seen\noccasionally",
                        "I work with them from time to time as part of my role": "Time to time\n(role)",
                        "I work with them regularly": "Regularly"}
    s3_labels_disp = [s3_labels_short.get(s, s) for s in s3_labels]
    gains = s3_gain_rows["gap"].values * 100
    err_lo = gains - s3_gain_rows["ci_lo"].values * 100
    err_hi = s3_gain_rows["ci_hi"].values * 100 - gains
    axes[0].bar(s3_labels_disp, gains, color=COLOR_SUMMARY, zorder=3, width=0.5)
    axes[0].errorbar(s3_labels_disp, gains, yerr=[err_lo, err_hi], fmt="none", ecolor=TEXT_SECONDARY, capsize=4, zorder=4)
    axes[0].axhline(0, color=AXIS, linewidth=1)
    axes[0].set_ylabel("Summary - NVD accuracy (pp)")
    axes[0].set_title("Gain by S3 familiarity", fontsize=10)

    s2_rows = subgroup_gain_df[subgroup_gain_df["subgroup"].isin(["primary_S1Yes_S2No", "contrast_S1Yes_S2Yes"])]
    s2_labels_disp = ["Primary\n(S1=Yes,S2=No)", "Contrast\n(S1=Yes,S2=Yes)"]
    gains2 = s2_rows["gap"].values * 100
    err_lo2 = gains2 - s2_rows["ci_lo"].values * 100
    err_hi2 = s2_rows["ci_hi"].values * 100 - gains2
    axes[1].bar(s2_labels_disp, gains2, color=COLOR_SUMMARY, zorder=3, width=0.5)
    axes[1].errorbar(s2_labels_disp, gains2, yerr=[err_lo2, err_hi2], fmt="none", ecolor=TEXT_SECONDARY, capsize=4, zorder=4)
    axes[1].axhline(0, color=AXIS, linewidth=1)
    axes[1].set_title("Gain by S2 (security training)", fontsize=10)

    for ax in axes:
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(AXIS)
        ax.spines["bottom"].set_color(AXIS)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "p4_gain_by_subgroup.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ================= PROBE 5: ARTEFACT / INTEGRITY CHECKS =================
    print("\n" + "=" * 80)
    print("PROBE 5: ARTEFACT / INTEGRITY CHECKS")
    print("=" * 80)

    comp["slot"] = list(zip(comp["block"], comp["cve_id"]))
    comp["slot"] = comp["slot"].map(SLOT_MAP)
    slot_acc = comp.groupby("slot")["is_correct"].agg(["mean", "count"])
    print("\nAccuracy by slot position (1-4):")
    print(slot_acc)
    slot_acc.to_csv(TABLES_DIR / "p5_accuracy_by_slot.csv")

    full_block = analysis_sample[analysis_sample["n_items_answered_of_20"] == 20]
    print(f"\nDuration distribution, full-block (20/20 item) responses, n={len(full_block)}:")
    print(full_block[["response_id", "duration_seconds"]].sort_values("duration_seconds").to_string(index=False))
    print(f"\nFlagged as implausibly rushed: {sorted(RUSHED_RESPONSE_IDS)} "
          f"(117s for 20 items across 4 CVE entries = ~29s/entry incl. reading a CVSS table, a description, "
          f"and answering 5 questions; the next-fastest full-block response is 519s, >4x slower)")
    rushed_df = full_block[full_block["response_id"].isin(RUSHED_RESPONSE_IDS)][["response_id", "duration_seconds", "n_items_answered_of_20"]]
    rushed_df.to_csv(TABLES_DIR / "p5_rushed_flagged.csv", index=False)

    gap_all = bootstrap_condition_gap(comp)
    comp_norushed = comp[~comp["response_id"].isin(RUSHED_RESPONSE_IDS)]
    gap_norushed = bootstrap_condition_gap(comp_norushed)
    print(f"\nHeadline gap, all items: {gap_all['gap']:+.3f} (n_resp={gap_all['n_respondents']})")
    print(f"Headline gap, minus rushed: {gap_norushed['gap']:+.3f} (n_resp={gap_norushed['n_respondents']})")

    same_cve = comp.groupby(["cve_id", "condition"])["is_correct"].agg(["mean", "count"]).unstack()
    same_cve.columns = ["_".join(c) for c in same_cve.columns]
    same_cve["nvd_minus_summary"] = same_cve["mean_NVD"] - same_cve["mean_Summary"]
    print("\nSame CVE, NVD vs Summary (holding CVE constant):")
    print(same_cve.to_string())
    same_cve.to_csv(TABLES_DIR / "p5_same_cve_paired.csv")
    nvd_wins_cve = same_cve[same_cve["nvd_minus_summary"] > 0]
    print(f"\nCVEs where NVD beats Summary (pooled across questions): {nvd_wins_cve.index.tolist()}")

    cve_q_cond = comp.groupby(["cve_id", "question_num", "condition"])["is_correct"].agg(["mean", "count"]).unstack("condition")
    cve_q_cond.columns = ["_".join(c) for c in cve_q_cond.columns]
    cve_q_cond["nvd_minus_summary"] = cve_q_cond["mean_NVD"] - cve_q_cond["mean_Summary"]
    nvd_beats_summary_items = cve_q_cond[cve_q_cond["nvd_minus_summary"] > 0].sort_values("nvd_minus_summary", ascending=False)
    print(f"\nCVE x question items where NVD beats Summary: {len(nvd_beats_summary_items)} of {len(cve_q_cond)}")
    print(nvd_beats_summary_items.to_string())
    nvd_beats_summary_items.to_csv(TABLES_DIR / "p5_nvd_beats_summary_items.csv")

    DEFECTIVE_THRESHOLD = 0.5
    defective = cve_q_cond[(cve_q_cond["mean_NVD"] < DEFECTIVE_THRESHOLD) & (cve_q_cond["mean_Summary"] < DEFECTIVE_THRESHOLD)]
    print(f"\nItems failing in BOTH conditions (<{DEFECTIVE_THRESHOLD:.0%} accuracy each), "
          f"i.e. format-independent / likely ambiguous-wording candidates: {len(defective)}")
    print(defective.to_string())
    defective.to_csv(TABLES_DIR / "p5_defective_items_both_conditions.csv")

    defective_index = set(defective.index.tolist())
    comp_key = list(zip(comp["cve_id"], comp["question_num"]))
    comp_minus_defective = comp[[k not in defective_index for k in comp_key]]
    gap_minus_defective = bootstrap_condition_gap(comp_minus_defective)

    headline_rules = pd.DataFrame([
        {"rule": "all_items", "gap": gap_all["gap"], "n_items": gap_all["n_items"], "n_respondents": gap_all["n_respondents"]},
        {"rule": "minus_defective_items", "gap": gap_minus_defective["gap"], "n_items": gap_minus_defective["n_items"], "n_respondents": gap_minus_defective["n_respondents"]},
        {"rule": "minus_rushed_responses", "gap": gap_norushed["gap"], "n_items": gap_norushed["n_items"], "n_respondents": gap_norushed["n_respondents"]},
    ])
    print("\nHeadline gap under each rule:")
    print(headline_rules.to_string(index=False))
    headline_rules.to_csv(TABLES_DIR / "p5_headline_gap_rules.csv", index=False)

    # ================= NOT ANSWERABLE =================
    print("\n" + "=" * 80)
    print("NOT ANSWERABLE FROM AVAILABLE FIELDS")
    print("=" * 80)
    for item in not_answerable:
        print(f"  - {item}")
    if not not_answerable:
        print("  (all requested probes above were computable from S1/S2/S3 + comprehension/likert data; "
              "no probe required a role/occupation field)")


if __name__ == "__main__":
    main()
