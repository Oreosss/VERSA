"""LLM-as-judge heuristic evaluation of the dashboard UI (Objective 3 gap).

Scores the live dashboard's usability against Nielsen's 10 usability
heuristics using an OpenAI model as an independent judge, given screenshots
captured by `src/capture_dashboard_screenshots.py`.

This closes an evaluation gap, not a design gap: the dissertation's
Objective 3 ("surface these summaries through an interactive dashboard")
and Table 2.1 (which claims a "visual triage dashboard" -- filtering,
overview, summary-vs-raw -- as the tool's differentiator against every
comparator) were, until this script, backed by zero evidence. Every
existing evaluation method (automated text metrics, `src/llm_judge.py`, the
human comprehension study) scores the generated *summary text*, never the
dashboard the summaries are surfaced through.

v2 note (2026-08-13): this is the re-run after three usability fixes
(tooltips on the technical-details headers and "More filters" labels; a
"Clear all filters" button on the zero-result state). v1's results are
archived under `v2_bullet/judge/v1/` and `v2_bullet/screenshots_v1/`; see
`src/compare_usability_judge_runs.py` for the paired comparison. The six
PRIMARY_SCREENSHOTS are unchanged from v1 (same states, same captions,
same context-image composition) for a clean paired diff. Two of the three
fixes are CSS `:hover`-only tooltips, invisible to any static screenshot
that doesn't explicitly trigger the hover, so two SUPPLEMENTARY_SCREENSHOTS
were added specifically to make them observable. They are scored (with the
six primary screenshots as their context) but reported separately, not
merged into the six-screenshot aggregate/figure, since v1 has no
counterpart to diff them against.

Design, mirroring `src/llm_judge.py`'s established conventions:

- Judge: OpenAI (`gpt-4.1-2025-04-14`), a different provider from the
  Anthropic generator, for the same self-evaluation-bias reason.
- Multi-pass: each screenshot is scored 3 times at temperature 0 to
  evidence stability, same as the text judge.
- No blinding: unlike the text judge (which compares 3 arms and must not
  let the model infer which is which), there is only one dashboard design
  being inspected here. This is a single-system heuristic evaluation, in
  the tradition of Nielsen's inspection method, not a comparison.
- Holistic-but-anchored scoring: each call scores one PRIMARY screenshot
  against all 10 heuristics at once (not 10 separate calls), but is also
  shown other screenshots as CONTEXT, since heuristics like "consistency
  and standards" cannot be judged validly from a single isolated frame.
  See `v2_bullet/rubric/rubric_usability.txt`.

Resumable: a (screenshot, pass) tuple already present in
`llm_judge_usability_raw.json` is skipped, not re-scored.
"""

import base64
import json
import os
import random
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
plt.rcParams["font.serif"] = [
    "Times New Roman",
    "Times",
    "CMU Serif",
    "DejaVu Serif",
]
plt.rcParams["axes.unicode_minus"] = False

SCREENSHOTS_DIR = Path("v2_bullet/screenshots")
RUBRIC_PATH = Path("v2_bullet/rubric/rubric_usability.txt")
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"

JUDGE_DIR = Path("v2_bullet/judge")
RAW_PATH = JUDGE_DIR / "llm_judge_usability_raw.json"
PER_SCREENSHOT_PATH = JUDGE_DIR / "llm_judge_usability_per_screenshot.csv"
AGGREGATE_JSON_PATH = JUDGE_DIR / "llm_judge_usability_aggregate.json"
COMPARISON_MD_PATH = JUDGE_DIR / "LLM_JUDGE_USABILITY_COMPARISON.md"
SUPPLEMENTARY_PER_SCREENSHOT_PATH = JUDGE_DIR / "llm_judge_usability_supplementary_per_screenshot.csv"
FIGURES_DIR = Path("v2_bullet/figures")

MODEL = "gpt-4.1-2025-04-14"
TEMPERATURE = 0
N_PASSES = 3
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
RANDOM_SEED = 42  # consistent with the project's random.Random(42) convention

