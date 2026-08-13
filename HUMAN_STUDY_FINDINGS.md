# HUMAN_STUDY_FINDINGS.md

_Factual record of the human comprehension study (Stage 8). Generated from direct inspection of `data/human_study/` and the output of `src/analyze_human_study.py`. Every number below is read from the script's output, not estimated. This document is the primary results record; `METHODOLOGY_LOG.md` Stage 8 records the study design and verification steps, `FINDINGS_LOG.md` Section 3 summarises the headline figures for the Findings chapter, and `DISCUSSION_SOURCE_PACK.md` Section 5 pulls the discussion-relevant material — all added/updated 2026-08-10, after this document. Last updated: 2026-08-10, after two revisions on the same day: (1) two late responses (`R_5AMEuutsNvp3PVV`, `R_1BsF3Jz93sc6q3v`) were folded in via a fresh Qualtrics CSV export, not the hand-transcribed PDF read initially used to sanity-check them; (2) the one respondent without a technical background was excluded from the main analysis — see §3.1._

---

## 1. Data sources

| File | Contents |
|---|---|
| `data/human_study/survey_source.txt` | Qualtrics import file: verbatim stimulus HTML and MC choice lists actually shown to participants |
| `data/human_study/answer_key.txt` | Supplied answer key (72 items) — **verified against the source below, not trusted as-is** |
| `data/human_study/qualtrics_export_recorded.csv` | 17 finalised response rows (`R_...` IDs) |
| `data/human_study/qualtrics_export_inprogress.csv` | 7 in-progress/abandoned response rows (`FS_...` IDs), exported separately |
| `src/analyze_human_study.py` | Parses all of the above, verifies the answer key, scores comprehension, aggregates, and applies the exclusion in §3.1 |

Script outputs (regenerable, not hand-edited): `response_summary.csv` (all responses, unfiltered), `comprehension_long.csv` / `likert_long.csv` (all responses; the exclusion in §3.1 is applied at aggregation time, not by removing rows from these files), `answer_key_check.csv`, all in `data/human_study/`.

---

## 2. Study design (recovered from the source, not just described)

Three CVE "quads" (fixed sets of 4 CVEs drawn from different severity×exploitability cells of the 24-CVE eval sample), each with two counterbalanced presentation orders:

| Quad | Blocks | CVEs (slot 1–4) |
|---|---|---|
| 1 | A / B | CVE-2020-8010, CVE-2021-21974, CVE-2022-3062, CVE-2023-21608 |
| 2 | C / D | CVE-2023-29119, CVE-2023-43661, CVE-2021-30970, CVE-2024-21887 |
| 3 | E / F | CVE-2021-42013, CVE-2023-44221, CVE-2021-22204, CVE-2022-40765 |

Each participant is randomly assigned to exactly **one** of the six blocks (A–F) and answers on 4 CVEs only. Within a block, presentation condition alternates by slot; the paired block flips it:

- **A / C / E**: slot 1 = raw NVD, slot 2 = LLM summary, slot 3 = raw NVD, slot 4 = LLM summary
- **B / D / F**: slot 1 = LLM summary, slot 2 = raw NVD, slot 3 = LLM summary, slot 4 = raw NVD

**Verified programmatically, not assumed:** `analyze_human_study.py` classifies each of the 24 stimulus blocks in `survey_source.txt` as NVD (a single plain paragraph) or Summary (the three-header "What is vulnerable / How it can be exploited / What action to take" structure) directly from the HTML, and confirms this matches the pattern above for all 24 slots with zero mismatches. It also confirms, for every recorded response that reached a block, that the active block inferred from which columns were answered matches the CSV's own `Version` field in every case (zero mismatches across all 17 recorded responses) — the block assignment is internally consistent.

**Both conditions show identical structured metadata.** A technical-context table (CVE ID, severity, attack vector, privileges required, user interaction, C/I/A impact, KEV status, EPSS score) is displayed above the stimulus text in *both* the NVD and Summary conditions. The only thing that differs between conditions is the prose narrative — the free-text description vs. the three-part LLM summary — not the structured CVSS/KEV/EPSS fields. This is a materially different scope than the automated LLM-as-judge faithfulness evaluation (`METHODOLOGY_LOG.md` Stage 6e / `DISCUSSION_SOURCE_PACK.md` §1), which scored faithfulness against the bare NVD description field only, with the CVSS sub-fields and KEV/EPSS excluded from the reference. The human study, by construction, gives both conditions equal access to that structured data; it isolates the narrative/comprehension question specifically.

**Answer key verified, not trusted.** All 72 supplied answer-key entries were independently checked against the first-listed MC choice for that question in `survey_source.txt` (the source states the correct answer is always the first-listed choice). **All 72 agree — zero discrepancies.**

