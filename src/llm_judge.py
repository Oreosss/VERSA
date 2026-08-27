"""LLM-as-judge evaluation of the bullet-format summaries (Stage 6e).

Scores all 24 eval CVEs across three arms (persona summary, baseline summary,
raw NVD description) on two dimensions using an OpenAI model as an
independent judge:

- Comprehension support: scored on the text alone, no reference supplied.
  Operationalises Endsley Level 2 comprehension (what is vulnerable / how it
  is exploited / remediation scope).
- Faithfulness to source: scored with the target CVE's own raw NVD
  description supplied as reference. For the raw NVD arm itself, the
  reference is its own text (a control condition).

The judge (OpenAI) is a different provider from the generator (Anthropic,
`claude-opus-4-6`, see `src/generate_summaries.py`), chosen specifically to
avoid self-evaluation bias.

Blinding: the model is never told which arm (persona/baseline/raw NVD) a text
belongs to -- every call presents the text under a neutral "TEXT TO SCORE"
label with no framing about its origin. This is a stronger form of blinding
than a swapped A/B label inside the prompt, since the model has no arm
identity to key off in the first place. A/B labelling still happens at the
bookkeeping layer: `llm_judge_raw.json` (this script's primary output) never
contains the words "persona" or "baseline", only a per-CVE label A/B (for
persona/baseline) or "nvd". The true mapping is written separately to
`llm_judge_mapping.json` and is only rejoined during aggregation in this same
script, so a reader of the raw file alone cannot infer which arm produced
which score without the separate mapping file.

Multi-pass: each (CVE, arm, dimension) is scored 3 times at temperature 0 to
evidence stability, since some backends are not perfectly deterministic even
at temperature 0.

Resumable: a (cve_id, label, dimension, pass) tuple already present in
`llm_judge_raw.json` is skipped, not re-scored.
"""

import hashlib
import json
import os
import random
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import openai
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

matplotlib.use("Agg")

# Serif font for the judge-scores figure, with fallbacks.
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = [
    "Times New Roman",
    "Times",
    "CMU Serif",
    "DejaVu Serif",
]
plt.rcParams["axes.unicode_minus"] = False

EVAL_SAMPLE_PATH = "data/eval_sample.jsonl"
SUMMARIES_PATH = "v2_bullet/summaries/summaries_bullet.json"
RUBRIC_PATHS = {
    "comprehension": "v2_bullet/rubric/rubric_comprehension.txt",
    "faithfulness": "v2_bullet/rubric/rubric_faithfulness.txt",
}
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"

JUDGE_DIR = Path("v2_bullet/judge")
RAW_PATH = JUDGE_DIR / "llm_judge_raw.json"
MAPPING_PATH = JUDGE_DIR / "llm_judge_mapping.json"
PER_TEXT_PATH = JUDGE_DIR / "llm_judge_per_text.csv"
AGGREGATE_JSON_PATH = JUDGE_DIR / "llm_judge_aggregate.json"
COMPARISON_MD_PATH = JUDGE_DIR / "LLM_JUDGE_COMPARISON.md"
FIGURES_DIR = Path("v2_bullet/figures")

MODEL = "gpt-4.1-2025-04-14"
TEMPERATURE = 0
N_PASSES = 3
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
RANDOM_SEED = 42  # consistent with the project's random.Random(42) convention

ARMS = ("persona", "baseline", "nvd")
DIMENSIONS = ("comprehension", "faithfulness")

REFERENCE_SECTION_RE = re.compile(r"\n\s*(?:##\s*Reference\b|\*\*Reference\*\*)", re.IGNORECASE)

COLOR_NVD = "#2a78d6"
COLOR_PERSONA = "#008300"
COLOR_BASELINE = "#4a3aa7"
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

ARM_DISPLAY = {"nvd": "Raw NVD", "persona": "Persona", "baseline": "Baseline"}
ARM_COLOR = {"nvd": COLOR_NVD, "persona": COLOR_PERSONA, "baseline": COLOR_BASELINE}
DIMENSION_LABEL = {"comprehension": "Comprehension support score (1-5)", "faithfulness": "Faithfulness to source score (1-5)"}
PANEL_TITLE = {"comprehension": "Comprehension support", "faithfulness": "Faithfulness"}


