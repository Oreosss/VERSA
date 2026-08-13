# FINDINGS_LOG.md
_Factual record for the thesis Findings and Evaluation chapter. Generated from direct inspection of `v2_bullet/metrics/`, `v2_bullet/judge/`, `v2_bullet/figures/`, `STATUS.md`, and `METHODOLOGY_LOG.md`. Last updated: 2026-08-05._
_Values below are read from the actual output files, not paraphrased from prose notes. Where a file is referenced elsewhere in the repo but does not exist in this working tree, that is stated explicitly._
_Section 3 (Human Comprehension Study) added 2026-08-10, after Stage 8 was run; the rest of this file is unchanged from 2026-08-05._

---

## 1. Automated Metrics — `v2_bullet/metrics/`

**Files:** `metrics_per_summary_bullet.csv`, `metrics_per_summary_bullet.json` (same data, higher precision), `PROMPT_COMPARISON_bullet.md`. No separate aggregate file exists — descriptive stats and effect sizes live inside `PROMPT_COMPARISON_bullet.md`.

**Design:** paired, n=24 eval CVEs, 2 prompt arms (persona, baseline), same 24 CVEs in both arms. Descriptive statistics and paired Cohen's d only — **no significance test reported** (v1 prose's Wilcoxon signed-rank test was deliberately dropped for this run; see METHODOLOGY_LOG.md Stage 6d).

### 1.1 Descriptive statistics (n=24 per arm)

| Metric | Persona mean | Persona median | Persona SD | Baseline mean | Baseline median | Baseline SD |
|---|---|---|---|---|---|---|
| ROUGE-1 (F) | 0.231 | 0.218 | 0.077 | 0.240 | 0.227 | 0.071 |
| ROUGE-2 (F) | 0.127 | 0.124 | 0.057 | 0.123 | 0.110 | 0.045 |
| ROUGE-L (F) | 0.156 | 0.152 | 0.054 | 0.163 | 0.151 | 0.050 |
| BERTScore precision | 0.819 | 0.819 | 0.017 | 0.821 | 0.824 | 0.012 |
| BERTScore recall | 0.906 | 0.903 | 0.016 | 0.906 | 0.907 | 0.015 |
| BERTScore F1 | 0.860 | 0.860 | 0.013 | 0.861 | 0.861 | 0.011 |
| Dale-Chall (summary) | 11.902 | 11.982 | 0.352 | 11.961 | 11.877 | 0.418 |
| Word count | 279.542 | 282.500 | 20.208 | 266.083 | 269.000 | 27.573 |

Dale-Chall, raw NVD description (n=24, same 24 descriptions scored against both arms): mean **13.650**, median 13.811, SD 1.688, min 10.304, max 16.469.

### 1.2 Persona vs. baseline — paired differences (n=24 pairs, matched by cve_id)

| Comparison | Mean diff | Median diff | SD diff | Cohen's d (paired) |
|---|---|---|---|---|
| ROUGE-1 (F) | −0.009 | −0.004 | 0.026 | −0.337 |
| ROUGE-2 (F) | 0.004 | −0.002 | 0.029 | 0.133 |
| ROUGE-L (F) | −0.007 | −0.002 | 0.022 | −0.324 |
| BERTScore precision | −0.003 | −0.000 | 0.013 | −0.217 |
| BERTScore recall | −0.000 | −0.000 | 0.008 | −0.037 |
| BERTScore F1 | −0.002 | −0.000 | 0.009 | −0.191 |
| Dale-Chall (summary) | −0.059 | −0.068 | 0.253 | −0.235 |
| Word count | 13.458 | 14.500 | 18.079 | 0.744 |

### 1.3 Summary vs. raw NVD — Dale-Chall paired difference (n=24 pairs per arm)

Negative = summary scored easier (lower Dale-Chall) than the raw NVD description for that CVE.

| Comparison | Mean diff | Median diff | SD diff | Cohen's d (paired) |
|---|---|---|---|---|
| Persona summary − raw NVD | −1.748 | −1.748 | 1.512 | −1.156 |
| Baseline summary − raw NVD | −1.689 | −1.684 | 1.427 | −1.183 |