---

## 3. Sample

| | Count |
|---|---|
| Total raw response attempts (both exports) | 24 |
| — from `qualtrics_export_recorded.csv` | 17 |
| — from `qualtrics_export_inprogress.csv` | 7 |
| Consented (`C1` = "Yes, I consent") | 24 / 24 |
| Reached at least one CVE entry | 16 |
| Completed a full block (20/20 items: 4 CVEs × 5 questions) | 15 |
| Partial block (some but not all items) | 1 (`R_z1BKukAYP47eJvr`, 10/20 — answered slots 1–2 of block D in full, did not reach slots 3–4) |
| Consented then abandoned before any CVE entry (0/20 items) | 8 |

Two responses (`R_5AMEuutsNvp3PVV`, block B; `R_1BsF3Jz93sc6q3v`, block A) arrived after the initial version of this document and are folded into all figures below via a clean re-export, not the earlier hand-transcribed PDF read (which, on comparison, scored the 12 MC comprehension items correctly in both cases but mis-read two Likert ratings — the CSV export is authoritative and superseded it).

**Block distribution** among the 16 who reached at least one item: A=3, B=4, C=2, D=2, E=2, F=3. Every block was used by at least 2 participants; no block went unused.

### 3.1 Exclusion: one respondent outside the target population

The thesis's target population (`CLAUDE.md`) is technical non-security personnel — developers, CS students. One respondent, `R_2V23IjInwIyOO34` (block B, 20/20 items answered), answered **No** to `S1` ("Do you have a technical background?"). This is a scope mismatch, not a low score: this person is outside the population the tool is meant to help, so their result is **excluded from the main analysis in §4 and §5 below**, not averaged in as ordinary variance.

For transparency: `R_2V23IjInwIyOO34`'s comprehension accuracy was 16.7% (2/12 correct) — far below every technical-background respondent (range 41.7%–100%, see §4.3) — consistent with the exclusion rationale (a genuinely different population, not noise). This number is reported here and nowhere else; it is not part of any aggregate below.

**Post-exclusion analysis sample: 15 technical-background respondents** (14 complete blocks + 1 partial), all with `S1` = Yes.

### 3.2 One further respondent held out pending review, not counted anywhere in this document

An 18th response, `R_5Eznt1RPReTcuu0` (block F, technical background, 20/20 items, completed 2026-08-10), appeared in `qualtrics_export_recorded.csv` after every figure in this document had already been computed and written up. It is **not a scope exclusion like §3.1** — it is technical-background and otherwise eligible — it is held out purely because it arrived after the fact and has not yet been reviewed or folded into a full re-run. `src/analyze_human_study.py` excludes it explicitly (`pending_review_ids`, alongside the §3.1 exclusion) so the script continues to reproduce the n=15 figures in this document rather than silently drifting to n=16. Folding it in requires a deliberate re-run and a full pass over every headline number in this document, `HUMAN_STUDY_DEMOGRAPHICS.md`, `STATUS.md`, `FINDINGS_LOG.md`, and `DISCUSSION_SOURCE_PACK.md` — not done as of this writing.

---

## 4. Comprehension results (3 MC questions per CVE entry, n=15 technical-background respondents)

**174 scored items total** (14 full responses × 12 items + 1 partial response × 6 items).

### 4.1 By condition

| Condition | Accuracy | n |
|---|---|---|
| NVD (raw) | 83.9% | 87 |
| Summary (LLM) | 88.5% | 87 |

