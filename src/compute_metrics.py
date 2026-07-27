"""Compute automated evaluation metrics (ROUGE, BERTScore, Flesch-Kincaid,
Dale-Chall, word count) for the 48 generated summaries (summaries.json)
against the raw NVD description for each eval CVE (data/eval_sample.jsonl).

Reference text: the raw NVD `description` field is used as the reference for
all three text-comparison metrics throughout (ROUGE, BERTScore, and the FK
baseline comparison). This is fixed because the research question is defined
as improving comprehension relative to the raw NVD description -- see
METHODOLOGY_LOG.md, "Automated evaluation metrics" section, for the full
rationale and the per-metric favourable direction (they are not all "higher
is better" against this same reference).

Text extraction: `output_text` records carry a trailing "Reference" section
of bare source URLs, which is stripped before scoring (pure noise for a
text-similarity metric). The three summary sections themselves (headers
included) are scored as-is. One record (CVE-2022-3062, baseline) uses
**bold** section headers instead of ## headers; both styles are handled
uniformly by the extraction regex.

Pinned for reproducibility (also recorded in METHODOLOGY_LOG.md):
- rouge-score 0.1.2, RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)
- bert-score 0.3.13, model_type='roberta-large' (lang='en' default), 17 layers, idf=False
- textstat 0.7.13, flesch_kincaid_grade() and dale_chall_readability_score()
- word count: len(text.split()) (whitespace-delimited token count), no library
- scipy 1.18.0 (stats.wilcoxon)
- No RNG-dependent computation in this script; all metrics are deterministic
  given fixed model weights, so no random seed is set or required.
"""

import json
import re
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import textstat
from bert_score import score as bert_score_fn
from rouge_score import rouge_scorer
from scipy import stats

matplotlib.use("Agg")

SUMMARIES_PATH = "v1_prose/summaries/summaries_prose.json"
EVAL_SAMPLE_PATH = "data/eval_sample.jsonl"
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"
OUT_CSV = "metrics_per_summary.csv"
OUT_JSON = "metrics_per_summary.json"
COMPARISON_MD = "PROMPT_COMPARISON.md"
FIGURES_DIR = Path("figures")

BERT_SCORE_MODEL = "roberta-large"
BERT_SCORE_LANG = "en"
BERT_SCORE_NUM_LAYERS = 17

REFERENCE_SECTION_RE = re.compile(r"\n\s*(?:##\s*Reference\b|\*\*Reference\*\*)", re.IGNORECASE)

COLOR_NVD = "#2a78d6"       # blue
COLOR_PERSONA = "#008300"   # green
COLOR_BASELINE = "#4a3aa7"  # violet
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
    "fk_grade_summary": "Flesch-Kincaid grade (summary)",
    "dc_score_summary": "Dale-Chall score (summary)",
    "word_count": "Word count",
}


def extract_summary_text(output_text):
    match = REFERENCE_SECTION_RE.search(output_text)
    body = output_text[: match.start()] if match else output_text
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


def wilcoxon_rank_biserial(diff):
    nonzero = diff[diff != 0]
    if len(nonzero) == 0:
        return float("nan")
    ranks = stats.rankdata(np.abs(nonzero))
    pos = ranks[nonzero > 0].sum()
    neg = ranks[nonzero < 0].sum()
    total = ranks.sum()
    return float((pos - neg) / total)


def paired_summary(a, b, label_a, label_b):
    """Paired comparison of two equal-length arrays (a - b), matched by index."""
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
    result["wilcoxon_r"] = wilcoxon_rank_biserial(diff)
    if np.any(diff != 0):
        try:
            w_stat, w_p = stats.wilcoxon(diff)
            result["wilcoxon_stat"] = float(w_stat)
            result["wilcoxon_p"] = float(w_p)
        except ValueError:
            result["wilcoxon_stat"] = float("nan")
            result["wilcoxon_p"] = float("nan")
    else:
        result["wilcoxon_stat"] = float("nan")
        result["wilcoxon_p"] = float("nan")
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
        "| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) | "
        "Wilcoxon r | Wilcoxon W | Wilcoxon p |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    lines = [header]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['n']} | {fmt(r['mean_diff'])} | {fmt(r['median_diff'])} | "
            f"{fmt(r['sd_diff'])} | {fmt(r['cohens_dz'])} | {fmt(r['wilcoxon_r'])} | "
            f"{fmt(r['wilcoxon_stat'])} | {fmt(r['wilcoxon_p'], 4)} |\n"
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
    FIGURES_DIR.mkdir(exist_ok=True)
    png_path = FIGURES_DIR / f"{name}.png"
    svg_path = FIGURES_DIR / f"{name}.svg"
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


