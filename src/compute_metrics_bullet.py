"""Compute automated evaluation metrics (ROUGE, BERTScore, Dale-Chall, word count)
for the 48 generated bullet-format summaries (v2_bullet/summaries/summaries_bullet.json)
against the raw NVD description for each eval CVE (data/eval_sample.jsonl).

This is the v2 (bullet-format) counterpart to `src/compute_metrics.py` (the frozen
v1 prose run, `v1_prose/`, on the `prompt-prose` branch). It reuses that script's
scoring logic, libraries, preprocessing, and reference text unchanged so the two
runs are directly comparable. Two deliberate differences from v1, both decided
before this script was written (see METHODOLOGY_LOG.md "Stage 6d"):

1. Flesch-Kincaid is EXCLUDED here. FK is driven by sentence length, and the
   bullet format confounds that: a bullet FK score would reflect formatting
   (many short, single-clause lines) rather than readability. Dale-Chall is the
   primary readability metric for this run instead, since it scores vocabulary
   familiarity rather than sentence length and is unaffected by this confound.
2. No Wilcoxon signed-rank test. v1 reported Wilcoxon (W, p, rank-biserial r) as
   supporting evidence alongside Cohen's d. For v2 this run reports paired
   Cohen's d only -- descriptive statistics and effect sizes, no population-level
   significance test -- consistent with the exploratory, small-N (24) framing of
   this whole evaluation stage.

Bullet normalisation (the key correctness step for this run): summary bodies are
markdown bullet lists (lines starting with "- "). The leading bullet marker and
its whitespace are stripped from every bullet line before any metric is computed,
so scoring never sees the "- " token itself. See `strip_bullet_markers()`. Section
headers ("## What is vulnerable" etc.) are left untouched, matching v1's rule that
headers are scored as-is.

Reference text: the raw NVD `description` field is used as the reference for
ROUGE and BERTScore, same as v1, for the same reason (the research question is
comprehension relative to the raw NVD description, not relative to some other
summary).

Pinned for reproducibility (identical to v1, see METHODOLOGY_LOG.md):
- rouge-score 0.1.2, RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)
- bert-score 0.3.13, model_type='roberta-large' (lang='en' default), 17 layers, idf=False
- textstat 0.7.13, dale_chall_readability_score() (flesch_kincaid_grade() not used, see above)
- word count: len(text.split()) (whitespace-delimited token count), no library
- No RNG-dependent computation in this script; all metrics are deterministic
  given fixed model weights, so no random seed is set or required.
"""

import json
import re
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import textstat
from bert_score import score as bert_score_fn
from rouge_score import rouge_scorer

matplotlib.use("Agg")

SUMMARIES_PATH = "v2_bullet/summaries/summaries_bullet.json"
EVAL_SAMPLE_PATH = "data/eval_sample.jsonl"
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"
OUT_CSV = "v2_bullet/metrics/metrics_per_summary_bullet.csv"
OUT_JSON = "v2_bullet/metrics/metrics_per_summary_bullet.json"
COMPARISON_MD = "v2_bullet/metrics/PROMPT_COMPARISON_bullet.md"
FIGURES_DIR = Path("v2_bullet/figures")

BERT_SCORE_MODEL = "roberta-large"
BERT_SCORE_LANG = "en"
BERT_SCORE_NUM_LAYERS = 17

REFERENCE_SECTION_RE = re.compile(r"\n\s*(?:##\s*Reference\b|\*\*Reference\*\*)", re.IGNORECASE)
BULLET_MARKER_RE = re.compile(r"(?m)^[ \t]*-[ \t]+")

COLOR_NVD = "#2a78d6"       # blue
COLOR_PERSONA = "#008300"   # green
COLOR_BASELINE = "#4a3aa7"  # violet
COLOR_REGRESSIVE = "#d6432a"  # red-orange: summary DC score worse than raw NVD
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

