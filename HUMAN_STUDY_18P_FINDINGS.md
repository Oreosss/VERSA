# HUMAN_STUDY_18P_FINDINGS.md

_Fresh analysis of the human comprehension study at n=18 raw recorded responses (up from the n=17 recorded / n=15 technical-background sample used in `HUMAN_STUDY_FINDINGS.md` and `HUMAN_STUDY_DEMOGRAPHICS.md`, both 2026-08-10). This document does not rely on, or attempt to reconcile with, those earlier write-ups; every number below is read directly from `data/human_study/response_summary.csv`, `comprehension_long.csv`, and `likert_long.csv`, and from the tables/figures produced by `src/analyze_human_study_18p.py`. The two earlier documents are untouched and remain the record for the n=15 analysis. Created 2026-08-11._

One new response (`R_5Eznt1RPReTcuu0`, block F, 20/20 items, arrived 2026-08-10 21:32) was folded into `data/human_study/qualtrics_export_recorded.csv` via a fresh Qualtrics export, then `src/analyze_human_study.py` was re-run to regenerate the three derived CSVs this document reads from. That base pipeline's own integrity checks (condition-pattern verification against `survey_source.txt`, answer-key verification, block-vs-`Version`-field consistency) all still pass with zero mismatches at n=18, see that script's console output.

All tables referenced below are in `data/human_study/18p_tables/`; all figures are in `figures/human_study_18p/`.

---

## 1. Data schema (Step 1)

| File | Join key | Notable columns |
|---|---|---|
| `response_summary.csv` | `response_id` | `s1_technical_background`, `s2_security_training`, `s3_cve_familiarity` (demographics), `n_items_answered_of_20`, `duration_seconds` |
| `comprehension_long.csv` | `response_id` (+ `cve_id`, `condition`, `question_num` for a unique row) | `condition` in `{NVD, Summary}`, `question_num` in `{1,2,3}`, `is_correct` |
| `likert_long.csv` | `response_id` (+ `cve_id`, `condition` for a unique row) | `clarity_score`, `confidence_score` (1-5) |

- **Condition encoding:** `condition` column, values `NVD` (raw description) or `Summary` (LLM three-part summary).
- **CVE encoding:** `cve_id` column, e.g. `CVE-2020-8010`.
- **Question number encoding:** `comprehension_long.question_num`, values 1/2/3. Verified against `data/human_study/survey_source.txt` (not assumed): for all 12 CVEs, Q1 asks which component/software is affected ("what's vulnerable"), Q2 asks what an attacker needs or does ("how exploited"), Q3 asks about affected/fixed versions ("what action to take"). This lines up exactly with the thesis's three-part summary structure, so `question_num` is treated as the question-type field throughout this document (1=what's vulnerable, 2=how exploited, 3=remediation).
- **S3 value set** (as it actually appears in the data, free text, not a coded scale): `I have never worked with them`, `I have seen them occasionally but do not work with them regularly`, `I work with them from time to time as part of my role`, `I work with them regularly` (this fourth option is defined in the instrument but was not selected by anyone in this sample).

**S1=No exclusion:** raw pool (all rows in `response_summary.csv`, recorded + in-progress) n=25. Excluded for `S1=No`: n=1 (`R_2V23IjInwIyOO34`). Remaining n=24.

**Analysis sample** (the population this document uses throughout: `S1=Yes` and reached at least one item): **n=16**.
- Primary group (`S1=Yes`, `S2=No`): **n=12**
- Contrast group (`S1=Yes`, `S2=Yes`): **n=4**

One further technical-background respondent (`R_1NrDYHyqpv7gdml`, `S2=Yes`) consented and answered S1/S2/S3 but abandoned immediately afterward (0/20 items) and is in the raw pool but not the analysis sample.

---

## 2. Sample characterisation

**S1** (full raw pool, n=25): Yes=22, No=1, blank/unanswered=2.

**S2** (analysis sample, n=16): No=12, Yes=4.

**S3** (analysis sample, n=16): never worked with them=7, seen occasionally=6, time to time as part of role=3, regularly=0.

Figure: [`p1_s3_histogram.png`](figures/human_study_18p/p1_s3_histogram.png).