### 1.4 Flesch-Kincaid: excluded from this run (confirmed, not just claimed)

Confirmed in `PROMPT_COMPARISON_bullet.md` (header note), `src/compute_metrics_bullet.py` (lines 11–12, 399–405), and METHODOLOGY_LOG.md Stage 6d. Rationale: the bullet format makes each line a short, single-clause "sentence" by construction, so FK — which is driven by sentence length and syllable count — would largely reflect the formatting choice rather than genuine readability. Dale-Chall (vocabulary-familiarity based, not sentence-length based) is the sole readability metric reported for v2.

### 1.5 Readability regression cases

CVEs where the **summary** scored a *higher* (harder) Dale-Chall than the **raw NVD description** it was generated from — computed directly from `metrics_per_summary_bullet.csv`, not narrated in the .md report:

| CVE | Arm | Summary DC | NVD DC | Diff |
|---|---|---|---|---|
| CVE-2021-42013 | baseline | 11.785 | 11.514 | +0.272 |
| CVE-2021-42013 | persona | 11.753 | 11.514 | +0.240 |
| CVE-2023-43661 | baseline | 11.575 | 11.534 | +0.041 |
| CVE-2022-3062 | baseline | 11.611 | 11.072 | +0.539 |
| CVE-2022-3062 | persona | 11.498 | 11.072 | +0.426 |
| CVE-2024-1781 | baseline | 11.798 | 10.304 | +1.494 |
| CVE-2024-1781 | persona | 12.072 | 10.304 | +1.768 |

7 of 48 rows regress. No "disagreement" flag exists in the metrics pipeline for this stage (that concept only applies to the LLM-judge multi-pass design, section 2.5 below).

### 1.6 Figures (PNG 300dpi + SVG, in `v2_bullet/figures/`)

| Basename | Shows |
|---|---|
| `dc_grouped_nvd_persona_baseline_bullet` | Dale-Chall, raw NVD vs. persona vs. baseline (grouped bar) |
| `bertscore_persona_vs_baseline_bullet` | BERTScore F1 and precision, persona vs. baseline |
| `rouge_persona_vs_baseline_bullet` | ROUGE-1/2/L, persona vs. baseline |
| `dc_paired_slope_nvd_to_summary_bullet` | Per-CVE paired Dale-Chall change, raw NVD → summary |
| `word_count_persona_vs_baseline_bullet` | Word count, persona vs. baseline |

---

## 2. LLM-as-Judge — `v2_bullet/judge/`

**Judge model:** `gpt-4.1-2025-04-14`, temperature 0, 3 passes per (CVE, arm, dimension). Deliberately a different provider (OpenAI) from the generator (Anthropic, `claude-opus-4-6`) to avoid self-evaluation bias — see METHODOLOGY_LOG.md Stage 6e.

**Files:**
- `llm_judge_raw.json` — 432 individual call records: `cve_id, label (A/B/nvd), dimension, pass, score, justification, model, temperature, rubric_hash, timestamp`
- `llm_judge_mapping.json` — per-CVE A/B → persona/baseline de-anonymisation key
- `llm_judge_per_text.csv` — 144 rows (24 CVEs × 3 arms × 2 dimensions): `cve_id, arm, dimension, n_passes, mean_score, sd_score, scores`
- `llm_judge_aggregate.json` — `model, temperature, n_passes, rubric_hashes{comprehension,faithfulness}, descriptive[], paired_comparisons[]`
- `LLM_JUDGE_COMPARISON.md` — narrative rendering of the aggregate
- Rubric hashes: comprehension `2ec3864652eb026778d13f9d2077a83f371c967a628de7bf5adb48d5c0e46bd7`, faithfulness `b06ddc055f39ad0b9508dec92bd218f1e7fbfc69922c7db4c08c0185d0422d69` (verbatim rubric text in METHODOLOGY_LOG.md Stage 6e)

### 2.1 Per-arm aggregate scores (1–5 scale, n=24)