def extract_summary_text(output_text):
    match = REFERENCE_SECTION_RE.search(output_text)
    body = output_text[: match.start()] if match else output_text
    return body.strip()


def load_eval_sample(path):
    records = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            records[rec["id"]] = rec["description"]
    if not records:
        raise SystemExit(f"STOP: {path} is empty.")
    return records


def load_summaries(path):
    with open(path) as f:
        records = json.load(f)
    by_cve = {}
    for r in records:
        by_cve.setdefault(r["cve_id"], {})[r["prompt_version"]] = r["output_text"]
    for cve_id, arms in by_cve.items():
        if "persona" not in arms or "baseline" not in arms:
            raise SystemExit(f"STOP: {cve_id} is missing a persona or baseline record in {path}.")
    return by_cve


def load_rubrics(paths):
    texts = {}
    hashes = {}
    for dimension, path in paths.items():
        raw = Path(path).read_bytes()
        text = raw.decode("utf-8")
        if "{text}" not in text:
            raise SystemExit(f"STOP: {path} is missing the {{text}} placeholder.")
        if dimension == "faithfulness" and "{reference}" not in text:
            raise SystemExit(f"STOP: {path} is missing the {{reference}} placeholder.")
        texts[dimension] = text
        hashes[dimension] = hashlib.sha256(raw).hexdigest()
    return texts, hashes


def build_mapping(cve_ids, rng):
    mapping = {}
    for cve_id in sorted(cve_ids):
        if rng.random() < 0.5:
            mapping[cve_id] = {"A": "persona", "B": "baseline"}
        else:
            mapping[cve_id] = {"A": "baseline", "B": "persona"}
    return mapping


def label_for_arm(mapping, cve_id, arm):
    if arm == "nvd":
        return "nvd"
    entry = mapping[cve_id]
    return "A" if entry["A"] == arm else "B"


def arm_for_label(mapping, cve_id, label):
    if label == "nvd":
        return "nvd"
    return mapping[cve_id][label]


def load_json_list(path):
    if not Path(path).exists():
        return []
    with open(path) as f:
        return json.load(f)


def write_json_atomic(obj, path):
    tmp = Path(path).with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    tmp.replace(path)


def call_judge(client, prompt_text):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt_text}],
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            score = parsed["score"]
            justification = parsed["justification"]
            if not isinstance(score, int) or not (1 <= score <= 5):
                raise ValueError(f"score out of range or non-integer: {score!r}")
            if not isinstance(justification, str) or not justification.strip():
                raise ValueError("justification missing or empty")
            return response.model, score, justification
        except (openai.RateLimitError, openai.APIConnectionError) as e:
            last_error = e
        except openai.APIStatusError as e:
            if e.status_code >= 500:
                last_error = e
            else:
                raise
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = e

        if attempt < MAX_RETRIES:
            wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"    retryable error ({last_error}), retrying in {wait:.0f}s ({attempt}/{MAX_RETRIES})...")
            time.sleep(wait)

    raise RuntimeError(f"all {MAX_RETRIES} retries exhausted: {last_error}")


def cohens_d_paired(diff):
    return float(np.mean(diff) / np.std(diff, ddof=1))


def paired_summary(a, b, label_a, label_b):
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
    result["cohens_dz"] = cohens_d_paired(diff) if n > 1 and np.std(diff, ddof=1) > 0 else float("nan")
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
    png_path = FIGURES_DIR / f"{name}.png"
    svg_path = FIGURES_DIR / f"{name}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    return [str(png_path), str(svg_path)]


FIGURE_ARM_ORDER = ("persona", "baseline", "nvd")


