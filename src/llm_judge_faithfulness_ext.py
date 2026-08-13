"""Faithfulness sensitivity check (Stage 6f): description-only reference vs.
description+CVSS reference.

Stage 6e's faithfulness dimension scored each summary against the target
CVE's bare `description` field only. That reference excludes the CVSS
sub-fields (attack vector, attack complexity, privileges required, user
interaction, CIA impact, CVSS score/severity) even though
`generate_summaries.py`'s `build_target_cve_block()` supplies those fields to
the generator directly, as structured data alongside the description, and
both prompt templates instruct the model to use them. Inspecting Stage 6e's
raw justifications confirmed this: most "unsupported claim" flags on the
persona/baseline arms were the judge correctly following its rubric (only
credit a claim if it's in the reference) while marking real, sourced
CVSS-derived restatements as unsupported, because they were not literally in
the bare description string being used as the reference.

This script re-scores faithfulness only (comprehension is unaffected, since
it is not reference-based) using an EXPANDED reference: the description plus
the CVSS sub-fields, i.e. the same fields the generator was actually given,
minus two categories deliberately excluded:

- KEV listed / EPSS score: these are external enrichment this project's own
  pipeline joined on from CISA and FIRST, not something NVD itself publishes
  on the record, and both prompt templates explicitly forbid the model from
  describing or interpreting them in the summary text. Including them in the
  faithfulness reference would blur "faithful to NVD" with "faithful to this
  project's own enrichment," a different claim. Excluded.
- Neighbour CVEs: the original Stage 6e brief was explicit that a claim
  supported only by a neighbouring CVE must not be credited as faithful.
  Still excluded here for the same reason.

The CVSS sub-fields (attack vector, complexity, privileges required, user
interaction, CIA impact, CVSS score/severity), by contrast, are native NVD
record data: they come from the same `cvssMetricV31` block on the same NVD
record as the description, just a different field on it. Including them in
the reference tests a stricter, more meaningful hallucination question ("did
the summary invent or misstate anything beyond the full structured NVD
record it was given") rather than the narrower Stage 6e question ("does the
summary hold up against just the free-text description paragraph a reader
would see").

Both results are kept and reported side by side, not merged or overwritten:
Stage 6e's original (narrow-reference) scores remain valid evidence for its
own question and are reused directly from `llm_judge_per_text.csv` rather
than re-queried. This script only makes new API calls for the extended
reference (216 calls: 24 CVEs x 3 arms x 3 passes; faithfulness only).

Same A/B mapping, same blinding design (model never told which arm a text
belongs to), same multi-pass (3 passes, temperature 0) discipline as Stage
6e. See `src/llm_judge.py` for the full original design writeup.
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

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "CMU Serif", "DejaVu Serif"]
plt.rcParams["axes.unicode_minus"] = False

EVAL_SAMPLE_PATH = "data/eval_sample.jsonl"
SUMMARIES_PATH = "v2_bullet/summaries/summaries_bullet.json"
RUBRIC_PATH = "v2_bullet/rubric/rubric_faithfulness.txt"
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"

JUDGE_DIR = Path("v2_bullet/judge")
MAPPING_PATH = JUDGE_DIR / "llm_judge_mapping.json"
ORIGINAL_PER_TEXT_PATH = JUDGE_DIR / "llm_judge_per_text.csv"

RAW_EXT_PATH = JUDGE_DIR / "llm_judge_raw_faithfulness_ext.json"
PER_TEXT_EXT_PATH = JUDGE_DIR / "llm_judge_per_text_faithfulness_ext.csv"
COMPARISON_MD_PATH = JUDGE_DIR / "LLM_JUDGE_FAITHFULNESS_EXT_COMPARISON.md"
FIGURES_DIR = Path("v2_bullet/figures")

MODEL = "gpt-4.1-2025-04-14"
TEMPERATURE = 0
N_PASSES = 3
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
RANDOM_SEED = 43  # distinct from Stage 6e's seed (42) for this run's own processing-order shuffle

ARMS = ("persona", "baseline", "nvd")

REFERENCE_SECTION_RE = re.compile(r"\n\s*(?:##\s*Reference\b|\*\*Reference\*\*)", re.IGNORECASE)

COLOR_NVD = "#2a78d6"
COLOR_PERSONA = "#008300"
COLOR_BASELINE = "#4a3aa7"
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

ARM_DISPLAY = {"nvd": "Raw NVD\ndescription", "persona": "Persona\nsummary", "baseline": "Baseline\nsummary"}
ARM_COLOR = {"nvd": COLOR_NVD, "persona": COLOR_PERSONA, "baseline": COLOR_BASELINE}

# CVSS sub-fields included in the extended reference, in the order they are
# rendered. KEV/EPSS deliberately excluded, see module docstring.
CVSS_REFERENCE_FIELDS = [
    ("attack_vector", "Attack vector"),
    ("attack_complexity", "Attack complexity"),
    ("privileges_required", "Privileges required"),
    ("user_interaction", "User interaction"),
    ("confidentiality_impact", "Confidentiality impact"),
    ("integrity_impact", "Integrity impact"),
    ("availability_impact", "Availability impact"),
]


def build_extended_reference(rec):
    lines = [rec["description"]]
    conditions = [f"{label}: {rec[field]}" for field, label in CVSS_REFERENCE_FIELDS if rec.get(field) is not None]
    if conditions:
        lines.append(" | ".join(conditions))
    if rec.get("cvss_score") is not None and rec.get("cvss_severity") is not None:
        lines.append(f"CVSS score: {rec['cvss_score']} ({rec['cvss_severity']})")
    return "\n".join(lines)


def extract_summary_text(output_text):
    match = REFERENCE_SECTION_RE.search(output_text)
    body = output_text[: match.start()] if match else output_text
    return body.strip()


def load_eval_sample(path):
    records = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            records[rec["id"]] = rec
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


def load_rubric(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8")
    if "{text}" not in text or "{reference}" not in text:
        raise SystemExit(f"STOP: {path} is missing the {{text}} or {{reference}} placeholder.")
    return text, hashlib.sha256(raw).hexdigest()


def arm_for_label(mapping, cve_id, label):
    if label == "nvd":
        return "nvd"
    return mapping[cve_id][label]


def label_for_arm(mapping, cve_id, arm):
    if arm == "nvd":
        return "nvd"
    entry = mapping[cve_id]
    return "A" if entry["A"] == arm else "B"


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
        flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "none", "markeredgecolor": TEXT_SECONDARY},
        zorder=3,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)
    return bp


def save_figure(fig, name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / f"{name}.png"
    svg_path = FIGURES_DIR / f"{name}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    return [str(png_path), str(svg_path)]


FIGURE_ARM_ORDER = ("nvd", "persona", "baseline")


def fig_extended_scores(per_text_means):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    groups = [per_text_means[arm] for arm in FIGURE_ARM_ORDER]
    labels = [ARM_DISPLAY[arm] for arm in FIGURE_ARM_ORDER]
    colors = [ARM_COLOR[arm] for arm in FIGURE_ARM_ORDER]
    boxplot(ax, groups, labels, colors)
    ax.set_ylim(0.5, 5.5)
    ax.set_ylabel("Faithfulness score (1-5, mean of 3 passes)")
    ax.set_title("Faithfulness vs. description+CVSS reference, by text", fontsize=11, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "llm_judge_faithfulness_ext_bullet")


def fig_original_vs_extended(original_by_arm_cve, extended_by_arm_cve):
    fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
    for ax, arm, color in [(axes[0], "persona", COLOR_PERSONA), (axes[1], "baseline", COLOR_BASELINE)]:
        cve_ids = sorted(original_by_arm_cve[arm].keys())
        orig_vals = [original_by_arm_cve[arm][c] for c in cve_ids]
        ext_vals = [extended_by_arm_cve[arm][c] for c in cve_ids]
        for o, e in zip(orig_vals, ext_vals):
            ax.plot([0, 1], [o, e], color=color, alpha=0.5, linewidth=1, zorder=2)
        ax.scatter([0] * len(orig_vals), orig_vals, color=TEXT_SECONDARY, s=22, zorder=3, label="Description only")
        ax.scatter([1] * len(ext_vals), ext_vals, color=color, s=22, zorder=3, label="Description + CVSS")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Description\nonly", "Description\n+ CVSS"])
        ax.set_title(arm.capitalize(), fontsize=10, color=TEXT_PRIMARY)
        ax.set_ylim(0.5, 5.5)
        style_axes(ax)
        ax.xaxis.grid(False)
    axes[0].set_ylabel("Faithfulness score (1-5)")
    fig.suptitle("Faithfulness reference sensitivity: description-only vs. description+CVSS (paired, n=24)", fontsize=11, color=TEXT_PRIMARY)
    fig.tight_layout()
    return save_figure(fig, "llm_judge_faithfulness_original_vs_ext_bullet")


def append_methodology_log(rubric_hash, n_calls_made, n_calls_skipped, n_failed, run_timestamp):
    entry = []
    entry.append("")
    entry.append("")
    entry.append(f"## Stage 6f -- Faithfulness Sensitivity Check: Description-Only vs. Description+CVSS Reference ({date.today().isoformat()})")
    entry.append("")
    entry.append("**Script:** `src/llm_judge_faithfulness_ext.py`")
    entry.append(
        f"**Outputs:** `{RAW_EXT_PATH}`, `{PER_TEXT_EXT_PATH}`, `{COMPARISON_MD_PATH}`, figures in `{FIGURES_DIR}/`"
    )
    entry.append("")
    entry.append(
        "Stage 6e's faithfulness dimension scored each summary against the target CVE's bare "
        "`description` field only. That reference excludes the CVSS sub-fields (attack vector, "
        "attack complexity, privileges required, user interaction, CIA impact, CVSS score/"
        "severity) even though `generate_summaries.py`'s `build_target_cve_block()` supplies "
        "those fields to the generator directly, as structured data alongside the description, "
        "and both prompt templates instruct the model to use them. Inspecting Stage 6e's raw "
        "justifications (see METHODOLOGY_LOG.md's Stage 6e manual note) confirmed that most "
        "'unsupported claim' flags on the persona/baseline arms were the judge correctly "
        "following its rubric while marking real, sourced CVSS-derived restatements as "
        "unsupported, simply because they were not literally present in the bare description "
        "string being used as the reference."
    )
    entry.append("")
    entry.append(
        "This stage re-scores faithfulness only (comprehension is not reference-based and is "
        "unaffected) using an EXPANDED reference: the description plus the CVSS sub-fields "
        "listed above, i.e. the same fields the generator was actually given. Two categories are "
        "deliberately still excluded from the expanded reference:"
    )
    entry.append("")
    entry.append(
        "- **KEV listed / EPSS score.** External enrichment this project's own pipeline joined "
        "on from CISA and FIRST, not something NVD itself publishes on the record, and both "
        "prompt templates explicitly forbid the model from describing or interpreting them in "
        "the summary text. Including them in the faithfulness reference would blur 'faithful to "
        "NVD' with 'faithful to this project's own enrichment', a different claim."
    )
    entry.append(
        "- **Neighbour CVEs.** The Stage 6e brief was explicit that a claim supported only by a "
        "neighbouring CVE must not be credited as faithful. Still excluded here for the same "
        "reason."
    )
    entry.append("")
    entry.append(
        "The CVSS sub-fields, by contrast, are native NVD record data: they come from the same "
        "`cvssMetricV31` block on the same NVD record as the description, just a different field "
        "on it. Including them tests a stricter, more meaningful hallucination question (did the "
        "summary invent or misstate anything beyond the full structured NVD record it was given) "
        "rather than Stage 6e's narrower question (does the summary hold up against just the "
        "free-text description paragraph a reader would see)."
    )
    entry.append("")
    entry.append(
        "Both results are kept and reported side by side, not merged or overwritten. Stage 6e's "
        "original scores remain valid evidence for its own, narrower question and are reused "
        f"directly from `{ORIGINAL_PER_TEXT_PATH}` rather than re-queried. This stage made "
        f"{3 * len(ARMS) * 24} new judge calls (faithfulness only, expanded reference): "
        f"{n_calls_made} made this run, {n_calls_skipped} already present (resumed), {n_failed} "
        "failed after retries."
    )
    entry.append("")
    entry.append("### Reference field composition")
    entry.append("")
    entry.append(
        "Extended reference = `description` + `\"Attack vector: ... | Attack complexity: ... | "
        "Privileges required: ... | User interaction: ...\"` + `\"Confidentiality impact: ... | "
        "Integrity impact: ... | Availability impact: ...\"` + `\"CVSS score: ... (severity)\"`, "
        "all pulled directly from `data/eval_sample.jsonl` fields, in the same field set and "
        "order `build_target_cve_block()` uses for generation (minus KEV, EPSS, references, and "
        "neighbours)."
    )
    entry.append("")
    entry.append("### Reuse of rubric, mapping, and blinding design")
    entry.append("")
    entry.append(
        f"Same faithfulness rubric text and hash as Stage 6e (`{rubric_hash}`, "
        f"`v2_bullet/rubric/rubric_faithfulness.txt`) -- only the reference content changes, not "
        f"the judge's instructions. Same A/B mapping loaded from Stage 6e's "
        f"`{MAPPING_PATH}` (not regenerated), so the same CVEs are anonymised the same way "
        "across both faithfulness runs and can be directly paired for comparison. Same blinding "
        "design: the judge is never told which arm a text belongs to. Model, temperature, and "
        f"pass count unchanged ({MODEL}, temperature {TEMPERATURE}, {N_PASSES} passes)."
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

    if not Path(MAPPING_PATH).exists():
        raise SystemExit(f"STOP: {MAPPING_PATH} not found. Run src/llm_judge.py (Stage 6e) first.")
    with open(MAPPING_PATH) as f:
        mapping = json.load(f)

    print(f"Loading eval sample from {EVAL_SAMPLE_PATH}...")
    eval_records = load_eval_sample(EVAL_SAMPLE_PATH)
    print(f"Loaded {len(eval_records)} eval CVE records.")

    print(f"Loading summaries from {SUMMARIES_PATH}...")
    summaries = load_summaries(SUMMARIES_PATH)
    cve_ids = sorted(summaries.keys())
    if set(cve_ids) != set(mapping.keys()):
        raise SystemExit("STOP: CVE set in summaries does not match Stage 6e's mapping file.")
    print(f"Loaded summaries for {len(cve_ids)} CVEs.")

    print("Loading and hashing faithfulness rubric...")
    rubric_text, rubric_hash = load_rubric(RUBRIC_PATH)

    JUDGE_DIR.mkdir(parents=True, exist_ok=True)

    texts_by_arm = {}
    references_by_cve = {}
    for cve_id in cve_ids:
        texts_by_arm[(cve_id, "persona")] = extract_summary_text(summaries[cve_id]["persona"])
        texts_by_arm[(cve_id, "baseline")] = extract_summary_text(summaries[cve_id]["baseline"])
        texts_by_arm[(cve_id, "nvd")] = eval_records[cve_id]["description"]
        references_by_cve[cve_id] = build_extended_reference(eval_records[cve_id])

    existing = load_json_list(RAW_EXT_PATH)
    completed = {(r["cve_id"], r["label"], r["pass"]) for r in existing}
    print(f"Found {len(existing)} existing extended-faithfulness record(s) in {RAW_EXT_PATH}.")

    rng = random.Random(RANDOM_SEED)
    units = []
    for cve_id in cve_ids:
        for arm in ARMS:
            label = label_for_arm(mapping, cve_id, arm)
            for pass_n in range(1, N_PASSES + 1):
                units.append((cve_id, arm, label, pass_n))
    rng.shuffle(units)

    client = OpenAI(api_key=api_key)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    made = 0
    skipped = 0
    failed = []

    for cve_id, arm, label, pass_n in units:
        key = (cve_id, label, pass_n)
        if key in completed:
            skipped += 1
            continue

        text = texts_by_arm[(cve_id, arm)]
        reference = references_by_cve[cve_id]
        prompt = rubric_text.replace("{text}", text).replace("{reference}", reference)

        print(f"Scoring {cve_id} [{arm}/{label}] faithfulness (extended ref) pass {pass_n}...")
        try:
            model_used, score, justification = call_judge(client, prompt)
        except Exception as e:
            print(f"  FAILED after retries: {e}")
            failed.append(f"{cve_id}:{label}:{pass_n}")
            continue

        record = {
            "cve_id": cve_id,
            "label": label,
            "dimension": "faithfulness_ext",
            "pass": pass_n,
            "score": score,
            "justification": justification,
            "model": model_used,
            "temperature": TEMPERATURE,
            "rubric_hash": rubric_hash,
            "reference_variant": "description_plus_cvss",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        existing.append(record)
        write_json_atomic(existing, RAW_EXT_PATH)
        completed.add(key)
        made += 1

    print()
    print(f"Done scoring. Made: {made}, skipped (resumed): {skipped}, failed: {len(failed)}")
    if failed:
        print(f"  Failed keys: {failed}")
        raise SystemExit(f"STOP: {len(failed)} judge call(s) failed after retries; re-run to resume.")

    # --- De-anonymise and aggregate (extended) ---
    print("Aggregating extended-reference scores (de-anonymising via mapping)...")
    per_text = {}
    for r in existing:
        arm = arm_for_label(mapping, r["cve_id"], r["label"])
        per_text.setdefault((r["cve_id"], arm), []).append(r["score"])

    per_text_rows = []
    for (cve_id, arm), scores in sorted(per_text.items()):
        arr = np.asarray(scores, dtype=float)
        per_text_rows.append(
            {
                "cve_id": cve_id,
                "arm": arm,
                "n_passes": len(arr),
                "mean_score": float(np.mean(arr)),
                "sd_score": float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan"),
                "scores": scores,
            }
        )
    ext_df = pd.DataFrame(per_text_rows)
    ext_df.to_csv(PER_TEXT_EXT_PATH, index=False)
    print(f"Wrote {PER_TEXT_EXT_PATH} ({len(ext_df)} rows).")

    # --- Load Stage 6e original faithfulness scores for comparison ---
    orig_df = pd.read_csv(ORIGINAL_PER_TEXT_PATH)
    orig_df = orig_df[orig_df["dimension"] == "faithfulness"]

    extended_by_arm = {}
    original_by_arm = {}
    for arm in ARMS:
        ext_sub = ext_df[ext_df["arm"] == arm].set_index("cve_id").sort_index()
        orig_sub = orig_df[orig_df["arm"] == arm].set_index("cve_id").sort_index()
        assert list(ext_sub.index) == list(orig_sub.index) == cve_ids, f"cve_id mismatch for arm {arm}"
        extended_by_arm[arm] = ext_sub["mean_score"].tolist()
        original_by_arm[arm] = orig_sub["mean_score"].tolist()

    extended_by_arm_cve = {arm: dict(zip(cve_ids, extended_by_arm[arm])) for arm in ARMS}
    original_by_arm_cve = {arm: dict(zip(cve_ids, original_by_arm[arm])) for arm in ARMS}

    desc_rows = []
    for arm in ARMS:
        desc_rows.append(descriptive_row(original_by_arm[arm], f"{arm} -- faithfulness (description only)"))
        desc_rows.append(descriptive_row(extended_by_arm[arm], f"{arm} -- faithfulness (description + CVSS)"))

    comparisons = []
    for arm in ARMS:
        comparisons.append(
            paired_summary(extended_by_arm[arm], original_by_arm[arm], f"{arm} extended", f"{arm} original")
        )

    # --- Markdown report ---
    def build_descriptive_table_md(rows):
        header = "| Arm / reference | N | Mean | Median | SD | Min | Max |\n|---|---|---|---|---|---|---|\n"
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
    md.append("# Faithfulness Sensitivity Check: Description-Only vs. Description+CVSS Reference\n\n")
    md.append(
        "This file reports evidence, not a verdict. Descriptive statistics and paired Cohen's d "
        "effect sizes only, exploratory and small-N (n=24 eval CVEs). Judge model "
        f"`{MODEL}`, temperature {TEMPERATURE}, {N_PASSES} passes per text. Extended-reference "
        f"scores are new (this run); description-only scores are Stage 6e's original results, "
        f"reused unchanged from `{ORIGINAL_PER_TEXT_PATH}`. See METHODOLOGY_LOG.md \"Stage 6f\" "
        "for the full rationale on which fields were added to the reference and why KEV/EPSS "
        "were deliberately excluded.\n\n"
    )
    md.append("## Descriptive statistics\n\n")
    md.append(build_descriptive_table_md(desc_rows))
    md.append("\n")
    md.append("## Paired comparison: extended reference vs. original (description-only) reference\n\n")
    md.append("Matched by CVE, n=24 pairs, per arm. A positive mean diff means the extended reference scored higher.\n\n")
    md.append(build_paired_table_md(comparisons))
    md.append("\n")
    md.append("## Figures\n\n")
    md.append(f"See `{FIGURES_DIR}/` for PNG (300 dpi) and SVG versions.\n\n")
    md.append("- `llm_judge_faithfulness_ext_bullet` -- faithfulness scores under the extended reference, by text\n")
    md.append("- `llm_judge_faithfulness_original_vs_ext_bullet` -- per-CVE paired change, description-only to description+CVSS reference, persona and baseline\n")

    COMPARISON_MD_PATH.write_text("".join(md))
    print(f"Wrote {COMPARISON_MD_PATH}.")

    # --- Figures ---
    print("Generating figures...")
    fig_extended_scores({arm: extended_by_arm[arm] for arm in ARMS})
    fig_original_vs_extended(original_by_arm_cve, extended_by_arm_cve)

    # --- Methodology log ---
    if made > 0:
        append_methodology_log(rubric_hash, made, skipped, len(failed), run_timestamp)
        print(f"Appended 'Stage 6f' section to {METHODOLOGY_LOG_PATH}.")
    else:
        print(f"No new judge calls this run; not re-appending to {METHODOLOGY_LOG_PATH}.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