| Arm | Comprehension mean | Comprehension SD | Faithfulness mean | Faithfulness SD |
|---|---|---|---|---|
| Persona | 5.000 | 0.000 | 3.180555555555556 | 0.48133436374961636 |
| Baseline | 5.000 | 0.000 | 3.0416666666666665 | 0.2658047665355975 |
| Raw NVD | 4.013888888888889 | 0.7516755304382212 | 5.000 | 0.000 |

### 2.2 Paired effect sizes

| Comparison | Mean diff | Cohen's d (dz) |
|---|---|---|
| Persona comprehension − NVD | 0.986111111111111 | 1.3118840126885807 |
| Baseline comprehension − NVD | 0.986111111111111 | 1.3118840126885807 |
| Persona comprehension − Baseline | 0.0 | n/a (SD=0, NaN in source JSON) |
| Persona faithfulness − NVD | −1.8194444444444444 | −3.7800011415575865 |
| Baseline faithfulness − NVD | −1.9583333333333333 | −7.3675628878200214 |
| Persona faithfulness − Baseline | 0.13888888888888892 | 0.40931747158018134 |

### 2.3 Ceiling effect — confirmed against primary data

Comprehension: persona and baseline are both a flat **5.000, SD 0.000** across all 24 CVEs — verified in both `llm_judge_aggregate.json` and every one of the 48 relevant rows of `llm_judge_per_text.csv` (all read `mean_score=5.0, sd_score=0.0`). Raw NVD averaged **4.014, SD 0.752, range 3–5**. This is a genuine ceiling effect in the data, not just an assertion in STATUS.md's notes — both sources agree.

### 2.4 Faithfulness gap — not a fabrication finding

Persona (3.18) and baseline (3.04) score well below the NVD control (5.0, by construction). METHODOLOGY_LOG.md Stage 6e's manual note (added 2026-07-28, after inspecting `justification` strings in `llm_judge_raw.json`) explains why: the faithfulness reference is the bare NVD `description` field only, which excludes CVSS sub-fields (attack vector, privileges required, user interaction, CIA impact) and KEV/EPSS. `src/generate_summaries.py`'s `build_target_cve_block()` supplies those fields to the generator directly, so both arms correctly restate real, sourced facts that are simply absent from the narrow reference text the judge scores against. **State this explicitly as a scope limitation in Findings — a faithfulness score below the NVD control does not indicate hallucination.**

### 2.5 Judge disagreement cases (sd_score > 0 across the 3 passes)

Only 7 of 144 (cve × arm × dimension) cells show any inter-pass variance:

| CVE | Arm | Dimension | Scores | Mean |
|---|---|---|---|---|
| CVE-2021-21974 | nvd | comprehension | [4, 4, 5] | 4.333 |
| CVE-2021-37976 | baseline | faithfulness | [2, 3, 3] | 2.667 |
| CVE-2021-42013 | nvd | comprehension | [5, 4, 5] | 4.667 |
| CVE-2022-3062 | baseline | faithfulness | [4, 4, 3] | 3.667 |
| CVE-2023-29119 | baseline | faithfulness | [2, 3, 3] | 2.667 |
| CVE-2024-1781 | nvd | comprehension | [3, 4, 3] | 3.333 |
| CVE-2024-3400 | persona | faithfulness | [3, 3, 4] | 3.333 |

### 2.6 Figures

`llm_judge_scores_bullet` (PNG 300dpi + SVG, in `v2_bullet/figures/`) — comprehension and faithfulness scores, raw NVD vs. persona vs. baseline.

---

## 3. Human Comprehension Study — `data/human_study/`

**Status: DONE (pilot-scale), added 2026-08-10.** Superseded the earlier state of this section, which read "not started, do not cite" — that was accurate when written (2026-08-05) but is now stale. Full results, data-quality notes, and discussion-relevant flags are in `HUMAN_STUDY_FINDINGS.md`; this section summarises the headline figures only. Method (survey design, condition-verification steps, answer-key verification) is in `METHODOLOGY_LOG.md` Stage 8, not repeated here.

