# HUMAN_STUDY_DEMOGRAPHICS.md

_Standalone record of everything demographic (`S1`, `S2`, `S3`) from the human comprehension study (Stage 8). Split out from `HUMAN_STUDY_FINDINGS.md` because this material kept growing across follow-up questions and deserved its own home rather than being scattered across that document's addenda. Every number below is read from `src/analyze_human_study.py`'s printed output, not estimated by hand. Created 2026-08-11, after `HUMAN_STUDY_FINDINGS.md` (2026-08-10)._

Cross-references: `HUMAN_STUDY_FINDINGS.md` §3.1 (the S1 exclusion, results in more depth), §8 (S2/S3 vs. comprehension and Likert, results in more depth). This document is the demographic-focused companion — sample composition, classification, and checks that don't fit neatly into a results table.

---

## 1. The instrument

Three demographic questions, asked once per respondent before the four vulnerability entries:

| Field | Question | Options |
|---|---|---|
| `S1` | "Do you have a technical background, for example in software development, IT operations, or computer science?" | Yes / No |
| `S2` | "Have you received any formal training or qualification in cyber security, for example a security degree, module, or professional certification?" | Yes / No |
| `S3` | "How would you describe your familiarity with vulnerability data such as CVE records and CVSS scores?" | 4-point scale: never worked with them / seen occasionally / work with them from time to time / work with them regularly |

These three fields are the entirety of the demographic instrument — no age, role, seniority, or other field was collected. Any breakdown not built from `S1`/`S2`/`S3` (alone or crossed) is not something this dataset can answer.

`S1` directly operationalises the thesis's target-population definition (`CLAUDE.md`: "technical non-security personnel, e.g. software developers, CS students"). `S2` is the closest available proxy for "non-security" specifically. `S3` measures a different thing — direct prior exposure to vulnerability records — which is related to but not the same as security training (someone can be trained without regularly reading CVE records, or vice versa; see §5).

---

## 2. Sample composition

### 2.1 S1 — technical background

| | Full raw pool (24 attempts) | Answered S1 (22) | Reached content (16) |
|---|---|---|---|
| Yes | — | 21 | 15 |
| No | — | 1 | 1 |

One respondent (`R_2V23IjInwIyOO34`) answered "No" and was **excluded from all comprehension/Likert analysis** in `HUMAN_STUDY_FINDINGS.md` as outside the thesis's target population — a scope decision, not a data-quality trim (their raw accuracy, 16.7%, is recorded but not part of any headline figure; see `HUMAN_STUDY_FINDINGS.md` §3.1). All figures in this document from §3 onward use the resulting **n=15 technical-background sample**, matching `HUMAN_STUDY_FINDINGS.md`.

### 2.2 S2 — formal cyber security training (n=15)

| S2 | n |
|---|---|
| No | 11 |
| Yes | 4 |

### 2.3 S3 — CVE/CVSS familiarity (n=15)

| S3 | n |
|---|---|
| Never worked with them | 7 |
| Seen occasionally | 5 |
| Work with them from time to time as part of my role | 3 |
| Work with them regularly | 0 |

No respondent in this sample selected the top familiarity option. The most-familiar subgroup discussed throughout this document and `HUMAN_STUDY_FINDINGS.md` §8.2 is therefore "work with them from time to time," not the survey's actual ceiling option — worth stating explicitly so nobody reads "most familiar group" as "security-data experts."

---

## 3. Technical non-security classification (S1 = Yes, S2 = No)

This is the direct operationalisation of the thesis's target population, and was computed on request rather than being part of the original analysis.

| | Technical-background sample (n=15) | Full raw pool, both fields answered (n=22) |
|---|---|---|
| Technical, no security training ("technical non-security") | **11** | **14** |
| Technical, with security training | 4 | 7 |
| Non-technical, with security training | — (excluded) | 1 |
| Non-technical, no security training | — (excluded) | 0 |

**11 of the 15** respondents in the main analysis sample are technical non-security by this definition — a clear majority, consistent with the study successfully recruiting toward its intended population rather than incidentally sampling security specialists. Three respondents never answered S1/S2 at all (two abandoned "in-progress" attempts and `R_1NrDYHyqpv7gdml`, which stopped at 3% progress right after consent).

---

## 4. S2 (training) vs. comprehension, Likert, and duration

_Full accuracy/Likert tables already in `HUMAN_STUDY_FINDINGS.md` §8.1 — reproduced briefly here for completeness, plus the duration angle which is new._

| S2 | Accuracy | Clarity | Confidence | Median duration |
|---|---|---|---|---|
| No (n=11) | 84.8% | 3.89 | 3.84 | 1777s (~30 min) |
| Yes (n=4) | 90.5% | 4.07 | 4.29 | 878s (~15 min) |