METRIC_LABELS = {
    "rouge1": "ROUGE-1 (F)",
    "rouge2": "ROUGE-2 (F)",
    "rougeL": "ROUGE-L (F)",
    "bertscore_precision": "BERTScore precision",
    "bertscore_recall": "BERTScore recall",
    "bertscore_f1": "BERTScore F1",
    "dc_score_summary": "Dale-Chall score (summary)",
    "word_count": "Word count",
}


def strip_bullet_markers(text):
    """Remove leading '- ' bullet markers (and their indentation) from bullet
    lines. Section headers and body text are otherwise untouched."""
    return BULLET_MARKER_RE.sub("", text)


def extract_summary_text(output_text):
    match = REFERENCE_SECTION_RE.search(output_text)
    body = output_text[: match.start()] if match else output_text
    body = strip_bullet_markers(body)
    return body.strip()


def load_summaries(path):
    with open(path) as f:
        return json.load(f)


def load_eval_descriptions(path):
    descriptions = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            descriptions[rec["id"]] = rec["description"]
    return descriptions


def compute_rouge_all(summaries, references, scorer):
    rows = []
    for summary, reference in zip(summaries, references):
        scores = scorer.score(reference, summary)
        rows.append(
            {
                "rouge1": scores["rouge1"].fmeasure,
                "rouge2": scores["rouge2"].fmeasure,
                "rougeL": scores["rougeL"].fmeasure,
            }
        )
    return rows


def compute_bertscore_all(summaries, references):
    P, R, F1 = bert_score_fn(
        summaries,
        references,
        lang=BERT_SCORE_LANG,
        model_type=BERT_SCORE_MODEL,
        num_layers=BERT_SCORE_NUM_LAYERS,
        idf=False,
        verbose=False,
    )
    return P.tolist(), R.tolist(), F1.tolist()


def cohens_d_paired(diff):
    return float(np.mean(diff) / np.std(diff, ddof=1))