**Files:** `HUMAN_STUDY_FINDINGS.md` (full report), `src/analyze_human_study.py` (regenerates everything below from the raw inputs), `data/human_study/qualtrics_export_recorded.csv` (17 responses), `qualtrics_export_inprogress.csv` (7 abandoned attempts), `survey_source.txt` (verbatim Qualtrics stimulus text — used to verify condition assignment and the answer key programmatically, not assumed), `answer_key.txt` (72 items, verified 72/72 against `survey_source.txt`), `response_summary.csv`, `comprehension_long.csv`, `likert_long.csv`.

### 3.1 Sample and an exclusion

24 raw response attempts (17 recorded + 7 abandoned/in-progress); 16 reached at least one CVE entry (15 complete blocks + 1 partial, 10/20 items). One respondent reported no technical background and was excluded from the figures below as outside the thesis's target population (`CLAUDE.md`: "technical non-security personnel"), not averaged in as noise — their raw comprehension accuracy (16.7%, 2/12) is recorded separately in `HUMAN_STUDY_FINDINGS.md` §3.1 and is not part of any number below. This leaves **n=15** technical-background respondents.

### 3.2 Comprehension accuracy (3 MC questions per CVE entry, n=15, 174 scored items)

| Condition | Accuracy | n |
|---|---|---|
| NVD (raw) | 83.9% | 87 |
| Summary (LLM) | 88.5% | 87 |