def fig_fk_grouped(df, nvd_by_cve):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    groups = [
        list(nvd_by_cve.values()),
        df.loc[df["arm"] == "persona", "fk_grade_summary"].tolist(),
        df.loc[df["arm"] == "baseline", "fk_grade_summary"].tolist(),
    ]
    labels = ["Raw NVD\ndescription", "Persona\nsummary", "Baseline\nsummary"]
    colors = [COLOR_NVD, COLOR_PERSONA, COLOR_BASELINE]
    boxplot(ax, groups, labels, colors)
    ax.set_ylabel("Flesch-Kincaid grade level")
    ax.set_title("Readability: raw NVD vs. summary (by prompt arm)", fontsize=11, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "fk_grouped_nvd_persona_baseline")


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
    fig.suptitle("BERTScore vs. raw NVD description, by prompt arm", fontsize=11, color=TEXT_PRIMARY)
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
    ax.set_title("ROUGE vs. raw NVD description, by prompt arm", fontsize=11, color=TEXT_PRIMARY)
    ax.legend(frameon=False, fontsize=9)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "rouge_persona_vs_baseline")


def fig_fk_paired_slope(df, nvd_by_cve):
    fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
    for ax, arm, color in [(axes[0], "persona", COLOR_PERSONA), (axes[1], "baseline", COLOR_BASELINE)]:
        sub = df.loc[df["arm"] == arm].sort_values("cve_id")
        for _, row in sub.iterrows():
            nvd_fk = nvd_by_cve[row["cve_id"]]
            ax.plot([0, 1], [nvd_fk, row["fk_grade_summary"]], color=color, alpha=0.5, linewidth=1, zorder=2)
        nvd_vals = [nvd_by_cve[c] for c in sub["cve_id"]]
        summary_vals = sub["fk_grade_summary"].tolist()
        ax.scatter([0] * len(nvd_vals), nvd_vals, color=COLOR_NVD, s=22, zorder=3, label="Raw NVD")
        ax.scatter([1] * len(summary_vals), summary_vals, color=color, s=22, zorder=3, label=f"{arm.capitalize()} summary")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Raw NVD", f"{arm.capitalize()}\nsummary"])
        ax.set_title(arm.capitalize(), fontsize=10, color=TEXT_PRIMARY)
        style_axes(ax)
        ax.xaxis.grid(False)
    axes[0].set_ylabel("Flesch-Kincaid grade level")
    fig.suptitle("Per-CVE readability change: raw NVD → summary (paired, n=24)", fontsize=11, color=TEXT_PRIMARY)
    fig.tight_layout()
    return save_figure(fig, "fk_paired_slope_nvd_to_summary")


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
    ax.set_title("Readability (Dale-Chall): raw NVD vs. summary (by prompt arm)", fontsize=11, color=TEXT_PRIMARY)
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
    ax.set_title("Summary length, by prompt arm", fontsize=11, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "word_count_persona_vs_baseline")


def fig_dc_paired_slope(df, dc_nvd_by_cve):
    fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
    for ax, arm, color in [(axes[0], "persona", COLOR_PERSONA), (axes[1], "baseline", COLOR_BASELINE)]:
        sub = df.loc[df["arm"] == arm].sort_values("cve_id")
        for _, row in sub.iterrows():
            dc_nvd = dc_nvd_by_cve[row["cve_id"]]
            ax.plot([0, 1], [dc_nvd, row["dc_score_summary"]], color=color, alpha=0.5, linewidth=1, zorder=2)
        nvd_vals = [dc_nvd_by_cve[c] for c in sub["cve_id"]]
        summary_vals = sub["dc_score_summary"].tolist()
        ax.scatter([0] * len(nvd_vals), nvd_vals, color=COLOR_NVD, s=22, zorder=3, label="Raw NVD")
        ax.scatter([1] * len(summary_vals), summary_vals, color=color, s=22, zorder=3, label=f"{arm.capitalize()} summary")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Raw NVD", f"{arm.capitalize()}\nsummary"])
        ax.set_title(arm.capitalize(), fontsize=10, color=TEXT_PRIMARY)
        style_axes(ax)
        ax.xaxis.grid(False)
    axes[0].set_ylabel("Dale-Chall readability score")
    fig.suptitle("Per-CVE readability change (Dale-Chall): raw NVD → summary (paired, n=24)", fontsize=11, color=TEXT_PRIMARY)
    fig.tight_layout()
    return save_figure(fig, "dc_paired_slope_nvd_to_summary")