def fig_judge_scores(per_text_means):
    stats = {}
    for arm in FIGURE_ARM_ORDER:
        for dimension in DIMENSIONS:
            arr = np.asarray(per_text_means[(arm, dimension)], dtype=float)
            stats[(arm, dimension)] = {
                "mean": float(np.mean(arr)),
                "sd": float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan"),
            }

    # Axis capped at the 1-5 score range, but ylim extends a bit past 5.0 so
    # every label sits above its bar/error-bar the same way, including
    # ceiling bars (mean 5.00, SD 0.00) that would otherwise clip past the
    # axis top. Ticks are pinned to 1-5 so that headroom doesn't add a
    # stray tick above 5.
    y_lo, y_hi = 1.0, 5.35

    fig, axes = plt.subplots(1, 2, figsize=(9, 4.5), sharey=True)
    for ax, dimension in zip(axes, DIMENSIONS):
        x = np.arange(len(FIGURE_ARM_ORDER))
        means = [stats[(arm, dimension)]["mean"] for arm in FIGURE_ARM_ORDER]
        sds = [stats[(arm, dimension)]["sd"] for arm in FIGURE_ARM_ORDER]
        colors = [ARM_COLOR[arm] for arm in FIGURE_ARM_ORDER]
        bars = ax.bar(
            x,
            means,
            width=0.55,
            yerr=sds,
            capsize=3,
            color=colors,
            alpha=0.75,
            edgecolor=colors,
            zorder=3,
        )
        for bar, mean, sd in zip(bars, means, sds):
            top_of_errorbar = mean + (sd if not np.isnan(sd) else 0.0)
            ax.text(bar.get_x() + bar.get_width() / 2, top_of_errorbar + 0.08, f"{mean:.2f}",
                     ha="center", va="bottom", fontsize=9, color=TEXT_PRIMARY)
        ax.set_xticks(x)
        ax.set_xticklabels([ARM_DISPLAY[arm] for arm in FIGURE_ARM_ORDER])
        ax.set_ylim(y_lo, y_hi)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_title(PANEL_TITLE[dimension], fontsize=10, color=TEXT_PRIMARY)
        style_axes(ax)
    axes[0].set_ylabel("Judge score (1-5, mean of 3 passes)")
    fig.suptitle("Independent judge scores, by text", fontsize=11, color=TEXT_PRIMARY)
    fig.tight_layout()

    print("LLM-as-judge means and SDs (per_text_means, n=24 per cell):")
    for dimension in DIMENSIONS:
        for arm in FIGURE_ARM_ORDER:
            s = stats[(arm, dimension)]
            print(f"  {ARM_DISPLAY[arm]:<10} {dimension:<14} mean={s['mean']:.2f}  sd={s['sd']:.2f}")

    return save_figure(fig, "llm_judge_scores_bullet")