HEURISTIC_KEYS = (
    "visibility_of_system_status",
    "match_real_world",
    "user_control_freedom",
    "consistency_standards",
    "error_prevention",
    "recognition_not_recall",
    "flexibility_efficiency",
    "aesthetic_minimalist",
    "error_recovery",
    "help_documentation",
)

HEURISTIC_LABEL = {
    "visibility_of_system_status": "Visibility of system status",
    "match_real_world": "Match between system and the real world",
    "user_control_freedom": "User control and freedom",
    "consistency_standards": "Consistency and standards",
    "error_prevention": "Error prevention",
    "recognition_not_recall": "Recognition rather than recall",
    "flexibility_efficiency": "Flexibility and efficiency of use",
    "aesthetic_minimalist": "Aesthetic and minimalist design",
    "error_recovery": "Help users recognize, diagnose, and recover from errors",
    "help_documentation": "Help and documentation",
}

# (screenshot id, filename, caption). Order matches the states produced by
# src/capture_dashboard_screenshots.py. Unchanged from v1 -- do not edit
# without also invalidating the v1 comparison.
PRIMARY_SCREENSHOTS = [
    (
        "1_initial_load",
        "1_initial_load.png",
        "Default list view on first load, no filters applied: severity "
        "distribution chart, stat header, and the vulnerability list sorted "
        "newest-first.",
    ),
    (
        "2_filtered_search",
        "2_filtered_search.png",
        "List view after applying Severity=High and 'Only show CISA "
        "KEV-listed', with the 'More filters' panel expanded showing the "
        "additional filter controls (privileges, user interaction, OS, "
        "vendor, attack complexity, CVSS impact fields, published-within).",
    ),
    (
        "3_explain_summary",
        "3_explain_summary.png",
        "Detail view for a CVE after clicking 'Explain', showing the "
        "generated three-part plain-language summary (What is vulnerable / "
        "How it can be exploited / What action to take) and the Similar "
        "Vulnerabilities panel.",
    ),
    (
        "4_raw_nvd_toggle",
        "4_raw_nvd_toggle.png",
        "Same detail view with the 'Show original NVD description' "
        "disclosure toggle expanded, revealing the raw NVD text beneath "
        "the generated summary. This is a sequential disclosure toggle, "
        "not a side-by-side comparison view.",
    ),
    (
        "5_all_expanded",
        "5_all_expanded.png",
        "Same detail view with every disclosure section open at once: raw "
        "NVD description, CWE details, technical details table, and "
        "references.",
    ),
    (
        "6_empty_state",
        "6_empty_state.png",
        "List view filtered to Severity=Low and 'Only show CISA "
        "KEV-listed' with an empty search box -- a filter combination "
        "with zero matches, showing the 'No CVEs match the current "
        "filters' empty state. v2: now also shows a 'Clear all filters' "
        "button, added after v1.",
    ),
]

# v2 only: hover states making the two CSS :hover-only tooltip fixes
# observable to a static screenshot. Scored with PRIMARY_SCREENSHOTS as
# context, but reported separately -- v1 has no counterpart for these.
SUPPLEMENTARY_SCREENSHOTS = [
    (
        "7_tooltip_tech_details",
        "7_tooltip_tech_details.png",
        "Same detail view as the other states, technical details expanded, "
        "mouse hovered over the 'Confidentiality impact' column header, "
        "showing a new tooltip explaining what the field means.",
    ),
    (
        "8_tooltip_filter_label",
        "8_tooltip_filter_label.png",
        "List view, 'More filters' panel open, mouse hovered over the "
        "'Privileges' label, showing a new tooltip explaining what the "
        "filter does.",
    ),
]

ALL_SCREENSHOTS = PRIMARY_SCREENSHOTS + SUPPLEMENTARY_SCREENSHOTS

COLOR_BAR = "#2f9e8f"
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"


def load_rubric(path):
    text = path.read_text()
    if "{primary_caption}" not in text:
        raise SystemExit(f"STOP: {path} is missing the {{primary_caption}} placeholder.")
    import hashlib

    rubric_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    return text, rubric_hash