def append_methodology_log(n_rows, arm_counts, files_written, figures_written):
    entry = []
    entry.append("")
    entry.append("## Automated evaluation metrics")
    entry.append("")
    entry.append("**Script:** `src/compute_metrics.py`")
    entry.append(
        f"**Outputs:** `{OUT_CSV}`, `{OUT_JSON}`, `{COMPARISON_MD}`, figures in `{FIGURES_DIR}/`"
    )
    entry.append("")
    entry.append(
        f"Computed ROUGE, BERTScore, Flesch-Kincaid grade level, Dale-Chall readability score, "
        f"and word count for all {n_rows} generated summaries ({arm_counts.get('persona', 0)} "
        f"persona, {arm_counts.get('baseline', 0)} baseline, paired across the same 24 eval "
        "CVEs), each scored against the raw NVD description for its CVE. Flesch-Kincaid grade "
        "level and Dale-Chall readability score were also computed for the 24 raw NVD "
        "descriptions themselves, as readability baselines. Full descriptive statistics, paired "
        f"differences, and effect sizes are reported in `{COMPARISON_MD}` as evidence, not as an "
        "interpretive verdict."
    )
    entry.append("")
    entry.append("### Reference text used for ROUGE and BERTScore")
    entry.append("")
    entry.append(
        "The raw NVD `description` field (from `data/eval_sample.jsonl`) is the reference text "
        "for both ROUGE and BERTScore, for every summary in both prompt arms. This is fixed "
        "because the research question is defined as improving comprehension relative to the "
        "raw NVD description, so NVD is the thing being compared against, not an alternative "
        "reference summary."
    )
    entry.append("")
    entry.append("### Favourable direction differs per metric")
    entry.append("")
    entry.append(
        "The same NVD reference is used for all three text-comparison metrics, but a favourable "
        "result does not mean the same thing for each of them, and this distinction is preserved "
        "throughout the reporting in this project rather than treated as a single similarity "
        "score."
    )
    entry.append("")
    entry.append(
        "Flesch-Kincaid treats the NVD description as a baseline to beat. A summary grade level "
        "lower than the NVD grade level is the favourable outcome, since a lower grade level "
        "means the text is easier to read. This is a before/after comparison, not a similarity "
        "score."
    )
    entry.append("")
    entry.append(
        "Dale-Chall is treated the same way as Flesch-Kincaid. A summary Dale-Chall score lower "
        "than the NVD score is the favourable outcome, since a lower score means the text relies "
        "less on unfamiliar vocabulary. As with Flesch-Kincaid, NVD is the baseline to beat, not "
        "a similarity target."
    )
    entry.append("")
    entry.append(
        "BERTScore treats NVD as a fidelity anchor rather than a target to maximise. A summary "
        "that stays semantically close to the NVD description indicates it has not drifted from "
        "or fabricated beyond the source. A higher BERTScore is favourable only as evidence of "
        "grounding, not as evidence that comprehension has improved. A summary scoring near 1.0 "
        "would mean it barely transformed the source text at all, which is not the goal of this "
        "study."
    )
    entry.append("")
    entry.append(
        "ROUGE is expected to be low, and that is not a failure. Because the summaries "
        "deliberately rephrase the NVD description into plainer language, low lexical overlap "
        "with NVD is the anticipated and desired result. ROUGE is retained mainly as a "
        "conventional reference point rather than as a primary success measure. Low ROUGE "
        "alongside high BERTScore is read as the signature of faithful rephrasing, meaning "
        "preserved, wording changed."
    )
    entry.append("")
    entry.append("### ROUGE")
    entry.append("")
    entry.append(
        "**What it measures.** ROUGE measures n-gram overlap between a generated text and a "
        "reference text. ROUGE-1 and ROUGE-2 count overlapping single words and word pairs "
        "respectively, and ROUGE-L measures the longest common subsequence of words, all "
        "reported here as F-measure against the raw NVD description. Porter stemming is applied "
        "before matching (`use_stemmer=True`), so words are reduced to a common root and "
        "grammatical variants such as \"vulnerability\" and \"vulnerabilities\" or \"exploited\" "
        "and \"exploits\" count as matches rather than mismatches. This is the standard "
        "configuration used in the original ROUGE toolkit and avoids penalising the summaries "
        "for ordinary morphological variation on top of the deliberate rephrasing already "
        "discussed below."
    )
    entry.append(
        "**Why it is included.** ROUGE is one of the most widely used automated metrics in "
        "summarisation research, and reporting it allows this study's results to sit alongside "
        "the broader summarisation literature, even though it is not expected to be the metric "
        "that best captures this study's goal."
    )
    entry.append(
        "**Pros for this task.** It is fast to compute, requires no external model, and gives a "
        "simple, well-understood lexical baseline that other summarisation studies also report."
    )
    entry.append(
        "**Limitations for this task.** ROUGE penalises the deliberate rephrasing the summaries "
        "are designed to perform. A summary that expresses the same vulnerability in plainer "
        "language will necessarily share fewer surface words with the NVD description, so a low "
        "ROUGE score here reflects successful transformation rather than infidelity to the "
        "source. It is retained mainly as a conventional reference point rather than as a "
        "measure this study optimises for or draws conclusions from in isolation."
    )
    entry.append("")
    entry.append("### BERTScore")
    entry.append("")
    entry.append(
        f"**What it measures.** BERTScore measures semantic similarity between a generated text "
        f"and a reference text using contextual embeddings from a pretrained language model "
        f"(`{BERT_SCORE_MODEL}`), matching tokens by embedding similarity rather than exact "
        "surface form. Precision, recall, and F1 are all recorded here rather than F1 alone, so "
        "that over-generation and under-coverage relative to the source can be distinguished."
    )
    entry.append(
        "**Why it is included.** It captures meaning preservation in a way ROUGE cannot, since "
        "it can recognise paraphrase and synonymy rather than requiring literal word overlap, "
        "which matters directly for summaries that are meant to rephrase, not copy, the source."
    )
    entry.append(
        "**Pros for this task.** Combined with low ROUGE, a high BERTScore supports the "
        "argument that a summary has preserved the meaning of the NVD description while changing "
        "its wording, which is the intended behaviour of the summarisation pipeline."
    )
    entry.append(
        "**Limitations for this task.** BERTScore supports a faithfulness argument but it is not "
        "a hallucination detector. It measures how semantically close the summary sits to the "
        "reference overall, not whether every specific claim in the summary is actually "
        "supported by the source, so a fabricated but topically plausible sentence can still "
        "score reasonably well. It is also weaker in specialised domains such as vulnerability "
        "descriptions, since the underlying language model is trained on general-purpose text "
        "rather than security-specific corpora."
    )
    entry.append("")
    entry.append("### Flesch-Kincaid grade level")
    entry.append("")
    entry.append(
        "**What it measures.** Flesch-Kincaid grade level estimates the US school grade level "
        "needed to understand a piece of text, calculated from average sentence length and "
        "average word length (syllable count) only."
    )
    entry.append(
        "**Why it is included.** Readability relative to the raw NVD description is a central "
        "comparison in this study, since the tool's stated goal is to improve comprehension for "
        "technical non-security personnel, and grade level is a widely used, cheaply computed "
        "proxy for how approachable a piece of text is."
    )
    entry.append(
        "**Pros for this task.** It is simple, reproducible, requires no external model, and "
        "gives a direct before/after comparison against the raw NVD description for every eval "
        "CVE."
    )
    entry.append(
        "**Limitations for this task.** Flesch-Kincaid measures reading ease from sentence and "
        "word length only, not clarity, logical structure, or factual correctness. A summary can "
        "score a lower grade level while still being confusing, poorly organised, or wrong, so "
        "this metric supports the comprehension claim but cannot establish it alone. It is "
        "reported alongside, and is intended to be read alongside, the questionnaire-based "
        "comprehension evidence from the study's human evaluation."
    )
    entry.append("")
    entry.append("### Dale-Chall readability score")
    entry.append("")
    entry.append(
        "**What it measures.** The Dale-Chall readability score estimates how difficult a text "
        "is to read by checking each word against a list of words familiar to most readers and "
        "penalising the proportion of words that fall outside that list, combined with average "
        "sentence length."
    )
    entry.append(
        "**Why it is included.** Flesch-Kincaid uses only sentence length and syllable count, so "
        "it has no way to detect vocabulary or jargon. A word such as \"authentication\" is short "
        "and scores as easy under Flesch-Kincaid, even though it is unfamiliar to a non-security "
        "reader and is exactly the kind of jargon this study's summaries are meant to explain. "
        "Dale-Chall targets that vocabulary barrier directly by scoring against a familiar-word "
        "list rather than word length, so it is included as a complementary readability proxy "
        "that may reveal a jargon-reduction effect Flesch-Kincaid structurally cannot see."
    )
    entry.append(
        "**Pros for this task.** It is simple, reproducible, requires no external model, and "
        "gives a direct before/after comparison against the raw NVD description for every eval "
        "CVE, on a dimension (word familiarity) that Flesch-Kincaid does not cover."
    )
    entry.append(
        "**Limitations for this task.** The familiar-word list underlying Dale-Chall was built "
        "for general English reading material, not for technical or security vocabulary "
        "specifically, so it will flag many correct and necessary security terms as unfamiliar "
        "regardless of how clearly they are explained. Proper names and regular inflections of "
        "listed words are also counted as difficult words by this implementation, which can "
        "inflate the score for text that names specific products, vendors, or CVE identifiers. "
        "As with Flesch-Kincaid, a lower score does not by itself establish that a text is "
        "genuinely clearer, only that it draws on more common vocabulary."
    )
    entry.append("")
    entry.append("### Word count")
    entry.append("")
    entry.append(
        "**What it measures.** Whitespace-delimited token count (`len(text.split())`) of the "
        "same extracted three-part summary body used for the other text metrics, i.e. after the "
        "trailing reference/URL block is stripped."
    )
    entry.append(
        "**Why it is included.** To check for a length confound between the two prompt arms: "
        "if one arm is systematically more verbose than the other, that difference in raw length "
        "could itself explain part of any gap seen in the readability or comprehension metrics, "
        "rather than the prompt's plain-language framing being responsible."
    )
    entry.append(
        "**Limitations for this task.** Word count says nothing about whether the extra length "
        "is useful (e.g. more concrete remediation detail) or just padding, so it is read "
        "alongside the readability and comprehension metrics, not as a quality signal on its own."
    )
    entry.append("")
    entry.append("### LLM-as-judge (deferred)")
    entry.append("")
    entry.append(
        "LLM-as-judge scoring is part of this study's evaluation design but is not implemented "
        "in this stage. It is deferred to a later stage and is out of scope for "
        "`src/compute_metrics.py`."
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
    entry.append("| Flesch-Kincaid library | `textstat` 0.7.13, `flesch_kincaid_grade()` |")
    entry.append("| Dale-Chall library | `textstat` 0.7.13, `dale_chall_readability_score()` |")
    entry.append("| Word count method | `len(text.split())`, no external library |")
    entry.append("| Statistics library | `scipy` 1.18.0, `scipy.stats.wilcoxon` |")
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
    summary_texts = [extract_summary_text(r["output_text"]) for r in summaries]
    references = [nvd_descriptions[cve_id] for cve_id in cve_ids]

    print("Computing ROUGE-1/2/L...")
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    rouge_rows = compute_rouge_all(summary_texts, references, scorer)

    print(f"Computing BERTScore ({BERT_SCORE_MODEL})... (downloads model on first run)")
    bp, br, bf1 = compute_bertscore_all(summary_texts, references)

    print("Computing Flesch-Kincaid grade level (summaries and NVD baseline)...")
    fk_summary = [textstat.flesch_kincaid_grade(t) for t in summary_texts]
    nvd_by_cve = {cve_id: textstat.flesch_kincaid_grade(desc) for cve_id, desc in nvd_descriptions.items()}
    fk_nvd = [nvd_by_cve[cve_id] for cve_id in cve_ids]

    print("Computing Dale-Chall readability score (summaries and NVD baseline)...")
    dc_summary = [textstat.dale_chall_readability_score(t) for t in summary_texts]
    dc_nvd_by_cve = {cve_id: textstat.dale_chall_readability_score(desc) for cve_id, desc in nvd_descriptions.items()}
    dc_nvd = [dc_nvd_by_cve[cve_id] for cve_id in cve_ids]

    print("Computing word count (summaries)...")
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
            "fk_grade_summary": fk_summary,
            "fk_grade_nvd": fk_nvd,
            "dc_score_summary": dc_summary,
            "dc_score_nvd": dc_nvd,
            "word_count": word_counts,
        }
    )

    df.to_csv(OUT_CSV, index=False)
    df.to_json(OUT_JSON, orient="records", indent=2)
    print(f"Wrote {OUT_CSV} and {OUT_JSON} ({len(df)} rows).")

    # --- Analysis ---
    metric_cols = [
        "rouge1", "rouge2", "rougeL",
        "bertscore_precision", "bertscore_recall", "bertscore_f1",
        "fk_grade_summary", "dc_score_summary", "word_count",
    ]

    desc_rows = []
    for arm in ["persona", "baseline"]:
        sub = df.loc[df["arm"] == arm]
        for col in metric_cols:
            desc_rows.append(descriptive_row(sub[col], f"{METRIC_LABELS[col]} -- {arm}"))
    desc_rows.append(descriptive_row(list(nvd_by_cve.values()), "Flesch-Kincaid grade -- raw NVD description"))
    desc_rows.append(descriptive_row(list(dc_nvd_by_cve.values()), "Dale-Chall score -- raw NVD description"))

    persona_df = df.loc[df["arm"] == "persona"].set_index("cve_id").sort_index()
    baseline_df = df.loc[df["arm"] == "baseline"].set_index("cve_id").sort_index()
    assert list(persona_df.index) == list(baseline_df.index), "cve_id sets diverge between arms"

    persona_vs_baseline_rows = []
    for col in metric_cols:
        persona_vs_baseline_rows.append(
            paired_summary(persona_df[col].values, baseline_df[col].values, f"Persona {METRIC_LABELS[col]}", f"Baseline {METRIC_LABELS[col]}")
        )

    nvd_sorted = [nvd_by_cve[c] for c in persona_df.index]
    fk_vs_nvd_rows = [
        paired_summary(persona_df["fk_grade_summary"].values, nvd_sorted, "Persona summary FK", "Raw NVD FK"),
        paired_summary(baseline_df["fk_grade_summary"].values, nvd_sorted, "Baseline summary FK", "Raw NVD FK"),
    ]

    dc_nvd_sorted = [dc_nvd_by_cve[c] for c in persona_df.index]
    dc_vs_nvd_rows = [
        paired_summary(persona_df["dc_score_summary"].values, dc_nvd_sorted, "Persona summary Dale-Chall", "Raw NVD Dale-Chall"),
        paired_summary(baseline_df["dc_score_summary"].values, dc_nvd_sorted, "Baseline summary Dale-Chall", "Raw NVD Dale-Chall"),
    ]

    n_pairs = len(persona_df)

    md = []
    md.append("# Prompt Comparison: Automated Metrics\n\n")
    md.append(
        "This file reports evidence, not a verdict. It contains descriptive statistics, paired "
        "differences, and effect sizes only; interpretation of which prompt arm is \"better\" is "
        "left to the dissertation chapters.\n\n"
    )
    md.append(
        f"**Design:** paired, n={n_pairs} eval CVEs, 2 prompt arms (persona, baseline), same 24 "
        "CVEs in both arms. Small-N, exploratory. Paired significance tests below are reported "
        "as supporting evidence only, not as the primary claim, and no multiple-comparison "
        f"correction has been applied. **Note on sample size:** n={n_pairs} is small for any "
        "population-level inference; the Wilcoxon results should not be read as confirmatory "
        "hypothesis tests, only as a descriptive supplement to the effect sizes and raw "
        "differences.\n\n"
    )
    md.append("## Descriptive statistics\n\n")
    md.append(
        "Mean, median, SD, min, max for each metric, per prompt arm, and for the Flesch-Kincaid "
        "grade level of the raw NVD description (n=24, not split by arm since it is the same set "
        "of 24 descriptions in both arms).\n\n"
    )
    md.append(build_descriptive_table_md(desc_rows))
    md.append("\n")

    md.append("## Persona vs. baseline: paired differences\n\n")
    md.append(
        "Paired difference (persona minus baseline) per metric, matched by cve_id, n=24 pairs. "
        "Cohen's d (paired, d_z = mean diff / SD of diff) and Wilcoxon matched-pairs rank-biserial "
        "r are both reported as effect sizes; the Wilcoxon signed-rank test (W, p) is reported "
        "alongside as supporting evidence only.\n\n"
    )
    md.append(build_paired_table_md(persona_vs_baseline_rows))
    md.append("\n")

    md.append("## Summaries vs. raw NVD: Flesch-Kincaid paired difference\n\n")
    md.append(
        "Paired difference (summary FK minus raw NVD FK) per arm, matched by cve_id, n=24 pairs "
        "per arm. A negative mean difference means the summary scored a lower (easier) grade "
        "level than the raw NVD description for that CVE.\n\n"
    )
    md.append(build_paired_table_md(fk_vs_nvd_rows))
    md.append("\n")

    md.append("## Summaries vs. raw NVD: Dale-Chall paired difference\n\n")
    md.append(
        "Paired difference (summary Dale-Chall minus raw NVD Dale-Chall) per arm, matched by "
        "cve_id, n=24 pairs per arm. As with Flesch-Kincaid, a negative mean difference means the "
        "summary scored lower (easier, less reliant on unfamiliar vocabulary) than the raw NVD "
        "description for that CVE.\n\n"
    )
    md.append(build_paired_table_md(dc_vs_nvd_rows))
    md.append("\n")

    md.append("## Figures\n\n")
    md.append(f"See `{FIGURES_DIR}/` for PNG (300 dpi) and SVG versions of each figure below.\n\n")
    md.append("- `fk_grouped_nvd_persona_baseline` -- FK grade level, raw NVD vs. persona vs. baseline\n")
    md.append("- `bertscore_persona_vs_baseline` -- BERTScore F1 and precision, persona vs. baseline\n")
    md.append("- `rouge_persona_vs_baseline` -- ROUGE-1/2/L, persona vs. baseline\n")
    md.append("- `fk_paired_slope_nvd_to_summary` -- per-CVE paired FK change, raw NVD to summary\n")
    md.append("- `dc_grouped_nvd_persona_baseline` -- Dale-Chall score, raw NVD vs. persona vs. baseline\n")
    md.append("- `dc_paired_slope_nvd_to_summary` -- per-CVE paired Dale-Chall change, raw NVD to summary\n")
    md.append("- `word_count_persona_vs_baseline` -- word count, persona vs. baseline\n")

    Path(COMPARISON_MD).write_text("".join(md))
    print(f"Wrote {COMPARISON_MD}.")

    # --- Figures ---
    print("Generating figures...")
    figures_written = []
    figures_written += fig_fk_grouped(df, nvd_by_cve)
    figures_written += fig_bertscore(df)
    figures_written += fig_rouge(df)
    figures_written += fig_fk_paired_slope(df, nvd_by_cve)
    figures_written += fig_dc_grouped(df, dc_nvd_by_cve)
    figures_written += fig_dc_paired_slope(df, dc_nvd_by_cve)
    figures_written += fig_word_count(df)

    # --- Methodology log ---
    arm_counts = df["arm"].value_counts().to_dict()
    append_methodology_log(len(df), arm_counts, [OUT_CSV, OUT_JSON, COMPARISON_MD], figures_written)
    print(f"Appended 'Automated evaluation metrics' section to {METHODOLOGY_LOG_PATH}.")

    print()
    print("Done.")
    print(f"Rows processed: {len(df)}")
    print(
        f"Word count added to {OUT_CSV} and {OUT_JSON} (column: word_count)."
    )
    print(f"Files written: {OUT_CSV}, {OUT_JSON}, {COMPARISON_MD}, {METHODOLOGY_LOG_PATH} (appended)")
    print(f"Figures written: {len(figures_written)}")
    for p in figures_written:
        print(f"  {p}")
    print("New this run: word_count_persona_vs_baseline.png/.svg")
    print("Pinned versions:")
    print("  rouge-score 0.1.2")
    print(f"  bert-score 0.3.13 (model={BERT_SCORE_MODEL}, layers={BERT_SCORE_NUM_LAYERS}, idf=False)")
    print("  textstat 0.7.13 (flesch_kincaid_grade, dale_chall_readability_score)")
    print("  scipy 1.18.0")


if __name__ == "__main__":
    main()