**S2 x S3 crosstab** (`p1_s2_x_s3_crosstab.csv`):

| S2 | Never | Seen occasionally | Time to time (role) |
|---|---|---|---|
| No (n=12) | 6 | 4 | 2 |
| Yes (n=4) | 1 | 2 | 1 |

Every cell except "No / Never" (n=6) is below 5 and is descriptive / audit-trail-only, not a group comparison to draw conclusions from.

**Baseline NVD-only accuracy** (`p1_baseline_nvd_accuracy_by_s2.csv`, `..._by_s3.csv`), the comprehension deficit the tool targets, measured only on raw-NVD entries:

| By S2 | Accuracy | n items |
|---|---|---|
| No | 81.9% | 72 |
| Yes | 85.7% | 21 |

| By S3 | Accuracy | n items |
|---|---|---|
| Never worked with them | 78.6% | 42 |
| Seen occasionally | 83.3% | 36 |
| Time to time (role) | 93.3% | 15 |

Even on raw NVD text alone, the least-familiar group is answering roughly 1 in 5 comprehension questions wrong, and the deficit shrinks monotonically with self-reported familiarity, before the summary is introduced at all.

**Composition** (`p1_composition_counts.csv`):

| Group | n |
|---|---|
| Raw pool total | 25 |
| Excluded (S1=No) | 1 |
| Analysis sample (S1=Yes, reached content) | 16 |
| Primary (S1=Yes, S2=No) | 12 |
| Contrast (S1=Yes, S2=Yes) | 4 |

---

## 3. Did the summary help

Accuracy overall and by question type, analysis sample (n=16 respondents, 186 scored items), bootstrap 95% CIs resampling respondents (not items) with replacement, 10,000 resamples (`p2_condition_x_questiontype_bootstrap.csv`):

| Question type | NVD | Summary | Gap (Summary - NVD) | 95% CI | n items each |
|---|---|---|---|---|---|
| Overall | 82.8% | 86.0% | +3.2pp | [-5.2, +11.1]pp | 93 |
| Q1: what's vulnerable | 80.6% | 87.1% | +6.5pp | [-9.4, +21.9]pp | 31 |
| Q2: how exploited | 90.3% | 87.1% | -3.2pp | [-13.3, +6.7]pp | 31 |
| Q3: what action to take | 77.4% | 83.9% | +6.5pp | [-15.6, +29.0]pp | 31 |

Every CI spans zero: at n=16 respondents, none of these gaps is distinguishable from no effect. The point estimates are directionally consistent with the thesis hypothesis for "what's vulnerable" and "what action to take" (the two weakest raw-NVD categories), and reversed, though not significantly, for "how exploited," where the raw description already scores highest of the three (90.3%). Cell n is 31 items per condition per question type throughout; table `p2_condition_x_questiontype_n.csv` confirms this is balanced.

Figure: [`p2_condition_x_questiontype.png`](figures/human_study_18p/p2_condition_x_questiontype.png).

---

## 4. Felt vs demonstrated understanding

**Clarity and confidence means by condition** (`p3_clarity_confidence_by_condition.csv`, n=31 rated entries each):

| Condition | Clarity | Confidence |
|---|---|---|
| NVD | 3.61 | 3.71 |
| Summary | 4.06 | 4.06 |