def append_methodology_log(rubric_texts, rubric_hashes, n_calls_made, n_calls_skipped, n_failed, run_timestamp):
    comprehension_rubric = rubric_texts["comprehension"].replace("{text}", "<text under evaluation>")
    faithfulness_rubric = rubric_texts["faithfulness"].replace(
        "{reference}", "<target CVE's raw NVD description>"
    ).replace("{text}", "<text under evaluation>")

    entry = []
    entry.append("")
    entry.append("")
    entry.append(f"## Stage 6e -- LLM-as-Judge Evaluation ({date.today().isoformat()})")
    entry.append("")
    entry.append("**Script:** `src/llm_judge.py`")
    entry.append(
        f"**Outputs:** `{RAW_PATH}`, `{MAPPING_PATH}`, `{PER_TEXT_PATH}`, `{AGGREGATE_JSON_PATH}`, "
        f"`{COMPARISON_MD_PATH}`, figures in `{FIGURES_DIR}/`"
    )
    entry.append("")
    entry.append(
        f"Scored all 24 eval CVEs across three arms (persona summary, baseline summary, raw NVD "
        f"description; `{SUMMARIES_PATH}` and `{EVAL_SAMPLE_PATH}`) on two dimensions "
        "(comprehension support, faithfulness to source) using an OpenAI model as judge, run 3 "
        f"times per text per dimension at temperature {TEMPERATURE}. "
        f"{3 * len(DIMENSIONS) * len(ARMS) * 24} judge calls in the full design; "
        f"{n_calls_made} made this run, {n_calls_skipped} already present (resumed), "
        f"{n_failed} failed after retries."
    )
    entry.append("")
    entry.append("### Judge model and independence rationale")
    entry.append("")
    entry.append(
        f"**Judge model:** `{MODEL}`, temperature {TEMPERATURE}, pinned by exact dated snapshot for "
        "reproducibility, mirroring the fixed model/temperature discipline used for generation "
        "(Stage 6c). The judge is deliberately drawn from a different provider (OpenAI) than the "
        "generator (Anthropic, `claude-opus-4-6`), so that the model producing a summary is never "
        "the same model scoring it. This avoids self-evaluation bias: an LLM judge from the same "
        "family as the generator has been shown in the literature to rate outputs in its own "
        "stylistic register more favourably, independent of actual quality."
    )
    entry.append("")
    entry.append("### Rubric (verbatim, locked and hashed)")
    entry.append("")
    entry.append(f"- Comprehension rubric hash: `{rubric_hashes['comprehension']}` (`{RUBRIC_PATHS['comprehension']}`)")
    entry.append(f"- Faithfulness rubric hash: `{rubric_hashes['faithfulness']}` (`{RUBRIC_PATHS['faithfulness']}`)")
    entry.append("")
    entry.append("**Comprehension rubric** (scored on the text alone, no reference supplied):")
    entry.append("")
    entry.append("```")
    entry.append(comprehension_rubric.strip())
    entry.append("```")
    entry.append("")
    entry.append("**Faithfulness rubric** (scored with the target CVE's own raw NVD description as reference):")
    entry.append("")
    entry.append("```")
    entry.append(faithfulness_rubric.strip())
    entry.append("```")
    entry.append("")
    entry.append("### Split call design: why comprehension and faithfulness use different setups")
    entry.append("")
    entry.append(
        "The two dimensions measure different things and are deliberately scored with different "
        "call setups rather than a single combined prompt. Comprehension support is scored on the "
        "candidate text alone, with no reference material supplied, because it operationalises "
        "Endsley Level 2 situational-comprehension: whether a technically capable non-security "
        "reader could understand what is vulnerable, how it is exploited, and the remediation "
        "scope from that text by itself. Supplying the raw NVD description alongside it would let "
        "the judge fill comprehension gaps in the summary using the reference, which is not what a "
        "real reader of the summary alone could do. Faithfulness to source, conversely, is only "
        "meaningful relative to a ground truth, so it is scored with the target CVE's own raw NVD "
        "description supplied as reference material, and the rubric explicitly instructs the judge "
        "not to credit a claim as supported unless it is present in that specific reference (a "
        "claim that happens to be true of a neighbouring or similar CVE, but absent from this "
        "CVE's own description, is marked unsupported). For the raw NVD arm itself, faithfulness "
        "is scored against its own text as a control: this is expected to score at or near the top "
        "of the scale, and functions as a sanity check on the rubric and the judge rather than a "
        "result of interest."
    )
    entry.append("")
    entry.append("### Blinding and multi-pass design")
    entry.append("")
    entry.append(
        "The judge is never told which arm (persona, baseline, or raw NVD) a text belongs to; every "
        "call presents the text under a neutral \"TEXT TO SCORE\" label with no framing about its "
        "origin, generation method, or source. This is a stronger form of blinding than swapping "
        "labels inside the prompt, since the model is given no arm identity to key off in the "
        "first place. A/B labelling is applied at the bookkeeping layer only: for each CVE, which "
        "of persona/baseline is \"A\" is randomised (`random.Random(42)`, consistent with this "
        "project's existing sampling-seed convention), and the raw per-call output file "
        f"(`{RAW_PATH}`) records only the label (A, B, or nvd for the raw-NVD arm), never the "
        f"words \"persona\" or \"baseline\" directly. The true mapping is written to a separate "
        f"file (`{MAPPING_PATH}`) and is only rejoined with the raw scores during aggregation in "
        "this same script, so the raw judge output is anonymised as an artefact in its own right, "
        "not just at prompt-construction time. The order in which the full set of "
        "(CVE, arm, dimension, pass) calls is dispatched is also randomised per run "
        "(`random.Random(42).shuffle`), rather than processed CVE-by-CVE or arm-by-arm in a fixed "
        "sequence, as a conservative mitigation against any incidental ordering effect, even though "
        "each call is an independent, stateless API request. Each (CVE, arm, dimension) is scored "
        f"{N_PASSES} times at temperature {TEMPERATURE} to evidence stability: every pass, score, "
        f"and justification is retained in `{RAW_PATH}`, and per-text mean and standard deviation "
        "across passes are reported rather than a single-shot score, since some model backends are "
        "not perfectly deterministic even at temperature 0."
    )
    entry.append("")
    entry.append("### Aggregation and framing")
    entry.append("")
    entry.append(
        "Per-text scores (mean of 3 passes) are aggregated to per-arm means, standard deviations, "
        "and paired Cohen's d effect sizes (persona vs. raw NVD, baseline vs. raw NVD, persona vs. "
        "baseline), matched by CVE, for both dimensions, following the same descriptive-statistics-"
        "and-effect-sizes-only framing used throughout this evaluation stage (Stage 6d): exploratory "
        "and small-N (24 CVEs), no significance claims."
    )
    entry.append("")
    entry.append("### Pros and limitations of LLM-as-judge")
    entry.append("")
    entry.append(
        "**Pros.** LLM-as-judge scales to scoring dimensions (comprehension, faithfulness) that "
        "automated lexical/embedding metrics (ROUGE, BERTScore) cannot directly measure, since both "
        "require reading comprehension and claim-level fact-checking rather than surface or "
        "embedding similarity. It is far cheaper and faster than recruiting human raters for every "
        "candidate text, and the 3-pass design gives a direct, reportable measure of its own "
        "scoring stability, which a single human rating would not."
    )
    entry.append("")
    entry.append(
        "**Limitations, and how this design mitigates them where possible:**"
    )
    entry.append("")
    entry.append(
        "- *Self-evaluation / self-preference bias.* An LLM judge tends to rate text in its own "
        "stylistic register more favourably. Mitigated by using a judge from a different provider "
        "(OpenAI) than the generator (Anthropic)."
    )
    entry.append(
        "- *Position bias.* LLM judges asked to directly compare two options in the same call are "
        "known to favour whichever option is presented first (or second). This design avoids "
        "pairwise comparison entirely: every call scores exactly one text in isolation against a "
        "fixed rubric, so there is no position for the judge to be biased by. The residual "
        "processing-order randomisation (above) is a conservative extra measure, not a correction "
        "for a comparison the design does not otherwise perform."
    )
    entry.append(
        "- *Verbosity bias.* LLM judges are known to rate longer, more elaborated text more "
        "favourably independent of actual quality, which matters here since the persona and "
        "baseline prompt arms produce summaries of different typical length (see word-count "
        "results, Stage 6d). The rubric anchors are written around concrete, checkable content "
        "criteria (whether what/how/remediation-scope is present and clear, or whether specific "
        "claims are supported) rather than an open-ended holistic quality judgement, and explicitly "
        "instructs the judge not to score brevity or style. This reduces but cannot fully eliminate "
        "the risk that a more elaborate summary scores higher for its length rather than its "
        "content; it is noted here as a residual limitation rather than a solved problem."
    )
    entry.append(
        "- *Leniency/severity clustering and imperfect determinism.* LLM judges can cluster scores "
        "toward one end of a scale, and are not guaranteed to be perfectly deterministic even at "
        "temperature 0 depending on backend. Mitigated empirically, not assumed away, by running "
        "3 passes per text per dimension and reporting the observed mean and standard deviation "
        f"rather than a single score; see `{PER_TEXT_PATH}` for the per-text spread actually "
        "observed."
    )
    entry.append(
        "- *No ground truth for comprehension.* Unlike faithfulness, which has the raw NVD "
        "description as a reference, there is no independent ground truth for what a real "
        "technically capable non-security reader would understand. The comprehension score is "
        "this judge model's estimate of that, not a measurement of an actual reader; the "
        "questionnaire-based human evaluation (Stage 8, not yet run) is the check on this "
        "dimension that LLM-as-judge alone cannot provide."
    )
    entry.append("")
    entry.append(f"- Run timestamp: {run_timestamp}")
    entry.append("")

    with open(METHODOLOGY_LOG_PATH, "a") as f:
        f.write("\n".join(entry))


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("STOP: OPENAI_API_KEY not set (add it to .env).")

    print(f"Loading eval sample from {EVAL_SAMPLE_PATH}...")
    nvd_descriptions = load_eval_sample(EVAL_SAMPLE_PATH)
    print(f"Loaded {len(nvd_descriptions)} eval CVE descriptions.")

    print(f"Loading summaries from {SUMMARIES_PATH}...")
    summaries = load_summaries(SUMMARIES_PATH)
    cve_ids = sorted(summaries.keys())
    missing = [c for c in cve_ids if c not in nvd_descriptions]
    if missing:
        raise SystemExit(f"STOP: {missing} present in summaries but not in {EVAL_SAMPLE_PATH}.")
    print(f"Loaded summaries for {len(cve_ids)} CVEs.")

    print("Loading and hashing rubric templates...")
    rubric_texts, rubric_hashes = load_rubrics(RUBRIC_PATHS)

    JUDGE_DIR.mkdir(parents=True, exist_ok=True)

    rng = random.Random(RANDOM_SEED)
    if Path(MAPPING_PATH).exists():
        with open(MAPPING_PATH) as f:
            mapping = json.load(f)
        print(f"Loaded existing A/B mapping from {MAPPING_PATH}.")
    else:
        mapping = build_mapping(cve_ids, rng)
        write_json_atomic(mapping, MAPPING_PATH)
        print(f"Generated and wrote new A/B mapping to {MAPPING_PATH}.")

    texts_by_arm = {}
    for cve_id in cve_ids:
        texts_by_arm[(cve_id, "persona")] = extract_summary_text(summaries[cve_id]["persona"])
        texts_by_arm[(cve_id, "baseline")] = extract_summary_text(summaries[cve_id]["baseline"])
        texts_by_arm[(cve_id, "nvd")] = nvd_descriptions[cve_id]

    existing = load_json_list(RAW_PATH)
    completed = {(r["cve_id"], r["label"], r["dimension"], r["pass"]) for r in existing}
    print(f"Found {len(existing)} existing judge record(s) in {RAW_PATH}.")

    units = []
    for cve_id in cve_ids:
        for arm in ARMS:
            label = label_for_arm(mapping, cve_id, arm)
            for dimension in DIMENSIONS:
                for pass_n in range(1, N_PASSES + 1):
                    units.append((cve_id, arm, label, dimension, pass_n))
    rng.shuffle(units)

    client = OpenAI(api_key=api_key)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    made = 0
    skipped = 0
    failed = []

    for cve_id, arm, label, dimension, pass_n in units:
        key = (cve_id, label, dimension, pass_n)
        if key in completed:
            skipped += 1
            continue

        text = texts_by_arm[(cve_id, arm)]
        prompt = rubric_texts[dimension].replace("{text}", text)
        if dimension == "faithfulness":
            prompt = prompt.replace("{reference}", nvd_descriptions[cve_id])

        print(f"Scoring {cve_id} [{arm}/{label}] {dimension} pass {pass_n}...")
        try:
            model_used, score, justification = call_judge(client, prompt)
        except Exception as e:
            print(f"  FAILED after retries: {e}")
            failed.append(f"{cve_id}:{label}:{dimension}:{pass_n}")
            continue

        record = {
            "cve_id": cve_id,
            "label": label,
            "dimension": dimension,
            "pass": pass_n,
            "score": score,
            "justification": justification,
            "model": model_used,
            "temperature": TEMPERATURE,
            "rubric_hash": rubric_hashes[dimension],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        existing.append(record)
        write_json_atomic(existing, RAW_PATH)
        completed.add(key)
        made += 1

    print()
    print(f"Done scoring. Made: {made}, skipped (resumed): {skipped}, failed: {len(failed)}")
    if failed:
        print(f"  Failed keys: {failed}")
        raise SystemExit(
            f"STOP: {len(failed)} judge call(s) failed after retries; re-run to resume once resolved."
        )

    # --- De-anonymise and aggregate ---
    print("Aggregating scores (de-anonymising via mapping)...")
    per_call_rows = []
    for r in existing:
        arm = arm_for_label(mapping, r["cve_id"], r["label"])
        per_call_rows.append({**r, "arm": arm})

    per_text = {}
    for row in per_call_rows:
        key = (row["cve_id"], row["arm"], row["dimension"])
        per_text.setdefault(key, []).append(row["score"])

    per_text_rows = []
    for (cve_id, arm, dimension), scores in sorted(per_text.items()):
        arr = np.asarray(scores, dtype=float)
        per_text_rows.append(
            {
                "cve_id": cve_id,
                "arm": arm,
                "dimension": dimension,
                "n_passes": len(arr),
                "mean_score": float(np.mean(arr)),
                "sd_score": float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan"),
                "scores": scores,
            }
        )

    per_text_df = pd.DataFrame(per_text_rows)
    per_text_df.to_csv(PER_TEXT_PATH, index=False)
    print(f"Wrote {PER_TEXT_PATH} ({len(per_text_df)} rows).")

    per_text_means = {}
    for arm in ARMS:
        for dimension in DIMENSIONS:
            sub = per_text_df[(per_text_df["arm"] == arm) & (per_text_df["dimension"] == dimension)]
            sub = sub.set_index("cve_id").sort_index()
            per_text_means[(arm, dimension)] = sub["mean_score"].tolist()
            per_text_means[(arm, dimension, "index")] = list(sub.index)

    desc_rows = []
    for dimension in DIMENSIONS:
        for arm in ARMS:
            desc_rows.append(
                descriptive_row(per_text_means[(arm, dimension)], f"{arm} -- {dimension}")
            )

    comparisons = []
    for dimension in DIMENSIONS:
        cve_order = per_text_means[("persona", dimension, "index")]
        assert cve_order == per_text_means[("baseline", dimension, "index")] == per_text_means[("nvd", dimension, "index")], \
            "cve_id sets diverge between arms"
        persona_scores = per_text_means[("persona", dimension)]
        baseline_scores = per_text_means[("baseline", dimension)]
        nvd_scores = per_text_means[("nvd", dimension)]
        comparisons.append(paired_summary(persona_scores, nvd_scores, f"Persona {dimension}", f"NVD {dimension}"))
        comparisons.append(paired_summary(baseline_scores, nvd_scores, f"Baseline {dimension}", f"NVD {dimension}"))
        comparisons.append(paired_summary(persona_scores, baseline_scores, f"Persona {dimension}", f"Baseline {dimension}"))

    aggregate = {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "n_passes": N_PASSES,
        "rubric_hashes": rubric_hashes,
        "descriptive": desc_rows,
        "paired_comparisons": comparisons,
    }
    write_json_atomic(aggregate, AGGREGATE_JSON_PATH)
    print(f"Wrote {AGGREGATE_JSON_PATH}.")

    # --- Markdown report ---
    def build_descriptive_table_md(rows):
        header = "| Arm / dimension | N | Mean | Median | SD | Min | Max |\n|---|---|---|---|---|---|---|\n"
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

    md = []
    md.append("# LLM-as-Judge Comparison: Comprehension and Faithfulness (v2, bullet format)\n\n")
    md.append(
        "This file reports evidence, not a verdict. Descriptive statistics and paired Cohen's d "
        "effect sizes only, exploratory and small-N (n=24 eval CVEs). Judge model "
        f"`{MODEL}`, temperature {TEMPERATURE}, {N_PASSES} passes per text per dimension. See "
        "METHODOLOGY_LOG.md \"Stage 6e\" for the rubric verbatim, the blinding and multi-pass "
        "design, and the pros/limitations of LLM-as-judge as a method.\n\n"
    )
    md.append("## Descriptive statistics\n\n")
    md.append("Per-arm, per-dimension mean judge score (1-5), computed from each text's mean across 3 passes, n=24.\n\n")
    md.append(build_descriptive_table_md(desc_rows))
    md.append("\n")
    md.append("## Paired comparisons\n\n")
    md.append("Matched by CVE, n=24 pairs. Persona vs. NVD, baseline vs. NVD, and persona vs. baseline, for each dimension.\n\n")
    md.append(build_paired_table_md(comparisons))
    md.append("\n")
    md.append("## Figures\n\n")
    md.append(f"See `{FIGURES_DIR}/` for PNG (300 dpi) and SVG versions.\n\n")
    md.append("- `llm_judge_scores_bullet` -- comprehension and faithfulness scores, raw NVD vs. persona vs. baseline\n")

    COMPARISON_MD_PATH.write_text("".join(md))
    print(f"Wrote {COMPARISON_MD_PATH}.")

    # --- Figure ---
    print("Generating figure...")
    per_text_means_for_fig = {
        (arm, dimension): per_text_means[(arm, dimension)] for arm in ARMS for dimension in DIMENSIONS
    }
    figures_written = fig_judge_scores(per_text_means_for_fig)
    for p in figures_written:
        print(f"  {p}")

    # --- Methodology log ---
    if made > 0:
        append_methodology_log(rubric_texts, rubric_hashes, made, skipped, len(failed), run_timestamp)
        print(f"Appended 'Stage 6e' section to {METHODOLOGY_LOG_PATH}.")
    else:
        print(f"No new judge calls this run; not re-appending to {METHODOLOGY_LOG_PATH}.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