+4.6 points in favour of the LLM summary. Directionally consistent with the automated-metrics comprehension results above (Section 2: persona/baseline comprehension at a 5.0/5.0 ceiling vs. NVD's 4.01, per Section 2.1), though the two evaluations are not measuring the same thing — the human study's comprehension score is a direct measurement from real readers, the LLM-judge's is a model's estimate of what a reader would understand (Stage 6e's own stated limitation, Section 2.3 above). At n=15 this is a pilot-scale, directionally-consistent result, **not a significance-tested finding** — no test is reported, matching the descriptive-statistics-only framing already used for the automated metrics (Section 1) and LLM-judge (Section 2) stages in this file.

### 3.3 Likert ratings (5-point scale, n=15, 58 rated entries)

| Condition | Clarity mean | Confidence mean |
|---|---|---|
| NVD | 3.69 | 3.79 |
| Summary | 4.17 | 4.10 |

### 3.4 Notable patterns (full detail and caveats in `HUMAN_STUDY_FINDINGS.md`)

- **Comprehension gap concentrated in the least-CVE-familiar subgroup.** Split by self-reported CVE/CVSS familiarity (`S3`), the NVD-vs-Summary gap is +7.1pp in the least-familiar subgroup (n=7 — the subgroup closest to the thesis's target population), 0pp in the middle subgroup, and +6.7pp in the most-familiar subgroup (n=3). Suggestive, not conclusive, given the cell sizes (`HUMAN_STUDY_FINDINGS.md` §8.2).
- **One MC item tests information absent from both stimuli** (a fix-version detail, "12.24", present in neither the NVD nor the Summary text shown to participants), self-flagged unprompted by a participant. Instrument defect, not a comprehension finding for that item; recommended fix before any future run (`HUMAN_STUDY_FINDINGS.md` §4.4).
- **A rushed 117-second full-block response is the clearest remaining outlier** after the population exclusion above (41.7% accuracy, second-lowest possible reading speed for 4 full entries + 20 questions). Recommend a minimum-duration filter in any future run (`HUMAN_STUDY_FINDINGS.md` §4.3).
- **A high-scoring participant (100% comprehension accuracy) left a substantive critique of the project's core premise** in the optional free-text field — that LLM summarisation "defers responsibility" rather than fixing the underlying problem of poorly-structured CVE records. Quoted in full in `HUMAN_STUDY_FINDINGS.md` §6; flagged there as Discussion-relevant, not omitted for being inconvenient to the thesis's framing.

---

## 4. Figures Inventory (results-relevant only, excludes `figures/methodology/`)

All in `v2_bullet/figures/`, each as `.png` (300dpi) and `.svg`:

| Basename | Shows | Source stage |
|---|---|---|
| `dc_grouped_nvd_persona_baseline_bullet` | Dale-Chall, raw NVD vs. persona vs. baseline | Stage 6d (metrics) |
| `bertscore_persona_vs_baseline_bullet` | BERTScore F1 and precision, persona vs. baseline | Stage 6d |
| `rouge_persona_vs_baseline_bullet` | ROUGE-1/2/L, persona vs. baseline | Stage 6d |
| `dc_paired_slope_nvd_to_summary_bullet` | Per-CVE paired Dale-Chall change, raw NVD → summary | Stage 6d |
| `word_count_persona_vs_baseline_bullet` | Word count, persona vs. baseline | Stage 6d |
| `llm_judge_scores_bullet` | Comprehension and faithfulness, raw NVD vs. persona vs. baseline | Stage 6e (judge) |

6 distinct figures already exist. No regeneration needed for Findings unless a different cut is required.

---

## 5. Repo State Cross-Check

**STATUS.md is stale by its own header** ("Generated ... 2026-07-08. Do not hand-edit"). Its "Evaluation" checklist (lines 129–135) shows automated metrics, LLM-as-judge, and the questionnaire all **unchecked**, and still lists Flesch-Kincaid as something to build. This is contradicted by the dated append-only notes further down the same file (2026-07-28 and 2026-07-28 evening entries), which correctly state metrics and judge are done and that FK was deliberately dropped.

**Rule for the Findings chapter: trust the dated notes in STATUS.md over its checklist table, and trust the output files in `v2_bullet/` over both.**

**Numbers cross-check result: no numeric conflicts found.** Every figure METHODOLOGY_LOG.md quotes verbatim (persona faithfulness 3.18, baseline 3.04, comprehension ceiling 5.0/5.0 vs. NVD 4.01/SD 0.75/range 3–5) matches `llm_judge_aggregate.json` and `llm_judge_per_text.csv` exactly. `PROMPT_COMPARISON_bullet.md`'s figures also match the raw CSV/JSON on spot-check (e.g. word-count diff +13.458 = 279.542 − 266.083 mean).

**Reference-integrity issue:** `PROMPT_COMPARISON_bullet.md` (line 3) and STATUS.md both reference `v1_prose/metrics/PROMPT_COMPARISON_prose.md` as the v1 counterpart. **That path does not exist in this working tree** (current branch: `prompt-bullet`). It exists only on the separate `prompt-prose` branch (confirmed via `git branch -a`), and STATUS.md's own 2026-07-28 note flags this ("v1_prose was not touched — it doesn't exist on this branch"). If Findings cites v1 prose numbers for comparison, check out `prompt-prose` to retrieve them — do not assume they're in the current tree.

---

## 6. File Checklist for Writing Findings

**Automated metrics**
- `v2_bullet/metrics/PROMPT_COMPARISON_bullet.md`
- `v2_bullet/metrics/metrics_per_summary_bullet.csv`
- `v2_bullet/metrics/metrics_per_summary_bullet.json` (same data, higher precision)

**LLM-as-judge**
- `v2_bullet/judge/LLM_JUDGE_COMPARISON.md`
- `v2_bullet/judge/llm_judge_aggregate.json`
- `v2_bullet/judge/llm_judge_per_text.csv`
- `v2_bullet/judge/llm_judge_raw.json` (for quoting specific `justification` strings, e.g. the faithfulness-gap explanation)
- `v2_bullet/rubric/rubric_comprehension.txt`, `v2_bullet/rubric/rubric_faithfulness.txt`

**Human comprehension study**
- `HUMAN_STUDY_FINDINGS.md` (full report — this is the primary source for the Findings chapter's human-study material)
- `data/human_study/response_summary.csv`, `comprehension_long.csv`, `likert_long.csv` (regenerable via `src/analyze_human_study.py`)
- `METHODOLOGY_LOG.md` Stage 8 (design and verification steps, not results)

**Figures**
- All 6 files (PNG+SVG) in `v2_bullet/figures/`, listed in Section 4.

**Cross-check / methodology sourcing**
- `STATUS.md` (trust the dated notes, not the stale checklist)
- `METHODOLOGY_LOG.md` — Stage 6c (generation run), Stage 6d (metrics, FK exclusion rationale), Stage 6e (judge design, rubric verbatim, bias mitigations, and the manual faithfulness-gap note)