**Participant-level clarity preference** (`p3_clearer_tally.csv`, n=16, comparing each respondent's mean NVD-entry clarity to their mean Summary-entry clarity):

| Rating | n participants |
|---|---|
| NVD clearer | 2 |
| Summary clearer | 10 |
| Equal | 4 |

**Per-CVE rank correlation, clarity vs accuracy** (`p3_cve_clarity_vs_accuracy.csv`, n=12 CVEs, both conditions pooled per CVE): Spearman rho = 0.376, p = 0.228. A weak positive trend, not significant at this n: clearer-rated CVEs tend to also be more accurately answered, but the relationship is loose, not a tight coupling.

**Confidence on correct vs incorrect entries, by condition** (`p3_confidence_correct_vs_incorrect.csv`; an entry is "fully correct" if all 3 of its MC questions were answered correctly):

| Condition | Entry outcome | Mean confidence | n entries |
|---|---|---|---|
| NVD | Not fully correct | 3.54 | 13 |
| NVD | Fully correct | 3.83 | 18 |
| Summary | Not fully correct | 3.78 | 9 |
| Summary | Fully correct | 4.18 | 22 |

Confidence tracks correctness in both conditions (correct > incorrect): the NVD gap is 3.83-3.54=0.29, the Summary gap is 4.18-3.78=0.40. Summary respondents are not simply more confident regardless of outcome; the confidence-accuracy relationship is at least as well calibrated under Summary as under NVD, by this measure.

**High-confidence-wrong counts** (`p3_high_confidence_wrong_by_condition.csv`; confidence >=4 on an entry that was not fully correct):

| Condition | Overconfident entries | n entries | Rate |
|---|---|---|---|
| NVD | 9 | 31 | 29.0% |
| Summary | 5 | 31 | 16.1% |

The summary does not inflate confidence on wrong answers relative to NVD in this sample; if anything the overconfidence rate is lower under Summary. This is the opposite of the "false fluency" risk the probe was designed to catch.

Figure: [`p3_clarity_vs_accuracy_scatter.png`](figures/human_study_18p/p3_clarity_vs_accuracy_scatter.png) (per-CVE-per-condition points, n=12 CVEs x 2 conditions = 24 points).

---

## 5. Who does it help: the core subgroup test

**Primary vs contrast group gain** (`p4_subgroup_gain.csv`), bootstrap 95% CI resampling respondents within each group:

| Group | n respondents | NVD | Summary | Gain | 95% CI |
|---|---|---|---|---|---|
| Primary (S1=Yes, S2=No) | 12 | 81.9% | 83.3% | +1.4pp | [-8.3, +11.1]pp |
| Contrast (S1=Yes, S2=Yes) | 4 | 85.7% | 95.2% | +9.5pp | [0.0, +22.2]pp |

This is a genuinely unexpected headline result: the gain is small and not distinguishable from zero for the primary target population (technical, no formal security training), and larger, with a CI that just touches zero at its lower bound, for the security-trained contrast group. That is the opposite direction from the thesis's working hypothesis that the tool helps least-trained readers most. The contrast group's n=4 makes this fragile (see caveat below), but the primary group's own CI (n=12) is centred near zero, not merely wide, so this is not just a small-n artefact on one side.

**Gain by S3 familiarity level** (`p4_subgroup_gain.csv`):

| S3 level | n respondents | Gain | 95% CI |
|---|---|---|---|
| Never worked with them | 7 | +7.1pp | [-4.8, +19.0]pp |
| Seen occasionally | 6 | -2.8pp | [-16.7, +11.1]pp |
| Time to time (role) | 3 | +6.7pp | [0.0, +33.3]pp |

No monotonic pattern by familiarity: the least-familiar group does show a positive point-estimate gain, consistent with the "helps least-familiar most" hypothesis, but the middle group's gain is negative and the most-familiar group's gain is similar in size to the least-familiar group's, not smaller. All three CIs span zero except the most-familiar group's, whose lower bound is exactly 0.0 (n=3, treat as descriptive).

**Any subgroup worse off with the summary** (`p4_worse_off_subgroups.csv`): one, the "seen occasionally" S3 group (gain -2.8pp, n=6, CI [-16.7, +11.1]pp spans zero). No S2 subgroup, and no other S3 subgroup, shows a negative point estimate.

**Does S3 self-report actually predict demonstrated accuracy** (self-report-bias check, `p4_per_respondent_accuracy_vs_s3.csv`): per-respondent overall accuracy (both conditions pooled) vs S3 ordinal rank, Spearman rho = 0.202, p = 0.454, n=16. Weak and not significant. This sits alongside the monotonic *group-level* baseline-NVD trend in Section 2 (78.6% -> 83.3% -> 93.3% by S3 level): the group averages move in the expected direction, but individual-level self-report is a noisy predictor of an individual's actual comprehension accuracy at this n, i.e. self-reported familiarity is informative in aggregate but should not be read as a reliable per-person proxy.

**Accuracy by condition x S2 and x S3** (`p4_accuracy_by_condition_x_s2.csv`, `p4_accuracy_by_condition_x_s3.csv`):

| Condition | S2=No | S2=Yes |
|---|---|---|
| NVD | 81.9% (n=72) | 85.7% (n=21) |
| Summary | 83.3% (n=72) | 95.2% (n=21) |

| Condition | Never (n=42) | Seen occasionally (n=36) | Time to time (n=15) |
|---|---|---|---|
| NVD | 78.6% | 83.3% | 93.3% |
| Summary | 85.7% | 80.6% | 100.0% |

Figure: [`p4_gain_by_subgroup.png`](figures/human_study_18p/p4_gain_by_subgroup.png) (S3-level gain, left; S2 primary/contrast gain, right; error bars are the bootstrap 95% CIs above).

---

## 6. Artefact / integrity checks

**Accuracy by slot position** (1st-4th CVE seen within a block, `p5_accuracy_by_slot.csv`):

| Slot | Accuracy | n items |
|---|---|---|
| 1 | 89.6% | 48 |
| 2 | 66.7% | 48 |
| 3 | 86.7% | 45 |
| 4 | 95.6% | 45 |

Slot 2 is a clear dip, but this is confounded with CVE identity, not a clean order effect: the study design fixes which CVE sits in which slot within each quad (see `src/analyze_human_study.py` `BLOCK_SLOTS`), and slot 2 across all three quads happens to hold CVE-2021-21974, CVE-2023-43661, and CVE-2023-44221, three of the four hardest CVEs by the per-CVE accuracy table (`p1`/base pipeline output: CVE-2023-44221 55.6%, CVE-2021-21974 72.2%, CVE-2023-43661 75.0%, all below the 12-CVE median). Slot and item difficulty cannot be separated with this fixed design; the dip should not be read as fatigue or order bias without that caveat.

**Rushed-response flag** (`p5_rushed_flagged.csv`): one respondent, `R_3dWEiMCm5OvAjyG`, completed a full 20/20-item block in 117 seconds, next-fastest full-block completion was 519 seconds (4.4x slower). 117s across 4 CVE entries (each with a CVSS/KEV/EPSS table, a description or summary, and 5 questions) is implausible as genuine reading and answering time, so it is flagged as a data-quality outlier, not merely a fast reader.

**Headline gap with and without the rushed response** (`p5_headline_gap_rules.csv`):

| Rule | Gap | n items | n respondents |
|---|---|---|---|
| All items | +3.2pp | 186 | 16 |
| Minus rushed response | +4.6pp | 174 | 15 |

Removing the rushed respondent widens the headline gap slightly. Their own within-respondent split ran counter to the headline direction (NVD 50.0% vs Summary 33.3%, 6 items each, a -16.7pp swing against Summary), so removing them removes a drag on the overall gap rather than removing noise that happened to favour it. The direction of the headline finding is unchanged either way.

**Same CVE, NVD vs Summary, holding CVE constant** (`p5_same_cve_paired.csv`, all 12 CVEs):

| CVE | NVD | Summary | NVD - Summary |
|---|---|---|---|
| CVE-2020-8010 | 77.8% (n=9) | 88.9% (n=9) | -11.1pp |
| CVE-2021-21974 | 77.8% (n=9) | 66.7% (n=9) | +11.1pp |
| CVE-2021-22204 | 100.0% (n=6) | 66.7% (n=12) | +33.3pp |
| CVE-2021-30970 | 100.0% (n=6) | 100.0% (n=3) | 0pp |
| CVE-2021-42013 | 83.3% (n=6) | 91.7% (n=12) | -8.3pp |
| CVE-2022-3062 | 77.8% (n=9) | 100.0% (n=9) | -22.2pp |
| CVE-2022-40765 | 100.0% (n=12) | 100.0% (n=6) | 0pp |
| CVE-2023-21608 | 88.9% (n=9) | 88.9% (n=9) | 0pp |
| CVE-2023-29119 | 100.0% (n=6) | 100.0% (n=6) | 0pp |
| CVE-2023-43661 | 50.0% (n=6) | 100.0% (n=6) | -50.0pp |
| CVE-2023-44221 | 58.3% (n=12) | 50.0% (n=6) | +8.3pp |
| CVE-2024-21887 | 100.0% (n=3) | 100.0% (n=6) | 0pp |

Several cells have n<5 within a condition (CVE-2021-22204 NVD n=6 is fine but its Summary side n=12 vs NVD n=6 is unbalanced because the counterbalanced blocks were not drawn from evenly across this sample; CVE-2021-30970 Summary n=3 and CVE-2024-21887 NVD n=3 are both below 5) and should be read as descriptive, not powered per-CVE comparisons.

**CVEs where NVD beats Summary** (pooled across all 3 questions): CVE-2021-21974 (+11.1pp), CVE-2021-22204 (+33.3pp), CVE-2023-44221 (+8.3pp). All three are among the hardest CVEs overall (see Section 6, slot discussion) rather than cases where NVD is unusually strong; both conditions do worse on these three, NVD simply does less badly.

**Item-level (CVE x question) cells where NVD beats Summary** (`p5_nvd_beats_summary_items.csv`, 7 of 36 CVE x question cells):

| CVE | Question | NVD | Summary | NVD - Summary | n (NVD / Summary) |
|---|---|---|---|---|---|
| CVE-2021-22204 | Q1 (what's vulnerable) | 100.0% | 50.0% | +50.0pp | 2 / 4 |
| CVE-2023-44221 | Q3 (remediation) | 50.0% | 0.0% | +50.0pp | 4 / 2 |
| CVE-2021-21974 | Q1 | 100.0% | 66.7% | +33.3pp | 3 / 3 |
| CVE-2021-21974 | Q2 (how exploited) | 100.0% | 66.7% | +33.3pp | 3 / 3 |
| CVE-2021-22204 | Q2 | 100.0% | 75.0% | +25.0pp | 2 / 4 |
| CVE-2021-22204 | Q3 | 100.0% | 75.0% | +25.0pp | 2 / 4 |
| CVE-2021-42013 | Q2 | 100.0% | 75.0% | +25.0pp | 2 / 4 |

Every one of these cells has an n of 2, 3, or 4 on at least one side (all below 5); descriptive / audit-trail-only, not evidence of a systematic Summary weakness on any one question type (CVE-2021-22204 alone accounts for 3 of the 7 rows).

**Items failing the same way in both conditions** (`p5_defective_items_both_conditions.csv`, threshold: both NVD and Summary accuracy < 50% for the same CVE x question): **none found**, at n=18. No comprehension item in this study is failing regardless of presentation format; where accuracy is low, it differs by condition, not by a shared defect in the question or the underlying CVE record. This is a positive integrity signal for the instrument itself.

**Headline gap under each rule** (`p5_headline_gap_rules.csv`):

| Rule | Gap | n items | n respondents |
|---|---|---|---|
| All items | +3.2pp | 186 | 16 |
| Minus format-independent defective items | +3.2pp (unchanged; 0 items removed) | 186 | 16 |
| Minus rushed responses | +4.6pp | 174 | 15 |

---

## 7. Not answerable from available fields

None of the probes in the brief required a field this instrument does not collect. The demographic instrument is exactly S1 (technical background), S2 (formal security training), S3 (CVE/CVSS familiarity), confirmed in Section 1; no probe above needed a role, seniority, or occupation field, and none was skipped.

---

## Headline summary

At n=16 (12 primary + 4 contrast), the summary-vs-NVD comprehension gap is small (+3.2pp overall) and not statistically distinguishable from zero at this sample size, consistent with the automated-metrics stage's own framing of pilot-scale, descriptive-only results. The most notable and unexpected finding is in Section 5: the accuracy gain from the summary is centred near zero for the primary target population (technical, no security training, n=12) and larger for the security-trained contrast group (n=4), the reverse of the thesis's working hypothesis that the tool helps least-trained readers most, though the contrast group is too small to treat this as settled. Felt-vs-demonstrated results are more consistent: participants rate the summary clearer and more confidence-inspiring than raw NVD (Section 4), and the summary does not inflate confidence on wrong answers relative to NVD, if anything the opposite. Integrity checks (Section 6) find no evidence of a broken question or CVE (no item fails in both conditions), one clearly rushed response whose removal slightly widens rather than narrows the headline gap, and a slot-position dip that is confounded with fixed CVE-to-slot assignment rather than a clean fatigue effect.