def image_data_uri(path):
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


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


def build_messages(rubric_text, screenshot_id, screenshot_uris):
    primary_id, _, primary_caption = next(s for s in ALL_SCREENSHOTS if s[0] == screenshot_id)
    prompt_text = rubric_text.replace("{primary_caption}", primary_caption)

    is_primary = screenshot_id in {sid for sid, _, _ in PRIMARY_SCREENSHOTS}
    # Primary screens use only the other primary screens as context (byte-
    # identical to v1's context composition, for a clean paired diff).
    # Supplementary (v2-only) screens use all six primary screens as
    # context, since they have none of their own to draw on.
    context_pool = PRIMARY_SCREENSHOTS

    content = [{"type": "text", "text": prompt_text}]
    content.append({"type": "text", "text": "PRIMARY SCREEN (score this one):"})
    content.append({"type": "image_url", "image_url": {"url": screenshot_uris[primary_id], "detail": "high"}})
    for sid, _, caption in context_pool:
        if sid == primary_id:
            continue
        content.append({"type": "text", "text": f"CONTEXT SCREEN -- {caption}"})
        content.append({"type": "image_url", "image_url": {"url": screenshot_uris[sid], "detail": "high"}})
    return [{"role": "user", "content": content}]


def call_judge(client, messages):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                response_format={"type": "json_object"},
                messages=messages,
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            result = {}
            for key in HEURISTIC_KEYS:
                entry = parsed[key]
                score = entry["score"]
                justification = entry["justification"]
                if not isinstance(score, int) or not (1 <= score <= 5):
                    raise ValueError(f"{key}: score out of range or non-integer: {score!r}")
                if not isinstance(justification, str) or not justification.strip():
                    raise ValueError(f"{key}: justification missing or empty")
                result[key] = {"score": score, "justification": justification}
            return response.model, result
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


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
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


def fig_usability_scores(heuristic_means, heuristic_sds):
    order = sorted(HEURISTIC_KEYS, key=lambda k: heuristic_means[k])
    labels = [HEURISTIC_LABEL[k] for k in order]
    means = [heuristic_means[k] for k in order]
    sds = [heuristic_sds[k] for k in order]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    y = np.arange(len(order))
    bars = ax.barh(y, means, xerr=sds, capsize=3, color=COLOR_BAR, alpha=0.8,
                    edgecolor=COLOR_BAR, height=0.6, zorder=3)
    for bar, mean in zip(bars, means):
        ax.text(mean + 0.12, bar.get_y() + bar.get_height() / 2, f"{mean:.2f}",
                 va="center", fontsize=9, color=TEXT_PRIMARY)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT_PRIMARY)
    ax.set_xlim(1.0, 5.6)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel(f"Judge score (1-5, mean across {len(PRIMARY_SCREENSHOTS)} screenshots x {N_PASSES} passes)")
    ax.set_title("Dashboard usability: LLM-as-judge scores by Nielsen heuristic",
                  fontsize=10, color=TEXT_PRIMARY)
    style_axes(ax)
    fig.tight_layout()
    return save_figure(fig, "llm_judge_usability_bullet")