A gap of +4.6 points in favour of the LLM summary. This widened after excluding the non-technical-background respondent (was +2.5 points, 77.8% vs 80.2%, when that respondent's uniformly-low scores were mixed into both conditions) — removing a genuine population mismatch sharpened the comparison rather than just shrinking the sample. It is still a small-N result (87 items per condition, drawn from 15 respondents each answering only 2 items per condition per CVE) and should be reported as **directionally consistent with the thesis hypothesis, not as a powered result** — consistent with how the automated-metrics stage treats its own n=24 (descriptive statistics and effect sizes only, no significance test; `FINDINGS_LOG.md` §1).

### 4.2 By condition × question number

| Condition | Q1 (what's affected) | Q2 (how exploited) | Q3 (remediation/versions) |
|---|---|---|---|
| NVD | 82.8% | 93.1% | 75.9% |
| Summary | 89.7% | 89.7% | 86.2% |

Q3 (remediation/version questions) is the weakest for both conditions — the largest source of wrong answers is not "what's vulnerable" but "which version fixes it," in both raw and summarised form. Summary leads NVD on Q1 and Q3; the two conditions are roughly level on Q2, where NVD's dense technical description language is apparently no harder to parse (numerically it's slightly *better* here, 93.1% vs 89.7%) than the LLM prose.

### 4.3 The clearest outlier is a rushed response, not a condition effect

Per-respondent accuracy, technical-background sample only:

| Respondent | Accuracy | Duration (s) |
|---|---|---|
| R_3dWEiMCm5OvAjyG | **41.7%** (5/12) | **117 (rushed)** |
| R_28BpNaOAXOVFUBu | 75.0% | 1286 |
| 6 respondents (R_1qVfAylDhwjOuec, R_25L2ocH4GqwynxW, R_3PRVpBt6CEvC9ro, R_50TZzn6D3lyloNX, R_5UHaJ323aSKYjJv, R_z1BKukAYP47eJvr [partial, 6 items]) | 83.3% each | 315–97,728 |
| R_1BPfKyLwsRPAw6m, R_3JgiWQCENHgWKH6, R_OOINYxIuH9S4pyh | 91.7% each | 1829–9827 |
| R_1BsF3Jz93sc6q3v, R_50xbc0ffVBVZgV7, R_5AMEuutsNvp3PVV, R_87Bi1GGOuqsGWRz | **100%** each | 519–1777 |

With the population mismatch removed, the standout outlier is `R_3dWEiMCm5OvAjyG` — the same response already flagged for completing a full 20-item block (4 full vulnerability entries, some several paragraphs, plus 20 questions) in **117 seconds**, implausibly fast for genuine reading. Its low accuracy (41.7%, the only score below 75% in the technical-background sample) is best attributed to rushed/low-effort responding rather than to condition or genuine comprehension difficulty. **A future run of this study should add a minimum-duration exclusion criterion or attention check** rather than relying on post-hoc judgement calls like this one.

Excluding this one additional response as a data-quality flag (not a scope exclusion like §3.1, so not applied to the headline figures above, but worth stating): the remaining 14 technical-background, non-rushed respondents cluster tightly between 75% and 100%, a much narrower spread than the raw range suggests.

### 4.4 Two items show a content-validity problem independent of condition

**CVE-2020-8010, Q1 ("which component is affected"):** wrong in 3 of 6 exposures (technical-background sample), split across both conditions. Both the raw NVD text and the LLM summary state the answer explicitly ("robot (controller) component"), so this is not a presentation-format effect — the term itself ("robot (controller) component," UIM-specific jargon naming an agent process, easily misread as literal robotics/OS-related) appears to be a genuine comprehension trap regardless of how it's presented.

**CVE-2023-44221, Q3 ("what does the record state about versions"):** wrong in 4 of 5 exposures (technical-background sample), across both conditions, consistently confusing "no fixed version is named, firmware up to X is affected" (correct) with "all firmware versions ever released are affected with no upper bound" (distractor) — a subtle wording distinction that trips people up in both formats and is currently the single weakest item in the whole instrument.

**CVE-2021-22204 / CVE-2021-42013, Q3 ("which versions... resolves it"): a genuine survey design flaw, self-reported by a participant.** The correct answer text is *"Versions from 7.44 up are affected, and 12.24 or later resolves it."* Checked directly against both stimulus texts in `survey_source.txt`: **neither the raw NVD paragraph nor the LLM summary states "12.24" anywhere.** The summary explicitly says only "update to a version that includes this fix" without naming a version. One participant (`R_OOINYxIuH9S4pyh`) flagged this unprompted in the optional free-text field: *"in vulnerability 3 question, it didn't state there was a fix for exfil tool version 12.24 or later but that seemed like the most correct option."* Most participants still selected the correct option by elimination (the other three choices are more obviously wrong), which is why this item's aggregate accuracy looks fine — but the item does not actually test comprehension of the text shown; it rewards world knowledge or elimination reasoning. **This should be corrected (or excluded) before any future run of this study** and reported as a known instrument limitation.

### 4.5 By CVE × condition (n per cell = 3–9 items; too small for per-cell conclusions, included for completeness / audit trail)

See `data/human_study/comprehension_long.csv` for the full item-level table (technical-background respondents can be isolated by joining against `response_summary.csv` where `s1_technical_background = "Yes"`). Aggregate cell accuracies range from 50% to 100%; no cell has enough independent respondents (max 3 per condition) to support a standalone claim.

---

## 5. Likert results (clarity, confidence — 5-point scale, 1=Strongly disagree, 5=Strongly agree, n=15 technical-background respondents)

**58 rated entries** (14 full responses × 4 CVEs + 1 partial × 2 CVEs).

| Condition | Clarity mean | Confidence mean | n |
|---|---|---|---|
| NVD | 3.69 | 3.79 | 29 |
| Summary | 4.17 | 4.10 | 29 |

The Summary condition rates higher on both dimensions — a gap of +0.48 clarity and +0.31 confidence on a 5-point scale, both wider than in the unfiltered sample (+0.33 / +0.19), for the same reason as the comprehension gap: removing a population mismatch sharpened rather than diluted the comparison. n=29 per condition is still small; treat as directional. Self-reported clarity/confidence does **not** track measured comprehension accuracy particularly closely at the per-CVE level (see `data/human_study/likert_long.csv` for the full per-CVE breakdown) — a reminder that self-reported understanding and demonstrated comprehension are not interchangeable, and both are worth reporting rather than treating Likert as a proxy for the MC score.

---

## 6. Qualitative comments (verbatim, from the optional closing free-text field)

**`R_OOINYxIuH9S4pyh`** (block F, 91.7% accuracy):
> in vulnerability 3 question, it didn't state there was a fix for exfil tool version 12.24 or later but that seemed like the most correct option

Directly corroborates the content-validity issue in §4.4.

**`R_5UHaJ323aSKYjJv`** (block F, 83.3% accuracy):
> I felt case 2 and 4 could have had more information added to them but overall I think it was clear.

**`R_25L2ocH4GqwynxW`** (block F, 83.3% accuracy):
> Nothing. Great work. Wishing you the best in your research.

**`R_50xbc0ffVBVZgV7`** (block C, 100% accuracy) — the longest and most substantive comment, directly relevant to the thesis's core premise and worth quoting in full for the Discussion chapter:
> CVEs are a dumb political system that leads to security and engineering teams getting misleading impressions on the severity of defects. In addition, some vulnerabilities don't get the CVEs they deserve.
>
> Thinking more about the problem: It is generally best practice to look at example exploit code, read advisories published by subject matter experts, and look at source code. Having an LLM summarize a CVE is just deferring responsibility, and hiding the issue that CVEs should just be better structured.

This is a substantive critique of the project's core premise from a participant who scored 100% comprehension in the study (block C, mixed NVD/Summary) — i.e. it is not the view of someone who struggled to understand either format. The critique has two separable parts worth treating separately in the Discussion: (1) a claim about CVE severity scoring being politically/organisationally distorted (a critique of the underlying data source, not of this project's summarisation approach), and (2) a claim that LLM summarisation specifically "defers responsibility" and "hides" a structural problem rather than fixing it — i.e. that improving comprehension of a bad record is the wrong intervention compared to improving the record itself, or compared to reading primary sources (exploit code, vendor advisories) directly. This is a legitimate expert-adjacent objection to the thesis's framing and should be represented as a limitation/counterargument in the Discussion chapter rather than omitted because it's uncomfortable for the project's premise.