def paired_summary(a, b, label_a, label_b):
    """Paired comparison of two equal-length arrays (a - b), matched by index.
    Descriptive statistics and Cohen's d (paired) only -- no significance test,
    see module docstring."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    diff = a - b
    n = len(diff)
    result = {
        "label": f"{label_a} - {label_b}",
        "n": n,
        "mean_diff": float(np.mean(diff)),
        "sd_diff": float(np.std(diff, ddof=1)) if n > 1 else float("nan"),
        "median_diff": float(np.median(diff)),
    }
    if n > 1 and np.std(diff, ddof=1) > 0:
        result["cohens_dz"] = cohens_d_paired(diff)
    else:
        result["cohens_dz"] = float("nan")
    return result


def descriptive_row(series, label):
    arr = np.asarray(series, dtype=float)
    return {
        "metric": label,
        "n": len(arr),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "sd": float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan"),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def build_descriptive_table_md(rows):
    header = "| Metric | N | Mean | Median | SD | Min | Max |\n|---|---|---|---|---|---|---|\n"
    lines = [header]
    for r in rows:
        lines.append(
            f"| {r['metric']} | {r['n']} | {fmt(r['mean'])} | {fmt(r['median'])} | "
            f"{fmt(r['sd'])} | {fmt(r['min'])} | {fmt(r['max'])} |\n"
        )
    return "".join(lines)


def build_paired_table_md(rows):
    header = (
        "| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) |\n"
        "|---|---|---|---|---|---|\n"
    )
    lines = [header]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['n']} | {fmt(r['mean_diff'])} | {fmt(r['median_diff'])} | "
            f"{fmt(r['sd_diff'])} | {fmt(r['cohens_dz'])} |\n"
        )
    return "".join(lines)


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


def boxplot(ax, data_groups, labels, colors):
    bp = ax.boxplot(
        data_groups,
        tick_labels=labels,
        patch_artist=True,
        widths=0.5,
        medianprops={"color": TEXT_PRIMARY, "linewidth": 1.5},
        whiskerprops={"color": AXIS, "linewidth": 1.2},
        capprops={"color": AXIS, "linewidth": 1.2},
        boxprops={"linewidth": 1.2},
        flierprops={
            "marker": "o",
            "markersize": 4,
            "markerfacecolor": "none",
            "markeredgecolor": TEXT_SECONDARY,
        },
        zorder=3,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)
    return bp


def fig_bertscore(df):
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.5), sharey=False)
    for ax, metric, title in zip(
        axes,
        ["bertscore_f1", "bertscore_precision"],
        ["BERTScore F1", "BERTScore precision"],
    ):
        groups = [
            df.loc[df["arm"] == "persona", metric].tolist(),
            df.loc[df["arm"] == "baseline", metric].tolist(),
        ]
        boxplot(ax, groups, ["Persona", "Baseline"], [COLOR_PERSONA, COLOR_BASELINE])
        ax.set_ylabel(title)
        style_axes(ax)
    fig.suptitle("BERTScore vs. raw NVD description, by prompt condition", fontsize=11, color=TEXT_PRIMARY)
    fig.tight_layout()
    return save_figure(fig, "bertscore_persona_vs_baseline")


def fig_rouge(df):
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    metrics = ["rouge1", "rouge2", "rougeL"]
    metric_labels = ["ROUGE-1", "ROUGE-2", "ROUGE-L"]
    x = np.arange(len(metrics))
    width = 0.32
    for offset, arm, color in [(-width / 2, "persona", COLOR_PERSONA), (width / 2, "baseline", COLOR_BASELINE)]:
        means = [df.loc[df["arm"] == arm, m].mean() for m in metrics]
        sds = [df.loc[df["arm"] == arm, m].std(ddof=1) for m in metrics]
        ax.bar(
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
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels)
    ax.set_ylabel("F-measure (mean ± SD)")
    ax.set_title("ROUGE, by prompt condition", fontsize=11, color=TEXT_PRIMARY)
    ax.legend(frameon=False, fontsize=9)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "rouge_persona_vs_baseline")


def fig_dc_grouped(df, dc_nvd_by_cve):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    groups = [
        list(dc_nvd_by_cve.values()),
        df.loc[df["arm"] == "persona", "dc_score_summary"].tolist(),
        df.loc[df["arm"] == "baseline", "dc_score_summary"].tolist(),
    ]
    labels = ["Raw NVD\ndescription", "Persona\nsummary", "Baseline\nsummary"]
    colors = [COLOR_NVD, COLOR_PERSONA, COLOR_BASELINE]
    boxplot(ax, groups, labels, colors)
    ax.set_ylabel("Dale-Chall readability score")
    ax.set_title("Readability (Dale-Chall): raw NVD vs. summary (by prompt condition)", fontsize=11, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "dc_grouped_nvd_persona_baseline")


def fig_word_count(df):
    fig, ax = plt.subplots(figsize=(5, 4.5))
    groups = [
        df.loc[df["arm"] == "persona", "word_count"].tolist(),
        df.loc[df["arm"] == "baseline", "word_count"].tolist(),
    ]
    boxplot(ax, groups, ["Persona", "Baseline"], [COLOR_PERSONA, COLOR_BASELINE])
    ax.set_ylabel("Word count")
    ax.set_title("Summary length, by prompt condition", fontsize=11, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "word_count_persona_vs_baseline")


def fig_dc_paired_slope(df, dc_nvd_by_cve):
    fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
    for ax, arm, color in [(axes[0], "persona", COLOR_PERSONA), (axes[1], "baseline", COLOR_BASELINE)]:
        sub = df.loc[df["arm"] == arm].sort_values("cve_id")
        n_regressive = 0
        for _, row in sub.iterrows():
            dc_nvd = dc_nvd_by_cve[row["cve_id"]]
            dc_summary = row["dc_score_summary"]
            if dc_summary > dc_nvd:
                n_regressive += 1
                ax.plot([0, 1], [dc_nvd, dc_summary], color=COLOR_REGRESSIVE, alpha=0.85, linewidth=1.6, zorder=3)
            else:
                ax.plot([0, 1], [dc_nvd, dc_summary], color=color, alpha=0.5, linewidth=1, zorder=2)
        nvd_vals = [dc_nvd_by_cve[c] for c in sub["cve_id"]]
        summary_vals = sub["dc_score_summary"].tolist()
        ax.scatter([0] * len(nvd_vals), nvd_vals, color=COLOR_NVD, s=22, zorder=4, label="Raw NVD")
        ax.scatter([1] * len(summary_vals), summary_vals, color=color, s=22, zorder=4, label=f"{arm.capitalize()} summary")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Raw NVD", f"{arm.capitalize()}\nsummary"])
        ax.set_title(arm.capitalize(), fontsize=10, color=TEXT_PRIMARY)
        if n_regressive:
            handles, labels = ax.get_legend_handles_labels()
            handles.append(Line2D([0], [0], color=COLOR_REGRESSIVE, linewidth=1.6))
            labels.append(f"Regressive (n={n_regressive})")
            ax.legend(handles, labels, frameon=False, fontsize=8, loc="upper right")
        style_axes(ax)
        ax.xaxis.grid(False)
    axes[0].set_ylabel("Dale-Chall readability score")
    fig.suptitle("Per-CVE readability change (Dale-Chall): raw NVD → summary (paired, n=24)", fontsize=11, color=TEXT_PRIMARY)
    fig.tight_layout()
    return save_figure(fig, "dc_paired_slope_nvd_to_summary")


def append_methodology_log(n_rows, arm_counts, files_written, figures_written, before_example, after_example):
    entry = []
    entry.append("")
    entry.append("")
    entry.append("## Stage 6d -- Automated Metrics on Bullet-Format Summaries (v2) (2026-07-28)")
    entry.append("")
    entry.append("**Script:** `src/compute_metrics_bullet.py`")
    entry.append(
        f"**Outputs:** `{OUT_CSV}`, `{OUT_JSON}`, `{COMPARISON_MD}`, figures in `{FIGURES_DIR}/`"
    )
    entry.append("")
    entry.append(
        f"Computed ROUGE, BERTScore, Dale-Chall readability score, and word count for all "
        f"{n_rows} generated bullet-format summaries ({arm_counts.get('persona', 0)} persona, "
        f"{arm_counts.get('baseline', 0)} baseline, paired across the same 24 eval CVEs used in "
        "v1 prose), each scored against the raw NVD description for its CVE. Dale-Chall was also "
        "computed for the 24 raw NVD descriptions themselves, as a readability baseline. "
        "Descriptive statistics and paired Cohen's d are reported in "
        f"`{COMPARISON_MD}` as evidence, not as an interpretive verdict."
    )
    entry.append("")
    entry.append("### Reused from v1 prose, unchanged")
    entry.append("")
    entry.append(
        "`src/compute_metrics_bullet.py` reuses the scoring logic from `src/compute_metrics.py` "
        "(frozen on `v1_prose/`, `prompt-prose` branch commit `9c65bd8`) directly: same ROUGE "
        "config (`rouge-score` 0.1.2, stemmed ROUGE-1/2/L), same BERTScore config (`bert-score` "
        "0.3.13, `roberta-large`, 17 layers, idf=False), same Dale-Chall implementation "
        "(`textstat` 0.7.13), same word-count method (`len(text.split())`), same NVD reference "
        "text (`data/eval_sample.jsonl` `description` field), and the same Reference-section "
        "stripping regex applied to `output_text` before scoring. This preserves method parity "
        "between the v1 and v2 metric runs."
    )
    entry.append("")
    entry.append("### Flesch-Kincaid excluded from this run")
    entry.append("")
    entry.append(
        "Flesch-Kincaid grade level was deliberately dropped for the bullet-format run. FK is "
        "computed from average sentence length and syllable count only, and the bullet format "
        "confounds sentence length directly: each bullet line is a short, single-clause "
        "\"sentence\" by construction, so a bullet-format FK score would largely reflect the "
        "formatting choice (many short lines) rather than genuine readability. Dale-Chall is the "
        "primary readability metric for this run instead, since it scores vocabulary familiarity "
        "rather than sentence length and is not subject to this confound."
    )
    entry.append("")
    entry.append("### Bullet marker normalisation")
    entry.append("")
    entry.append(
        "Bullet markers are not words and must not leak into scoring. Before any metric is "
        "computed, `strip_bullet_markers()` removes the leading `\"- \"` marker and its "
        "indentation from every bullet line via `re.sub(r\"(?m)^[ \\t]*-[ \\t]+\", \"\", text)`, "
        "applied after the trailing Reference/URL section is stripped and before section headers "
        "(`## What is vulnerable` etc., left untouched) and body text are scored. Example, taken "
        "from CVE-2020-8010 baseline:"
    )
    entry.append("")
    entry.append("Before:")
    entry.append("```")
    entry.append(before_example)
    entry.append("```")
    entry.append("After:")
    entry.append("```")
    entry.append(after_example)
    entry.append("```")
    entry.append("")
    entry.append("### No significance test in this run")
    entry.append("")
    entry.append(
        "v1 reported the Wilcoxon signed-rank test (W, p) and rank-biserial r alongside Cohen's d "
        "as supporting evidence. For v2, only paired Cohen's d is reported, per the exploratory, "
        "small-N (24) framing carried through this whole evaluation stage: descriptives and "
        "effect sizes, no population-level significance testing. This is a deliberate difference "
        "from v1's method, not an oversight."
    )
    entry.append("")
    entry.append("### Reproducibility")
    entry.append("")
    entry.append("| Component | Pinned value |\n|---|---|")
    entry.append("| ROUGE library | `rouge-score` 0.1.2, `RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)` |")
    entry.append(
        f"| BERTScore model | `{BERT_SCORE_MODEL}` (`bert-score` 0.3.13, lang=`{BERT_SCORE_LANG}`, "
        f"{BERT_SCORE_NUM_LAYERS} layers, idf=False) |"
    )
    entry.append("| Dale-Chall library | `textstat` 0.7.13, `dale_chall_readability_score()` |")
    entry.append("| Word count method | `len(text.split())`, no external library |")
    entry.append("| Random seeds | None used; all metrics in this script are deterministic given fixed model weights |")
    entry.append("")
    entry.append(
        f"This run processed {n_rows} rows. Files written were {', '.join(files_written)}. "
        f"{len(figures_written)} figures were written "
        f"({', '.join(Path(p).name for p in figures_written)})."
    )
    entry.append("")

    with open(METHODOLOGY_LOG_PATH, "a") as f:
        f.write("\n".join(entry))


def main():
    print(f"Loading summaries from {SUMMARIES_PATH}...")
    summaries = load_summaries(SUMMARIES_PATH)
    print(f"Loaded {len(summaries)} summary records.")

    print(f"Loading raw NVD descriptions from {EVAL_SAMPLE_PATH}...")
    nvd_descriptions = load_eval_descriptions(EVAL_SAMPLE_PATH)
    print(f"Loaded {len(nvd_descriptions)} eval CVE descriptions.")

    cve_ids = [r["cve_id"] for r in summaries]
    arms = [r["prompt_version"] for r in summaries]

    # Capture a before/after bullet-normalisation example for the log/note.
    raw_match = REFERENCE_SECTION_RE.search(summaries[0]["output_text"])
    raw_body = summaries[0]["output_text"][: raw_match.start()] if raw_match else summaries[0]["output_text"]
    before_line = next(line for line in raw_body.splitlines() if line.strip().startswith("- "))
    after_line = BULLET_MARKER_RE.sub("", before_line)

    summary_texts = [extract_summary_text(r["output_text"]) for r in summaries]
    references = [nvd_descriptions[cve_id] for cve_id in cve_ids]

    print("Computing ROUGE-1/2/L...")
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    rouge_rows = compute_rouge_all(summary_texts, references, scorer)

    print(f"Computing BERTScore ({BERT_SCORE_MODEL})... (downloads model on first run)")
    bp, br, bf1 = compute_bertscore_all(summary_texts, references)

    print("Computing Dale-Chall readability score (summaries and NVD baseline)...")
    dc_summary = [textstat.dale_chall_readability_score(t) for t in summary_texts]
    dc_nvd_by_cve = {cve_id: textstat.dale_chall_readability_score(desc) for cve_id, desc in nvd_descriptions.items()}
    dc_nvd = [dc_nvd_by_cve[cve_id] for cve_id in cve_ids]

    print("Computing word count (summaries, post bullet-normalisation)...")
    word_counts = [len(t.split()) for t in summary_texts]

    df = pd.DataFrame(
        {
            "cve_id": cve_ids,
            "arm": arms,
            "rouge1": [r["rouge1"] for r in rouge_rows],
            "rouge2": [r["rouge2"] for r in rouge_rows],
            "rougeL": [r["rougeL"] for r in rouge_rows],
            "bertscore_precision": bp,
            "bertscore_recall": br,
            "bertscore_f1": bf1,
            "dc_score_summary": dc_summary,
            "dc_score_nvd": dc_nvd,
            "word_count": word_counts,
        }
    )

    Path(OUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    df.to_json(OUT_JSON, orient="records", indent=2)
    print(f"Wrote {OUT_CSV} and {OUT_JSON} ({len(df)} rows).")

    # --- Analysis ---
    metric_cols = [
        "rouge1", "rouge2", "rougeL",
        "bertscore_precision", "bertscore_recall", "bertscore_f1",
        "dc_score_summary", "word_count",
    ]

    desc_rows = []
    for arm in ["persona", "baseline"]:
        sub = df.loc[df["arm"] == arm]
        for col in metric_cols:
            desc_rows.append(descriptive_row(sub[col], f"{METRIC_LABELS[col]} -- {arm}"))
    desc_rows.append(descriptive_row(list(dc_nvd_by_cve.values()), "Dale-Chall score -- raw NVD description"))

    persona_df = df.loc[df["arm"] == "persona"].set_index("cve_id").sort_index()
    baseline_df = df.loc[df["arm"] == "baseline"].set_index("cve_id").sort_index()
    assert list(persona_df.index) == list(baseline_df.index), "cve_id sets diverge between arms"

    persona_vs_baseline_rows = []
    for col in metric_cols:
        persona_vs_baseline_rows.append(
            paired_summary(persona_df[col].values, baseline_df[col].values, f"Persona {METRIC_LABELS[col]}", f"Baseline {METRIC_LABELS[col]}")
        )

    dc_nvd_sorted = [dc_nvd_by_cve[c] for c in persona_df.index]
    dc_vs_nvd_rows = [
        paired_summary(persona_df["dc_score_summary"].values, dc_nvd_sorted, "Persona summary Dale-Chall", "Raw NVD Dale-Chall"),
        paired_summary(baseline_df["dc_score_summary"].values, dc_nvd_sorted, "Baseline summary Dale-Chall", "Raw NVD Dale-Chall"),
    ]

    n_pairs = len(persona_df)

    md = []
    md.append("# Prompt Comparison: Automated Metrics (v2, bullet format)\n\n")
    md.append(
        "This file reports evidence, not a verdict. It contains descriptive statistics and paired "
        "Cohen's d effect sizes only; interpretation of which prompt arm is \"better\" is left to "
        "the dissertation chapters. This is the v2 (bullet-format) counterpart to "
        "`v1_prose/metrics/PROMPT_COMPARISON_prose.md`; see METHODOLOGY_LOG.md \"Stage 6d\" for "
        "the FK exclusion rationale, the bullet-normalisation method, and the reasoning for "
        "dropping the significance test that v1 reported.\n\n"
    )
    md.append(
        f"**Design:** paired, n={n_pairs} eval CVEs, 2 prompt arms (persona, baseline), same 24 "
        "CVEs in both arms (identical eval set to v1 prose). Small-N, exploratory. Descriptive "
        f"statistics and effect sizes only -- **no significance test is reported in this run** "
        "(v1's Wilcoxon signed-rank test was deliberately dropped here, see METHODOLOGY_LOG.md).\n\n"
    )
    md.append("## Descriptive statistics\n\n")
    md.append(
        "Mean, median, SD, min, max for each metric, per prompt arm, and for the Dale-Chall score "
        "of the raw NVD description (n=24, not split by arm since it is the same set of 24 "
        "descriptions in both arms).\n\n"
    )
    md.append(build_descriptive_table_md(desc_rows))
    md.append("\n")

    md.append("## Persona vs. baseline: paired differences\n\n")
    md.append(
        "Paired difference (persona minus baseline) per metric, matched by cve_id, n=24 pairs. "
        "Cohen's d (paired, d_z = mean diff / SD of diff) is the only effect size reported.\n\n"
    )
    md.append(build_paired_table_md(persona_vs_baseline_rows))
    md.append("\n")

    md.append("## Summaries vs. raw NVD: Dale-Chall paired difference\n\n")
    md.append(
        "Paired difference (summary Dale-Chall minus raw NVD Dale-Chall) per arm, matched by "
        "cve_id, n=24 pairs per arm. A negative mean difference means the summary scored lower "
        "(easier, less reliant on unfamiliar vocabulary) than the raw NVD description for that "
        "CVE.\n\n"
    )
    md.append(build_paired_table_md(dc_vs_nvd_rows))
    md.append("\n")

    md.append("## Bullet normalisation\n\n")
    md.append(
        "Leading bullet markers (`\"- \"` and indentation) were stripped from every bullet line "
        "before scoring; section headers were left untouched. Example (CVE-2020-8010, baseline):\n\n"
    )
    md.append(f"Before: `{before_line.strip()}`\n\n")
    md.append(f"After: `{after_line.strip()}`\n\n")

    md.append("## Figures\n\n")
    md.append(f"See `{FIGURES_DIR}/` for PNG (300 dpi) and SVG versions of each figure below.\n\n")
    md.append("- `dc_grouped_nvd_persona_baseline_bullet` -- Dale-Chall score, raw NVD vs. persona vs. baseline\n")
    md.append("- `bertscore_persona_vs_baseline_bullet` -- BERTScore F1 and precision, persona vs. baseline\n")
    md.append("- `rouge_persona_vs_baseline_bullet` -- ROUGE-1/2/L, persona vs. baseline\n")
    md.append("- `dc_paired_slope_nvd_to_summary_bullet` -- per-CVE paired Dale-Chall change, raw NVD to summary\n")
    md.append("- `word_count_persona_vs_baseline_bullet` -- word count, persona vs. baseline\n")

    Path(COMPARISON_MD).parent.mkdir(parents=True, exist_ok=True)
    Path(COMPARISON_MD).write_text("".join(md))
    print(f"Wrote {COMPARISON_MD}.")

    # --- Figures ---
    print("Generating figures...")
    figures_written = []
    figures_written += fig_dc_grouped(df, dc_nvd_by_cve)
    figures_written += fig_bertscore(df)
    figures_written += fig_rouge(df)
    figures_written += fig_dc_paired_slope(df, dc_nvd_by_cve)
    figures_written += fig_word_count(df)

    # --- Methodology log ---
    arm_counts = df["arm"].value_counts().to_dict()
    append_methodology_log(
        len(df), arm_counts, [OUT_CSV, OUT_JSON, COMPARISON_MD], figures_written,
        before_line.strip(), after_line.strip(),
    )
    print(f"Appended 'Stage 6d' section to {METHODOLOGY_LOG_PATH}.")

    print()
    print("Done.")
    print(f"Rows processed: {len(df)}")
    print(f"Files written: {OUT_CSV}, {OUT_JSON}, {COMPARISON_MD}, {METHODOLOGY_LOG_PATH} (appended)")
    print(f"Figures written: {len(figures_written)}")
    for p in figures_written:
        print(f"  {p}")
    print("Bullet normalisation example:")
    print(f"  before: {before_line.strip()}")
    print(f"  after:  {after_line.strip()}")


if __name__ == "__main__":
    main()