def append_methodology_log(rubric_text, rubric_hash, n_made, n_skipped, n_failed, run_timestamp):
    entry = []
    entry.append("")
    entry.append("")
    entry.append(f"## Dashboard Usability -- LLM-as-Judge Evaluation ({date.today().isoformat()})")
    entry.append("")
    entry.append("**Script:** `src/capture_dashboard_screenshots.py`, `src/llm_judge_usability.py`")
    entry.append(
        f"**Outputs:** `{RAW_PATH}`, `{PER_SCREENSHOT_PATH}`, `{AGGREGATE_JSON_PATH}`, "
        f"`{COMPARISON_MD_PATH}`, figures in `{FIGURES_DIR}/`"
    )
    entry.append("")
    entry.append(
        "Scores the live dashboard's usability, not the generated summary text -- every other "
        "evaluation method in this project (automated text metrics, Stage 6e LLM-as-judge, the "
        "human comprehension study) scores the summary text, never the dashboard it is surfaced "
        "through. This addresses Objective 3 (\"surface these summaries through an interactive "
        "dashboard\") and the Table 2.1 differentiation claim (\"visual triage dashboard\"), "
        "neither of which had any supporting evaluation before this stage."
    )
    entry.append("")
    entry.append(
        f"{len(PRIMARY_SCREENSHOTS)} representative dashboard states were captured with Playwright "
        f"({SCREENSHOTS_DIR}/) and each scored against all 10 of Nielsen's usability heuristics in a "
        f"single call per pass, 3 passes per screenshot at temperature {TEMPERATURE}, using an "
        f"OpenAI model as judge, plus {len(SUPPLEMENTARY_SCREENSHOTS)} v2-only supplementary states "
        "(hover-triggered tooltips, invisible to a static screenshot otherwise -- see the v2 note "
        f"above) scored the same way but reported separately "
        f"({len(ALL_SCREENSHOTS) * N_PASSES} judge calls in the full design; {n_made} made this run, "
        f"{n_skipped} already present (resumed), {n_failed} failed after retries)."
    )
    entry.append("")
    entry.append("### Judge model and independence rationale")
    entry.append("")
    entry.append(
        f"**Judge model:** `{MODEL}`, temperature {TEMPERATURE}, the same model and convention used "
        "for the text judge (Stage 6e), for the same reason: a different provider (OpenAI) from the "
        "Anthropic generator, so no model ever evaluates output associated with its own family."
    )
    entry.append("")
    entry.append("### Why heuristic evaluation, and why this is single-system, not blinded")
    entry.append("")
    entry.append(
        "Heuristic evaluation (Nielsen, 1994) is inspector-based, not user-based: an evaluator walks "
        "the interface and checks it against a fixed heuristic set, which is what this project's own "
        "informal \"Nielsen-style walkthrough\" (STATUS.md) already did once, ad hoc and undocumented. "
        "This script formalises and repeats that same walkthrough with multiple independent passes. "
        "Unlike the text judge (Stage 6e), which scores 3 arms and must be blinded to which is which, "
        "there is only one dashboard design here -- this is a single-system inspection, not a "
        "comparison, so no blinding scheme applies."
    )
    entry.append("")
    entry.append("### Holistic-but-anchored scoring")
    entry.append("")
    entry.append(
        "Each call scores one PRIMARY screenshot against all 10 heuristics at once, rather than 10 "
        "separate calls, since a human evaluator would naturally notice several heuristic violations "
        "on the same screen at once. The other 5 screenshots are supplied as CONTEXT images in every "
        "call (not scored themselves), since heuristics such as consistency and standards cannot be "
        "judged validly from a single isolated frame."
    )
    entry.append("")
    entry.append("### Rubric (verbatim, locked and hashed)")
    entry.append("")
    entry.append(f"- Rubric hash: `{rubric_hash}` (`{RUBRIC_PATH}`)")
    entry.append("")
    entry.append("```")
    entry.append(rubric_text.strip())
    entry.append("```")
    entry.append("")
    entry.append("### Limitations")
    entry.append("")
    entry.append(
        "- *Not a substitute for real users.* However many independent passes, a single LLM judge is "
        "not the same as multiple independent human evaluators -- Nielsen's original method assumes "
        "evaluator diversity catches a broader set of distinct problems than repeated passes of the "
        "same evaluator can. No live-dashboard user study has been run (the human comprehension study, "
        "Stage 8, used static Qualtrics stimuli, never the dashboard itself); this method is a proxy, "
        "not a replacement, for that gap."
    )
    entry.append(
        "- *Screenshot-bound.* The judge sees static images of 6 states, not a live interactive "
        "session, so heuristics concerned with real-time responsiveness or multi-step interaction "
        "sequences beyond what a screenshot can show are judged only as far as the captured states "
        "allow."
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

    missing = [f for _, f, _ in ALL_SCREENSHOTS if not (SCREENSHOTS_DIR / f).exists()]
    if missing:
        raise SystemExit(
            f"STOP: missing screenshot(s) {missing} in {SCREENSHOTS_DIR}/. "
            "Run src/capture_dashboard_screenshots.py first."
        )

    print("Loading and hashing rubric...")
    rubric_text, rubric_hash = load_rubric(RUBRIC_PATH)

    print("Encoding screenshots...")
    screenshot_uris = {sid: image_data_uri(SCREENSHOTS_DIR / fname) for sid, fname, _ in ALL_SCREENSHOTS}

    JUDGE_DIR.mkdir(parents=True, exist_ok=True)

    existing = load_json_list(RAW_PATH)
    completed = {(r["screenshot_id"], r["pass"]) for r in existing}
    print(f"Found {len(existing)} existing judge record(s) in {RAW_PATH}.")

    units = [(sid, pass_n) for sid, _, _ in ALL_SCREENSHOTS for pass_n in range(1, N_PASSES + 1)]
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(units)

    client = OpenAI(api_key=api_key)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    made = 0
    skipped = 0
    failed = []

    for screenshot_id, pass_n in units:
        key = (screenshot_id, pass_n)
        if key in completed:
            skipped += 1
            continue

        print(f"Scoring {screenshot_id} pass {pass_n}...")
        messages = build_messages(rubric_text, screenshot_id, screenshot_uris)
        try:
            model_used, heuristics = call_judge(client, messages)
        except Exception as e:
            print(f"  FAILED after retries: {e}")
            failed.append(f"{screenshot_id}:{pass_n}")
            continue

        record = {
            "screenshot_id": screenshot_id,
            "pass": pass_n,
            "heuristics": heuristics,
            "model": model_used,
            "temperature": TEMPERATURE,
            "rubric_hash": rubric_hash,
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

    # --- Aggregate ---
    # Primary and supplementary are aggregated separately: PER_SCREENSHOT_PATH
    # and AGGREGATE_JSON_PATH cover only PRIMARY_SCREENSHOTS, so their schema
    # and content are directly diffable against the v1 archive
    # (v2_bullet/judge/v1/) by src/compare_usability_judge_runs.py.
    # Supplementary (v2-only) scores go to their own file.
    print("Aggregating scores...")

    def screenshot_rows(screenshot_list):
        rows = []
        for screenshot_id, _, _ in screenshot_list:
            passes = [r for r in existing if r["screenshot_id"] == screenshot_id]
            for key in HEURISTIC_KEYS:
                scores = [p["heuristics"][key]["score"] for p in passes]
                arr = np.asarray(scores, dtype=float)
                rows.append(
                    {
                        "screenshot_id": screenshot_id,
                        "heuristic": key,
                        "n_passes": len(arr),
                        "mean_score": float(np.mean(arr)),
                        "sd_score": float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan"),
                        "scores": scores,
                    }
                )
        return pd.DataFrame(rows)

    per_screenshot_df = screenshot_rows(PRIMARY_SCREENSHOTS)
    per_screenshot_df.to_csv(PER_SCREENSHOT_PATH, index=False)
    print(f"Wrote {PER_SCREENSHOT_PATH} ({len(per_screenshot_df)} rows).")

    supplementary_df = screenshot_rows(SUPPLEMENTARY_SCREENSHOTS)
    supplementary_df.to_csv(SUPPLEMENTARY_PER_SCREENSHOT_PATH, index=False)
    print(f"Wrote {SUPPLEMENTARY_PER_SCREENSHOT_PATH} ({len(supplementary_df)} rows).")

    heuristic_means = {}
    heuristic_sds = {}
    for key in HEURISTIC_KEYS:
        sub = per_screenshot_df[per_screenshot_df["heuristic"] == key]
        heuristic_means[key] = float(sub["mean_score"].mean())
        heuristic_sds[key] = float(sub["mean_score"].std(ddof=1))

    aggregate = {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "n_passes": N_PASSES,
        "n_screenshots": len(PRIMARY_SCREENSHOTS),
        "rubric_hash": rubric_hash,
        "heuristic_means": heuristic_means,
        "heuristic_sds": heuristic_sds,
    }
    write_json_atomic(aggregate, AGGREGATE_JSON_PATH)
    print(f"Wrote {AGGREGATE_JSON_PATH}.")

    # --- Markdown report ---
    def fmt(x, nd=2):
        return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"

    md = []
    md.append("# LLM-as-Judge Comparison: Dashboard Usability (Nielsen's heuristics)\n\n")
    md.append(
        "This file reports evidence, not a verdict. Descriptive statistics only, single-system "
        f"heuristic evaluation. Judge model `{MODEL}`, temperature {TEMPERATURE}, {N_PASSES} passes "
        f"per screenshot, {len(PRIMARY_SCREENSHOTS)} primary screenshots + {len(SUPPLEMENTARY_SCREENSHOTS)} "
        "v2-only supplementary screenshots. See METHODOLOGY_LOG.md \"Dashboard Usability -- LLM-as-"
        "Judge Evaluation\" for the rubric verbatim and limitations. For the v1-vs-v2 paired "
        "comparison, see `LLM_JUDGE_USABILITY_V1_VS_V2.md` "
        "(`src/compare_usability_judge_runs.py`).\n\n"
    )
    md.append(f"## Mean score by heuristic (1-5), across all {len(PRIMARY_SCREENSHOTS)} primary screenshots\n\n")
    md.append("| Heuristic | Mean | SD (across screenshots) |\n|---|---|---|\n")
    for key in sorted(HEURISTIC_KEYS, key=lambda k: heuristic_means[k]):
        md.append(f"| {HEURISTIC_LABEL[key]} | {fmt(heuristic_means[key])} | {fmt(heuristic_sds[key])} |\n")
    md.append("\n## Per-screenshot detail (primary)\n\n")
    md.append("| Screenshot | Heuristic | Mean | SD (across 3 passes) |\n|---|---|---|---|\n")
    for _, row in per_screenshot_df.sort_values(["screenshot_id", "heuristic"]).iterrows():
        md.append(
            f"| {row['screenshot_id']} | {HEURISTIC_LABEL[row['heuristic']]} | "
            f"{fmt(row['mean_score'])} | {fmt(row['sd_score'])} |\n"
        )
    md.append(
        "\n## Supplementary (v2 only): hover-state evidence for the tooltip fixes\n\n"
        "Not part of the primary aggregate above -- v1 has no counterpart to diff these against, "
        "since the tooltips they show didn't exist in v1. Included here so the tooltip fixes are "
        "measured somewhere, given the primary screenshots can't show a `:hover` state at all.\n\n"
    )
    md.append("| Screenshot | Heuristic | Mean | SD (across 3 passes) |\n|---|---|---|---|\n")
    for _, row in supplementary_df.sort_values(["screenshot_id", "heuristic"]).iterrows():
        md.append(
            f"| {row['screenshot_id']} | {HEURISTIC_LABEL[row['heuristic']]} | "
            f"{fmt(row['mean_score'])} | {fmt(row['sd_score'])} |\n"
        )
    md.append("\n## Figures\n\n")
    md.append(f"See `{FIGURES_DIR}/` for PNG (300 dpi) and SVG versions.\n\n")
    md.append("- `llm_judge_usability_bullet` -- mean score per heuristic, primary screenshots\n")

    COMPARISON_MD_PATH.write_text("".join(md))
    print(f"Wrote {COMPARISON_MD_PATH}.")

    # --- Figure ---
    print("Generating figure...")
    figures_written = fig_usability_scores(heuristic_means, heuristic_sds)
    for p in figures_written:
        print(f"  {p}")

    # --- Methodology log ---
    if made > 0:
        append_methodology_log(rubric_text, rubric_hash, made, skipped, len(failed), run_timestamp)
        print(f"Appended 'Dashboard Usability' section to {METHODOLOGY_LOG_PATH}.")
    else:
        print(f"No new judge calls this run; not re-appending to {METHODOLOGY_LOG_PATH}.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