---

## 7. Flagged for the Discussion chapter (interpretation, not neutral fact — separated from §§1–6 deliberately)

1. **At n=15 technical-background respondents, the NVD-vs-Summary gap (comprehension +4.6pp, clarity +0.48, confidence +0.31) is directionally consistent with the thesis hypothesis but not distinguishable from noise.** This human pilot should be framed as a feasibility/pilot run, not a powered comparison — consistent with how the automated-metrics stage already treats its own n=24 ("descriptive statistics and effect sizes only, no significance test," `FINDINGS_LOG.md` §1).
2. **One respondent (`R_2V23IjInwIyOO34`) was excluded because they reported no technical background, outside the thesis's defined target population** (`CLAUDE.md`: "technical non-security personnel"). Their raw accuracy (16.7%) is reported in §3.1 for transparency but is not part of any headline figure. A future, larger run should screen for this at recruitment rather than post-hoc.
3. **The next-most extreme data point, a 117-second full-block response (`R_3dWEiMCm5OvAjyG`, 41.7% accuracy), is best explained by rushed/low-effort responding**, not condition. A minimum-duration exclusion or attention check is recommended for any future run.
4. **One MC item (the "12.24" fix-version question, asked twice as CVE-2021-22204/CVE-2021-42013 Q3) tests information not present in either stimulus**, self-reported by a participant. This is an instrument defect, not a finding about comprehension, and should be fixed or dropped before the next run.
5. **A substantive participant critique of the project's core premise exists in the data** (§6, `R_50xbc0ffVBVZgV7`) from a high-scoring respondent, and should be engaged with directly in the Discussion/Limitations rather than omitted.
6. **The human study's NVD condition is not equivalent to the automated LLM-judge's "raw NVD" reference.** The human study shows the same structured CVSS/KEV/EPSS table in both conditions; the LLM-judge faithfulness evaluation scored against the bare description field only. If the thesis compares human and automated results side by side, this scope difference needs to be stated explicitly — they are not measuring presentation of the same underlying artefact.
7. **83% Qualtrics progress with zero CVE answers recurs in 5 of 7 in-progress responses** — a possible friction point at the instructions→first-entry transition, worth a methods note even though it cannot be diagnosed further from this data alone.
8. **NVD readers are overconfident more than twice as often as Summary readers** (31.0% vs. 13.8% of entries; §11.1) — a distinct claim from the accuracy gap, and arguably the more thesis-relevant one: raw NVD text doesn't just produce more comprehension errors, it produces more errors readers don't recognise as errors. **Formal security training does not predict this** (untrained 22.7% vs. trained 21.4%), but familiarity with CVE data shows a non-monotonic pattern — the *partially*-familiar ("seen occasionally") subgroup is the most overconfident of the three (35.0%), more than the never-familiar group, while the format gap (NVD vs. Summary) all but disappears for that partially-familiar subgroup even as it stays large for true novices. Overconfidence is also concentrated in a few individuals and a few already-flagged weak items rather than spread evenly, so this should be framed as a real but fragile pattern (n=15) worth a larger follow-up, not a settled subgroup effect.
9. **The two items already flagged for content-validity problems (§4.4) show near-total distractor clustering, not scattered wrong answers** (§11.4) — corroborating, independent-of-eyeballing evidence that these are genuine stimulus-design flaws (missing/ambiguous remediation-version information) rather than participants guessing on fair-but-hard items.
10. **A response arrived in the export after this document's figures were already computed and has been deliberately held out pending review** (`R_5Eznt1RPReTcuu0`, §3.2) — a reminder that this data source is not fully static, and any future re-run needs an explicit "lock the dataset" step before headline numbers are drawn from it.