Trained respondents score a little higher, rate both conditions a little higher, and take about half the time (median) of untrained respondents. All three point the same direction, which is at least internally consistent — but every one of them rests on **n=4** trained respondents, and `HUMAN_STUDY_FINDINGS.md` §8.1 already flags the accuracy figure as too thin to trust as a group effect (training doesn't cleanly separate top and bottom individual performers: the rushed-response outlier and 3 of the 4 perfect scorers are all *untrained*). The duration gap is the same caveat — it could easily be 4 people who happen to read quickly, not a training effect.

**Do not use the mean duration for the untrained group** (12,081s) — it is entirely an artefact of one respondent's ~27-hour session (`R_50TZzn6D3lyloNX`, almost certainly a browser tab left open rather than continuous reading; already flagged as a duration outlier without an accuracy anomaly in `HUMAN_STUDY_FINDINGS.md` §3). The median (1777s) is the number to cite.

---

## 5. S3 (familiarity) vs. comprehension, Likert, and duration

_Accuracy/Likert tables already in `HUMAN_STUDY_FINDINGS.md` §8.2 — the duration column below is new._

| S3 | Accuracy | Clarity | Confidence | Median duration |
|---|---|---|---|---|
| Never worked with them (n=7) | 82.1% | 3.79 | 3.93 | 1829s |
| Seen occasionally (n=5) | 86.7% | 4.30 | 4.25 | 1286s |
| Work with them from time to time (n=3) | 96.7% | 3.60 | 3.40 | 733s |

**Median duration decreases monotonically with familiarity**, the same clean step-pattern as the accuracy trend (`HUMAN_STUDY_FINDINGS.md` §8.2) — more-familiar respondents were not only more accurate, they were faster, which is the expected joint signature of genuine familiarity (as opposed to, say, rushing) since accuracy did *not* fall alongside the faster times the way it did for the one confirmed rushed response (§7 below). This is a second independent measure (time) pointing the same direction as the first (accuracy), which strengthens confidence that the S3 trend reflects real familiarity rather than a quirk of these 15 people.

The clarity/confidence figures repeat the disconnect already documented in `HUMAN_STUDY_FINDINGS.md` §8.2 and §9.4: the most-familiar subgroup scores best (96.7%) and reads fastest (median 733s) but rates the entries *least* favourably on clarity and confidence (3.60 / 3.40, the lowest of the three subgroups). Restated here because it recurs across every demographic and content cut this study supports (CVE-level, quad-level, and here) and is treated as a real, load-bearing feature of the dataset — self-reported ease and demonstrated comprehension are measuring different things — not something to average away.

---

## 6. S2 × S3 jointly: explored and found inconclusive

A follow-up question asked whether training and familiarity interact — e.g. do untrained-but-familiar respondents behave differently from trained-but-unfamiliar ones. This was checked and the honest answer is **the data cannot support this cut**.

| | Never worked with them | Seen occasionally | Work with them sometimes |
|---|---|---|---|
| No training | 6 | 3 | 2 |
| Yes training | 1 | 2 | 1 |

Only one joint cell has more than 3 people: **no training + never worked with CVEs (n=6)** — the "purest novice" subgroup. There, accuracy is 80.6% NVD vs. 83.3% Summary (+2.8pp), in the same direction as and roughly consistent with the overall study result — nothing distinctive shows up for this subgroup specifically.

Every other cell is 1–3 respondents. Two cells produce numbers that look dramatic (a +16.7pp condition gap for "trained + never worked with CVEs," a +33.3pp gap for "trained + works with them sometimes") but **both are literally one person's data** — 6 and 3 comprehension items respectively, i.e. one or two CVEs' worth of answers for a single individual. These are not reported as findings anywhere in this document or in `HUMAN_STUDY_FINDINGS.md`, and should not be cited from the raw numbers alone without this context. They are recorded here specifically so this exploration isn't silently repeated and over-read later.

**Conclusion: S2 and S3 do not show an interaction this sample can detect.** The two variables aren't strongly coupled either — most trained respondents also report at least "seen occasionally" (3 of 4), so there isn't a natural "trained-but-unfamiliar" subgroup of any size to compare against a "untrained-but-familiar" one.

---

## 7. The one confirmed data-quality outlier is demographically unremarkable

`R_3dWEiMCm5OvAjyG` (117-second full block, 41.7% accuracy — the clearest outlier in the whole study, per `HUMAN_STUDY_FINDINGS.md` §4.3) is S1=Yes, S2=No, S3="never worked with them" — squarely inside the largest, most typical demographic cell (6 of 15 respondents share this exact profile). The other 5 respondents in that same cell are unremarkable (accuracy 83.3–100%, per `HUMAN_STUDY_FINDINGS.md` §4.3's per-respondent table). **The outlier's low score is not explained by their demographic profile** — five demographically-identical respondents performed normally — which supports the existing read that this was an individual rushed/low-effort response, not a "novices struggle" pattern.

---

## 8. Randomization sanity check: block assignment balance

Not a finding — a check that the six-block random assignment didn't happen to correlate with demographics in a way that would confound the condition comparisons in `HUMAN_STUDY_FINDINGS.md`.

**S2 by block:**

| Block | No training | Yes training |
|---|---|---|
| A | 2 | 1 |
| B | 3 | 0 |
| C | 2 | 0 |
| D | 1 | 1 |
| E | 2 | 0 |
| F | 1 | 2 |

**S3 by block:** every block has at least one "never worked with them" respondent; the more-familiar subgroups are thinly spread across blocks B/C/D/F only (full crosstab reproducible via `analyze_human_study.py`).

At n=2–4 per block this can't be a rigorous balance test, but nothing here looks like a confound severe enough to explain the per-block accuracy spread already flagged as noise in `HUMAN_STUDY_FINDINGS.md` §9.2 (e.g. Block C's 100% isn't a training or familiarity effect — its 2 respondents are one trained and one untrained, one "never" and one "sometimes" familiar; it's just two people who both happened to score well).

---

## 9. File checklist

- `data/human_study/response_summary.csv` — source for every table in this document (join on `s1_technical_background`, `s2_security_training`, `s3_cve_familiarity`, `duration_seconds`, `active_blocks`)
- `data/human_study/comprehension_long.csv`, `likert_long.csv` — merged against the above for the accuracy/Likert-by-demographic tables
- `src/analyze_human_study.py` — prints every number in this document (search for "Technical non-security classification" / "S2 x S3" / "Duration (seconds) by" / "Block assignment balance" in its output)
- `HUMAN_STUDY_FINDINGS.md` — the results document this demographic material supports; §3.1 (exclusion), §8 (S2/S3 vs. results), §9 (CVE/block/quad, including the demographically-unremarkable-outlier point reused in §7 above)