---

## 8. Addendum — breakdowns by S2 (formal training) and S3 (CVE/CVSS familiarity)

_Added after the initial version of this document, in response to a follow-up question. Technical-background sample only (n=15, per §3.1's exclusion); sourced from `analyze_human_study.py`'s printed output, not computed ad hoc. The survey collected exactly three demographic fields — `S1`, `S2`, `S3` — and `S1` is already the exclusion criterion in §3.1, so these two are the only further demographic splits the instrument supports; there is no age, role, or other field to break down by, and slicing S2×S3 jointly would leave cells of 1–2 respondents._

### 8.1 S2 — formal cyber security training

11 of the 15 technical-background respondents report no formal training; 4 report having some.

| S2 | Accuracy | n (items) |
|---|---|---|
| No | 84.8% | 132 |
| Yes | 90.5% | 42 |

By condition:

| S2 | NVD | Summary | Gap |
|---|---|---|---|
| No | 83.3% | 86.4% | +3.1pp |
| Yes | 85.7% | 95.2% | **+9.5pp** |

Trained respondents score a little higher overall, and the NVD-vs-Summary gap is *larger* for them, not smaller — counter to the naive expectation that trained readers would need the plain-language framing less. **This should not be read as a finding**: the trained group is 4 respondents / 21 items per condition, thin enough that one different response would change the direction of the gap. Training also doesn't cleanly separate top and bottom performers — the rushed 117-second outlier (§4.3, 41.7% accuracy) has no formal training, but so do 3 of the 4 respondents who scored a perfect 100%; untrained respondents span the full range, trained respondents happen to cluster higher but there are too few of them to call that a pattern.

Likert: trained respondents rate both conditions somewhat higher (clarity 4.07 vs 3.89; confidence 4.29 vs 3.84 for untrained) — same small-n caveat.

### 8.2 S3 — familiarity with CVE records / CVSS scores

7 respondents "have never worked with them," 5 have "seen them occasionally," 3 "work with them from time to time" as part of their role (the fourth S3 option, "work with them regularly," was not selected by anyone in this sample).

| S3 (familiarity) | Accuracy | n (items) |
|---|---|---|
| Never worked with them | 82.1% | 84 |
| Seen occasionally | 86.7% | 60 |
| Work with them from time to time | 96.7% | 30 |

This is a **clean, monotonic relationship** — accuracy rises step by step with self-reported familiarity — the most orderly demographic pattern in the whole dataset, and the expected direction (more exposure to real vulnerability records predicts better comprehension of a vulnerability record, independent of presentation format).

By condition, the pattern is more textured and directly relevant to the thesis's target population:

| S3 | NVD | Summary | Gap |
|---|---|---|---|
| Never worked with them | 78.6% | 85.7% | **+7.1pp** |
| Seen occasionally | 86.7% | 86.7% | 0pp |
| Work with them from time to time | 93.3% | 100% | +6.7pp |

The largest NVD-vs-Summary benefit appears in the **least-familiar group** (n=7) — the respondents closest to the thesis's actual target population ("technical non-security personnel" who do not work with CVE data regularly, per `CLAUDE.md`). The middle group shows no gap between conditions at all. This is a genuinely useful shape for the thesis's argument — the summary appears to help most where it is meant to help — but at n=7 in the driving cell, it is one atypical respondent away from disappearing, and should be reported as a suggestive pattern, not a result.

Likert does **not** follow the same shape, and this divergence is itself worth stating rather than smoothing over: clarity/confidence peak in the *middle* familiarity group (4.30 clarity / 4.25 confidence) and are lowest in the *most*-familiar group (3.60 / 3.40) — the group that scored best (96.7%) rated the entries least favourably on clarity and confidence. Self-reported ease of an entry does not track demonstrated comprehension cleanly in this data; both should be reported, and neither should stand in for the other. (Plausible reading, offered as interpretation only: the most-familiar respondents may be applying a higher bar when rating "clear and easy to understand," rather than actually understanding less — but at n=3 this is speculation, not something the data can confirm.)

---

## 9. Addendum — breakdowns by CVE, block, and quad (CVE set)

_Added after the initial version of this document, in response to a follow-up question. Technical-background sample only (n=15, per §3.1), sourced from `analyze_human_study.py`'s printed output._

### 9.1 By individual CVE (both conditions combined)

| CVE | Accuracy | n (items) |
|---|---|---|
| CVE-2023-44221 (SonicWall SMA100) | **60.0%** | 15 |
| CVE-2021-21974 (VMware ESXi / OpenSLP) | 72.2% | 18 |
| CVE-2023-43661 (Cachet) | 75.0% | 12 |
| CVE-2020-8010 (CA Unified Infrastructure Management) | 83.3% | 18 |
| CVE-2021-22204 (ExifTool) | 86.7% | 15 |
| CVE-2022-3062 (WordPress Simple File List) | 88.9% | 18 |
| CVE-2023-21608 (Adobe Acrobat Reader) | 88.9% | 18 |
| CVE-2021-42013 (Apache HTTP Server) | 93.3% | 15 |
| CVE-2021-30970 (macOS Privacy bypass) | 100% | 9 |
| CVE-2022-40765 (Mitel MiVoice Connect) | 100% | 15 |
| CVE-2023-29119 (Waybox Enel X) | 100% | 12 |
| CVE-2024-21887 (Ivanti Connect Secure / Policy Secure) | 100% | 9 |

The two worst-performing items are exactly the two already flagged in §4.4 as content-validity problems, independent of condition: CVE-2023-44221 (the "no fixed version named" vs. "all versions affected, no upper bound" distractor confusion) and, one tier up, the run of items around CVE-2020-8010 ("robot (controller) component" jargon). This is confirmatory, not new — both items score poorly in *both* the NVD and Summary presentation, so the low accuracy is an item-difficulty effect, not something either presentation format caused or fixed.

### 9.2 By block (A–F) — included for completeness, but should not be read as a content-difficulty finding

| Block | Accuracy | n (items) | n (respondents) |
|---|---|---|---|
| A | 77.8% | 36 | 3 |
| D | 83.3% | 18 | 2 |
| E | 83.3% | 24 | 2 |
| F | 86.1% | 36 | 3 |
| B | 88.9% | 36 | 3 |
| C | 100% | 24 | 2 |

At 2–3 respondents per block, this ranking is dominated by *who* happened to be randomly assigned to each block, not the block's content. Block C's perfect score is just its two respondents (`R_87Bi1GGOuqsGWRz`, `R_50xbc0ffVBVZgV7`) each independently scoring 100% regardless of block (§4.3). Block A's low score is the rushed 117-second outlier (`R_3dWEiMCm5OvAjyG`, 41.7% — already flagged in §4.3) dragging down its two otherwise-strong blockmates (91.7%, 100%). **This table is reported for transparency and audit, not as evidence about block content** — §9.3 gives the more trustworthy version of this cut.

### 9.3 By quad (the CVE set — pools both counterbalance letters, 2× the n of §9.2)

Merging each block pair (A+B, C+D, E+F) removes the single-respondent noise in §9.2 and gives a genuine per-CVE-set comparison:

| Quad | CVEs | Accuracy | NVD | Summary | Gap |
|---|---|---|---|---|---|
| Quad 2 (C/D) | Waybox, Cachet, macOS, Ivanti | **92.9%** | 85.7% | **100%** | **+14.3pp** |
| Quad 3 (E/F) | Apache, SonicWall, ExifTool, Mitel | 85.0% | 86.7% | 83.3% | −3.3pp (reversed) |
| Quad 1 (A/B) | CA UIM, ESXi, WordPress, Adobe | 83.3% | 80.6% | 86.1% | +5.5pp |

Quad 2 is the standout: 100% accuracy in the Summary condition and the single largest condition gap anywhere in the study. Quad 3 is the only quad where NVD numerically beats Summary — directly explained by CVE-2023-44221 (§9.1's worst-performing item) sitting in the Summary slot in block E but the NVD slot in block F: a single low-accuracy item is enough to flip an aggregate at this sample size, which is itself a useful illustration of why per-cell conclusions at n=15 need to be read cautiously.

### 9.4 The accuracy/Likert disconnect shows up again here, on an independent cut

| Quad | Accuracy | Clarity | Confidence |
|---|---|---|---|
| Quad 2 (C/D) | **92.9% (best)** | 3.64 (lowest) | 3.43 (lowest) |
| Quad 3 (E/F) | 85.0% (middle) | **4.30 (highest)** | **4.40 (highest)** |
| Quad 1 (A/B) | 83.3% (lowest) | 3.79 | 3.88 |

The quad with the best measured comprehension (Quad 2) has the *worst* self-reported clarity and confidence, and vice versa for Quad 3. This is the same pattern already noted at the CVE level (CVE-2023-21608, §5) and the familiarity-subgroup level (§8.2, the most-familiar respondents scored best but rated clarity/confidence lowest) — a third independent cut showing the same disconnect is enough to treat it as a real feature of this dataset rather than a one-off: **self-reported ease of an entry and demonstrated comprehension of it are measuring different things here, and neither should be read as a proxy for the other.**

---

## 11. Addendum — response-pattern findings (calibration, order, consistency, distractors)

_Added 2026-08-11, in response to a follow-up question asking what else in the response data (beyond demographics) hadn't been surfaced yet. Technical-background sample only (n=15, per §3.1's exclusion); sourced from `analyze_human_study.py`'s printed output._

### 11.1 NVD readers are miscalibrated more often than Summary readers

Defining "overconfident" as an entry rated Agree/Strongly agree on the confidence Likert item while at least one of its 3 comprehension questions was answered wrong:

| Condition | Overconfident entries | Rate |
|---|---|---|
| NVD | 9 of 29 | **31.0%** |
| Summary | 4 of 29 | **13.8%** |

**Not a training effect.** S2 (formal training) shows essentially no difference: 22.7% overconfident for untrained respondents vs. 21.4% for trained. Training does not predict who gets confidently wrong.

**A non-monotonic familiarity effect (S3), not a simple "less familiar = more overconfident" pattern:**

| S3 | Overconfidence rate |
|---|---|
| Never worked with them | 21.4% |
| Seen occasionally | **35.0% (highest)** |
| Work with them from time to time | **0.0%** |

The most-familiar respondents have zero overconfident entries — expected. But the middle group ("seen occasionally") is *more* overconfident than the least-familiar group, not less — a shape consistent with partial, unreliable familiarity producing false confidence more than either no exposure or real experience does. Splitting this by condition sharpens it: for the least-familiar group, format matters enormously (NVD 35.7% vs. Summary 7.1% overconfident) — the plain-language summary specifically protects genuine novices from false confidence. For the "seen occasionally" group, format barely matters (NVD 40.0% vs. Summary 30.0%, both already high) — partial familiarity appears to produce overconfidence regardless of how the text is presented. Cell sizes here are small (n=3–7 respondents per S3 group) and this should be read as directional, not a powered result.

**Concentrated in specific people and specific items more than in any demographic group.** Three of the 15 respondents (`R_28BpNaOAXOVFUBu`, `R_25L2ocH4GqwynxW`, `R_5UHaJ323aSKYjJv`) account for 7 of the 13 overconfident entries — over half, from a fifth of the sample. At the item level, overconfidence tracks the items already flagged as weak in §4.4: CVE-2023-44221 is answered confidently-but-wrong in 4 of 5 exposures (80%, the highest rate of any item in the study), followed by the "12.24" item (CVE-2021-22204, 40%). The overall NVD-vs-Summary overconfidence gap is real, but it is substantially explained by a handful of problem items and a handful of individuals rather than being evenly spread across the sample.

Underconfident entries (all 3 correct but confidence rated ≤2) are rare in both conditions (NVD 2/29, Summary 0/29) and not treated as a finding given the small counts. The overconfidence gap is a different claim from the accuracy gap in §4.1: it says NVD readers are not just less accurate, they are also more than twice as likely to feel sure of themselves while actually wrong about part of an entry. That is directly relevant to the thesis's risk-communication framing — a comprehension failure a reader doesn't recognise as a failure is a worse outcome than one they're unsure about.

### 11.2 The apparent "slot 2" accuracy dip is item difficulty, not fatigue

Accuracy by position in the 4-CVE sequence within a block:

| Slot (order seen) | Accuracy |
|---|---|
| 1st | 91.1% |
| 2nd | **68.9%** |
| 3rd | 90.5% |
| 4th | 95.2% |

This looks like a fatigue effect until checked against §9.1: the CVE occupying slot 2 in every one of the three quads (CVE-2021-21974, CVE-2023-43661, CVE-2023-44221) is that quad's single worst-performing item — CVE-2023-44221 is the worst item in the entire study (§4.4, §9.1). Slot position and item difficulty are fully confounded by how the quads happen to be ordered. The dip also does not fit a fatigue story on its own terms: slot 4, the *last* CVE seen, has the *highest* accuracy (95.2%), not the lowest. Likert clarity/confidence dip slightly at slot 2 too (3.67 / 3.80 vs. ~3.9–4.2 elsewhere) — consistent with the item-difficulty explanation rather than contradicting it. **This should be reported as an instrument-ordering artefact, not an order/fatigue effect**, and is a useful caution against reading position effects out of a between-subjects design where item and position are confounded by construction.

### 11.3 Within-person consistency: NVD accuracy and Summary accuracy are only loosely related

Each respondent answered 2 entries under each condition. Correlating each person's own NVD-entries accuracy against their own Summary-entries accuracy:

- Pearson r = 0.485, Spearman r = 0.290 (n=15; too small to treat as a stable estimate, direction only)
- 6 of 15 respondents scored better on Summary than NVD, 2 scored better on NVD, 7 tied

The moderate positive correlation suggests part of the variance is a general-comprehension-ability effect (careful readers do reasonably in both formats), but it is far from 1.0, leaving room for a genuine condition effect on top of it. The 6:2 split among non-tied respondents is directionally consistent with the aggregate Summary advantage in §4.1 and shows that advantage is not an artefact of one or two individuals — most people who showed *any* difference between conditions showed it in the same direction as the aggregate.

### 11.4 Two already-flagged weak items show near-total distractor clustering, not scattered guessing

For every wrong answer given to CVE-2021-21974 Q3 and CVE-2023-44221 Q3 (the two items already flagged as content-validity problems in §4.4), the wrong answer is the *same* wrong option, every single time:

| Item | Wrong answers | All converge on |
|---|---|---|
| CVE-2021-21974 Q3 (NVD, 2-distractor item) | 2 of 2 | "No fixed build is available and the service must be disabled permanently" |
| CVE-2023-44221 Q3, NVD | 2 of 2 | "All firmware versions ever released are affected with no upper bound" |
| CVE-2023-44221 Q3, Summary | 2 of 2 | "All firmware versions ever released are affected with no upper bound" |

For CVE-2023-44221 Q3 (a 4-option item, 3 distractors), all 4 wrong answers across *both* conditions pick the identical distractor — under random guessing among 3 distractors, 4 independent people converging on the same one is unlikely by chance (~1 in 27). This is corroborating evidence, independent of the eyeballed reasoning already in §4.4, that these items are pulling readers toward one specific, plausible-sounding wrong answer rather than producing noise — i.e. a genuine item-design flaw (the stimulus text under-specifies remediation/version information in a way both formats share) rather than participants guessing randomly on a hard-but-fair item. No other item in the dataset has ≥2 wrong answers to compare, so this pattern is currently only checkable for these two items.

---

## 12. File checklist

- `data/human_study/survey_source.txt` — ground truth for stimulus text and condition assignment
- `data/human_study/answer_key.txt` — supplied key (verified, zero discrepancies against source)
- `data/human_study/answer_key_check.csv` — the verification itself, item by item
- `data/human_study/qualtrics_export_recorded.csv`, `qualtrics_export_inprogress.csv` — raw data (17 + 7 responses)
- `data/human_study/response_summary.csv` — one row per response, unfiltered, data-quality flags included
- `data/human_study/comprehension_long.csv` — one row per (response, CVE, question), scored, unfiltered (join against `response_summary.csv` to apply the §3.1 exclusion)
- `data/human_study/likert_long.csv` — one row per (response, CVE), clarity + confidence, unfiltered
- `src/analyze_human_study.py` — regenerates all of the above from the raw inputs, applies the §3.1 and §3.2 exclusions to its printed aggregates, and prints the §8 S2/S3 demographic breakdowns, the §9 CVE/block/quad breakdowns, and the §11 calibration/slot/consistency/distractor breakdowns
