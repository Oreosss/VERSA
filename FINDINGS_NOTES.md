# Findings Notes: Automated Evaluation Metrics

**Status:** interpretive draft, written to feed the dissertation findings chapter. Unlike `PROMPT_COMPARISON.md` (evidence only, no interpretation, by design), this file draws conclusions and flags what they might mean. Treat it as a first pass to edit, not text to paste in unchanged -- check the framing against your own reading of the literature and the rest of the study before it goes in the chapter.

**Source of truth:** all numbers below are computed by `src/compute_metrics.py` from `summaries.json` (48 generations) and `data/eval_sample.jsonl` (24 raw NVD descriptions), and are reproducible from `metrics_per_summary.csv`. If the metrics are ever recomputed, re-derive the numbers in this file rather than hand-editing them out of sync. A few figures here (word counts, win rates, correlations, sign counts, worked examples) were computed for this note specifically and are not in `PROMPT_COMPARISON.md` or `metrics_per_summary.csv` -- the code for each is inline below its finding so it can be re-run.

**Design recap:** 24 eval CVEs, 2 prompt arms (persona, baseline), same 24 CVEs in both arms (paired), one model (`claude-opus-4-6`), temperature 0, single generation per (CVE, arm) pair. Reference text for all three text-comparison metrics is the raw NVD `description`. n=24 throughout -- small-N and exploratory, so effect sizes and directional consistency (how many of the 24 CVEs agree on a direction) are weighted more heavily below than p-values.

---

## 1. Readability (Flesch-Kincaid): the central comparison, and the headline finding

The core research question is whether the tool improves comprehension relative to raw NVD descriptions. Flesch-Kincaid (FK) is the automated proxy for that on the readability axis, and it does not show an improvement.

**On average, both arms are slightly harder to read than the NVD description they summarise, not easier.**

| | Mean FK | Median FK | SD |
|---|---|---|---|
| Raw NVD description | 12.34 | 12.07 | 5.23 |
| Persona summary | 13.13 | 12.97 | 1.39 |
| Baseline summary | 13.50 | 13.30 | 1.75 |

Paired difference (summary minus NVD, per CVE): persona +0.78 grades (d=0.19, Wilcoxon p=0.20), baseline +1.16 grades (d=0.31, Wilcoxon p=0.10). Both effects are small and neither paired test clears significance at n=24, so read this as "no detectable average improvement," not as "reliably worse" -- but the direction is consistently against the improvement hypothesis, not for it.

**Only a minority of individual CVEs actually got easier.** Counting per CVE whether the summary's FK grade came in below the NVD description's FK grade:

```python
for arm in ['persona','baseline']:
    sub = df[df.arm==arm]
    wins = (sub.fk_grade_summary < sub.fk_grade_nvd).sum()
    print(arm, f'{wins}/24 easier than NVD')
```
- Persona: **8/24 (33%)** of summaries were easier to read than the NVD description they replaced.
- Baseline: **7/24 (29%)**.

So roughly two-thirds to three-quarters of the time, the summary is a harder read than the thing it is meant to make easier to understand, on this metric.

**The one clear pattern: source complexity predicts outcome, and it predicts it strongly.** Summary FK correlates with NVD FK at r=0.83 (persona) and r=0.89 (baseline), both p<0.001. Put together with the win-rate numbers, this splits into two regimes rather than a single trend:

- **When the source description is already dense and jargon-heavy, the summary helps.** The clearest case is CVE-2023-44221 (SonicWall SMA100 command injection, KEV-listed): the NVD description is a single 41-word sentence ("Improper neutralization of special elements in the SMA100 SSL-VPN management interface allows a remote authenticated attacker with administrative privilege to inject arbitrary commands...") scoring FK 25.8, the hardest in the sample. Both summaries cut that roughly in half (persona FK 15.3, baseline FK 17.8), the two largest readability improvements in the dataset. CVE-2024-3400 (Palo Alto GlobalProtect) shows the same pattern (NVD FK 20.6, summaries down to 14.9-15.2).
- **When the source description is already short and plain, the summary makes it worse.** CVE-2023-50919 (GL.iNet NGINX auth bypass) is the sharpest example: the NVD description scores FK 2.4 (very easy), largely because it is a short sentence padded with a long list of terse device model numbers, which the FK formula reads as short, simple tokens. Both summaries expand this into full explanatory prose across three sections and land at FK 9.4-11.1, the two largest regressions in the dataset. CVE-2020-8958 and CVE-2023-43661 show the same pattern at a smaller scale.

This is a genuinely useful finding for the chapter, but it needs the FK caveat attached every time it is stated: FK measures sentence and word length only, not clarity, so "FK went up" for CVE-2023-50919 could mean the explanation genuinely got more elaborate (arguably appropriate for a critical auth-bypass vulnerability that a one-line description under-explains), not that it got less clear. The CVE-2023-50919 case is worth using directly as a worked example of this limitation in the chapter, since it is a real instance from your own data of FK penalising something that is plausibly a legitimate elaboration rather than a readability failure.

**Practical implication worth stating explicitly:** if FK-vs-NVD is going to be reported as a headline automated result, the honest framing is "the tool's benefit on this metric is concentrated in already-complex source material, and it adds length-driven complexity when the source is already terse" rather than "the tool improves readability." The human evaluation stage (questionnaire, LLM-as-judge) is where the actual comprehension claim needs to be established, since FK cannot carry it alone, and your own methodology write-up already says so.

---

## 2. Semantic faithfulness (BERTScore): both arms stay grounded, baseline slightly more so

| | Precision | Recall | F1 |
|---|---|---|---|
| Persona | 0.809 | 0.902 | 0.853 |
| Baseline | 0.817 | 0.906 | 0.859 |

Both arms sit in a high, tight band (F1 SD ~0.01 either arm), which supports a faithfulness argument: neither prompt is producing summaries that drift semantically far from the source CVE. Per the favourable-direction framing already fixed in `METHODOLOGY_LOG.md`, this is evidence of grounding, not a score to maximise -- a summary near 1.0 would mean it barely transformed the source, which is not the goal.

Baseline scores fractionally but consistently higher than persona on all three BERTScore components (F1 diff -0.006, d=-0.85, Wilcoxon p<0.0001; precision diff -0.008, d=-1.16, p<0.0001; recall diff -0.005, d=-0.45, p=0.01). Directional consistency: baseline beats persona on precision in 21/24 CVEs, recall in 18/24, F1 in 21/24. These are the tightest, most consistently one-directional results in the whole analysis, so this is the one place where "baseline sits closer to the source than persona" is on fairly solid statistical footing for a study this size, even accounting for the small N.

**Precision is consistently well below recall in both arms, and this looks like a length effect, not a faithfulness problem.** Recall minus precision: persona +0.093 (SD 0.013), baseline +0.089 (SD 0.013), both essentially universal across the sample (paired t-test recall vs precision, both arms p<1e-20). BERTScore recall asks "is the reference (NVD) well covered by the summary," and precision asks "is everything in the summary well supported by the reference." Since the three-part summaries are much longer than the NVD description they are built from (see Section 4), they necessarily contain a lot of elaboration, remediation advice, and framing language that has no counterpart in the terse NVD text to match against -- that drags precision down mechanically, independent of whether the added content is accurate. This is worth stating explicitly in the chapter so a reader does not misread the precision gap as evidence of unsupported or fabricated content: it is at least partly, and plausibly mostly, a length artefact of the three-part structure rather than a hallucination signal. This is exactly the kind of claim BERTScore cannot adjudicate on its own (documented as a limitation already), and is a good motivating example for why LLM-as-judge or human review is still needed to check specific factual claims.

---

## 3. Lexical overlap (ROUGE): low as expected, and baseline is consistently closer to NVD's wording

| | ROUGE-1 | ROUGE-2 | ROUGE-L |
|---|---|---|---|
| Persona | 0.195 | 0.104 | 0.138 |
| Baseline | 0.221 | 0.123 | 0.158 |

Both arms are low, consistent with the study's stated expectation: the summaries deliberately rephrase NVD into plainer language, so low overlap is the intended outcome, not a failure. Combined with the high BERTScore numbers above, low ROUGE plus high BERTScore is the intended signature of faithful rephrasing (meaning preserved, wording changed), and that pattern holds for both arms here.

Baseline scores higher than persona on all three ROUGE variants, with the largest and most consistent effect in the whole analysis: ROUGE-1 diff -0.026 (d=-0.94), and persona scores lower than baseline in **23 of 24 CVEs**. ROUGE-2 (20/24) and ROUGE-L (19/24, 1 tie) show the same direction slightly less uniformly. This says persona's wording departs further from NVD's original phrasing than baseline's does, on top of persona also scoring slightly lower on BERTScore -- i.e. persona is not just using different words for the same content (which would be low ROUGE, high BERTScore, unchanged from baseline), it is producing text that is measurably further from the source on both axes at once, even if only by a small margin on the semantic side.

---

## 4. A confound worth naming directly: persona summaries are substantially longer

```python
persona mean words: 356.8 (SD 49.8, median 348.5)
baseline mean words: 316.0 (SD 38.9, median 312.5)
NVD description mean words: 42.4
```

Persona summaries run about 41 words longer than baseline on average, and are longer in 23 of 24 CVEs. Both summary types are roughly 7.5-8.5x the length of the raw NVD description they are built from, which is itself worth a line in the chapter (the "summary" is a substantial expansion of the source, not a compression -- consistent with the three-part structure adding explanatory framing NVD does not provide, but worth being explicit that "summary" here means "restructured and elaborated," not "shortened").

This length gap plausibly explains, at least in part, several of the results above rather than sitting as an independent finding:
- Persona's lower ROUGE and BERTScore precision relative to baseline (more added text = proportionally less of the summary matches the short reference).
- Persona's slightly higher FK grade level relative to baseline on the CVEs where both increase (longer sentences and more elaboration tend to push FK up).

This does not undo the findings above, but it changes what they should be read as evidence of. The persona-vs-baseline differences in Sections 2 and 3 are more safely described as "the persona prompt produces longer, more elaborated output that sits a little further from NVD's exact wording and content" than as "the persona prompt is less faithful" -- the latter is not supported without controlling for length, which this study has not done. If prompt-length parity matters for the dissertation's claims about the persona prompt specifically, that is a design question for a future iteration (e.g. an explicit length cap in both prompts), not something the current data can settle.

---

## 5. What these results can and cannot support in the findings chapter

**Can support:**
- Both prompt arms produce summaries that are semantically grounded in the source NVD description (high, tight BERTScore) while substantially rewording it (low ROUGE) -- the intended rephrasing signature.
- Automated readability (FK) shows no average improvement over raw NVD, and actually gets slightly worse on average, with the effect concentrated by source complexity (helps on dense sources, hurts on already-terse ones).
- Baseline and persona are measurably different in output: baseline stays lexically and semantically closer to NVD; persona is longer and departs further from NVD on both axes.

**Cannot support on this evidence alone:**
- Any claim that either prompt arm "understands" better or produces a more useful summary for a human reader -- none of these three metrics measure comprehension, logical clarity, or correctness of the technical content. This is explicitly why the questionnaire and LLM-as-judge stages exist, and the FK result in particular is a good place in the chapter to motivate why automated readability is not sufficient on its own.
- Any claim that persona summaries are less faithful or more prone to fabrication -- the precision/ROUGE gap is confounded with length, and BERTScore is not a hallucination detector regardless.
- Any population-level claim ("summaries are harder to read than NVD" as a general fact about the tool) -- n=24, no correction for multiple comparisons, one model at temperature 0 with a single generation per condition (no sampling variance captured). Effect sizes and directional consistency (23/24, 21/24, etc.) are more defensible than the p-values here, and that is the framing used throughout this note.

**Open questions worth carrying into the next evaluation stages:**
- Does the CVE-2023-50919-style FK regression (terse source, elaborated summary) actually read as clearer or more complete to a human, despite scoring worse on FK? This is directly testable in the questionnaire and would validate or undercut the reading in Section 1.
- Is persona's greater distance from NVD's wording (Sections 2-3) adding useful interpretive framing, or introducing drift? LLM-as-judge, or a targeted claim-support check against the source CVE, could distinguish these where BERTScore cannot.
- Would controlling for output length change the persona-vs-baseline comparison in Sections 2-3? Not answerable from the current data, but worth flagging as a limitation if the dissertation draws any persona-vs-baseline conclusion from these metrics.

---

## 6. Reproducing or extending these numbers

The headline tables (descriptive stats, paired diffs, effect sizes) are already in `PROMPT_COMPARISON.md` and `metrics_per_summary.csv`/`.json`. The additional analyses in this note (word counts, FK win rate, per-metric sign counts, source-complexity correlation, BERTScore precision/recall gap significance, the worked examples in Section 1) were computed directly from `metrics_per_summary.csv` plus `extract_summary_text()` from `src/compute_metrics.py`, and are not persisted anywhere as code -- if they need to be re-run after a metrics recomputation, the pandas/scipy snippets are inline above each finding.

---

## 7. Flesch-Kincaid limitation and why readability results must be interpreted with care

Flesch-Kincaid measures only sentence length and syllables per word. It has no access to meaning, to structure, or to word familiarity. It cannot tell whether a sentence is well organised, whether a term is explained, or whether a reader already knows the vocabulary being used. It is a proxy for surface complexity, not for comprehension.

This matters directly for the readability result in Section 1. The summaries in this study are intended to improve comprehension largely by adding explanation, defining terms inline, and unpacking what a CVSS field or an attack vector value actually implies for the reader. That kind of explanatory expansion necessarily increases word count and sentence length relative to the terse NVD source, which is exactly what Flesch-Kincaid penalises. A summary can therefore be scored as harder to read by Flesch-Kincaid at the same time as it becomes genuinely easier for a human reader to understand, because the metric is measuring the cost of the explanation rather than its value. Flesch-Kincaid consequently penalises the very transformation that produces the intended comprehension gain. A near-null or slightly higher Flesch-Kincaid grade level for the summaries, as found in Section 1, is therefore consistent with a genuine comprehension improvement that the metric is structurally unable to detect, and it is equally consistent with no improvement at all. Flesch-Kincaid alone cannot distinguish these two possibilities. This is the reason Flesch-Kincaid cannot alone address this study's research question, and it is why the human user study, not any automated readability score, is the decisive measure of comprehension for this thesis.

Dale-Chall was added to this evaluation as a complementary readability proxy for exactly this reason. Rather than scoring length, it checks each word against a list of vocabulary familiar to most readers and penalises the proportion of words that fall outside that list. It therefore targets word familiarity rather than word length, which is a closer proxy for the jargon barrier this study is actually concerned with. A term such as "authentication" is short and scores as easy under Flesch-Kincaid, despite being unfamiliar to a non-security reader, whereas Dale-Chall is built to flag exactly that kind of term as difficult regardless of its length.

**What the Dale-Chall results show, relative to Flesch-Kincaid, once computed.** The two metrics point in opposite directions. Where Flesch-Kincaid found summaries slightly harder than NVD on average (Section 1), Dale-Chall finds summaries consistently and substantially easier than NVD. Mean Dale-Chall score falls from 13.65 for the raw NVD description to 11.78 for persona summaries and 12.09 for baseline summaries. The paired difference against NVD is large by conventional benchmarks for both arms (persona mean difference -1.87, d=-1.28, Wilcoxon p<0.0001, baseline mean difference -1.56, d=-1.06, Wilcoxon p<0.0001), and the direction is close to universal across the sample rather than driven by a few CVEs, with 22 of 24 persona summaries and 21 of 24 baseline summaries scoring easier than their NVD source on Dale-Chall.

The clearest illustration is CVE-2023-50919, already flagged in Section 1 as the sharpest Flesch-Kincaid regression in the whole dataset. There, the NVD description scores an easy 2.4 on Flesch-Kincaid, largely an artefact of a short sentence padded with terse device model numbers, and the summaries expand it into full explanatory prose, driving Flesch-Kincaid up to 9.4 and 11.1. On Dale-Chall, the same CVE tells a different story. The NVD description scores 16.3, one of the least familiar-vocabulary sources in the sample, and both summaries bring that down to 12.5 to 12.8, in line with the rest of the sample rather than standing out as harder. Read together, the two metrics support the reading proposed in Section 1 directly. The apparent Flesch-Kincaid regression on this CVE is consistent with the summary replacing unfamiliar, jargon-heavy source material with more familiar vocabulary, at the cost of additional length, which is exactly the trade a genuine explanatory improvement would make and exactly the trade Flesch-Kincaid is unable to credit.

This pattern is not confined to that one case. Across the CVEs where Flesch-Kincaid recorded the summary as harder than NVD, Dale-Chall still recorded an improvement in most of them (14 of 16 for persona, 14 of 17 for baseline). Taken together with the descriptive result above, this is the strongest automated evidence in this evaluation for a genuine jargon-reduction effect operating underneath a flat or slightly negative Flesch-Kincaid result, and it directly supports treating the Flesch-Kincaid finding in Section 1 as inconclusive on comprehension rather than as evidence against it. It remains automated evidence rather than a comprehension finding in its own right, since Dale-Chall's familiar-word list was built for general English and does not know that a security term is correctly and necessarily used rather than merely unfamiliar, and it can equally over-penalise or under-penalise specific vendor names, product names, and CVE identifiers. The questionnaire and LLM-as-judge stages remain the tests that can actually confirm whether this vocabulary simplification is experienced as a comprehension gain by a human reader.

**The CVEs where Dale-Chall disagreed with the improvement direction.** The near-universal pattern above is not exceptionless. In 2 of 24 persona summaries and 3 of 24 baseline summaries, the summary scored equal to or higher (harder, less familiar vocabulary) than its NVD source on Dale-Chall.

| CVE | Arm | NVD Dale-Chall | Summary Dale-Chall | Change |
|---|---|---|---|---|
| CVE-2024-1781 | Persona | 10.30 | 11.42 | +1.12 |
| CVE-2024-1781 | Baseline | 10.30 | 11.78 | +1.48 |
| CVE-2021-42013 | Persona | 11.51 | 11.71 | +0.20 |
| CVE-2021-42013 | Baseline | 11.51 | 11.95 | +0.43 |
| CVE-2022-3062 | Baseline | 11.07 | 11.44 | +0.37 |

Three facts about this set are directly verifiable from the computed data. First, CVE-2024-1781, CVE-2022-3062, and CVE-2021-42013 are, in that order, the three lowest raw NVD Dale-Chall scores of all 24 eval CVEs (sample minimum 10.30, second-lowest 11.07, third-lowest 11.51), meaning the disagreement is concentrated entirely on the CVEs whose source description already used the most familiar vocabulary in the sample, consistent with the same already-simple-source pattern documented for Flesch-Kincaid in Section 1. Second, CVE-2024-1781 and CVE-2021-42013 disagree in both prompt arms, while CVE-2022-3062 disagrees only in the baseline arm. Its persona summary moved in the favourable direction on Dale-Chall (11.07 to 10.89), so this CVE is not a case where both arms failed in the same way. Third, on this same CVE, CVE-2022-3062 persona, Flesch-Kincaid and Dale-Chall disagree with each other on the identical summary text, Flesch-Kincaid recorded it as harder than NVD (9.42 to 12.23) while Dale-Chall recorded it as easier (11.07 to 10.89), which is a direct instance, within a single generation, of the two metrics measuring different things rather than merely tracking each other imperfectly.

One additional fact is worth recording without drawing a conclusion from it. CVE-2022-3062 baseline is the same record noted elsewhere in this project as using `**bold**` section headers in its raw output text rather than the `##` markdown headers every other summary uses (see `src/compute_metrics.py`, `extract_summary_text`). The text-extraction step already normalises both header styles identically before any metric is computed, and the other four disagreement rows in the table above show the same direction of effect with standard `##` headers, so the header formatting difference is very unlikely to be the explanation for this CVE's Dale-Chall result. It is noted here only because it is independently verifiable from the project's own data, not because the current evidence supports a causal link between the two.

**What the disagreement cases mean for the readability claim.** Dale-Chall improved for the large majority of the sample, in 22 of 24 cases for the persona arm and 21 of 24 cases for the baseline arm. The small number of cases that ran against this trend were examined individually rather than dismissed as noise, since a pattern that explains three exceptions is more useful to the thesis than a footnote acknowledging they exist.

Two CVEs disagreed in both prompt arms, CVE-2024-1781 and CVE-2021-42013. A third, CVE-2022-3062, disagreed only in the baseline arm, where the persona summary for the same CVE moved in the favourable direction.

The two CVEs that disagreed in both arms are not a random pair. They are among the lowest, meaning easiest, NVD Dale-Chall scores anywhere in the 24-CVE sample, and CVE-2024-1781 is the single easiest source description in the entire sample. This points to a specific mechanism rather than an unexplained failure. Where the source description is already written in accessible language, there is very little unfamiliar vocabulary left for the summary to remove. The explanatory scaffolding the summaries add regardless, such as inline definitions and the unpacking of what a CVSS field like attack vector or privileges required actually implies for the reader, introduces vocabulary of its own. When the source is already simple, that added vocabulary has no corresponding jargon reduction to offset it, so the transformation costs more in new terminology than it recovers in simplification.

This is not a Dale-Chall artefact on its own. The same already-simple-source pattern was independently documented for Flesch-Kincaid earlier in this section, in the discussion of CVE-2023-50919 and the cases like it. Flesch-Kincaid and Dale-Chall measure different underlying properties of a text, sentence and word length in one case and vocabulary familiarity in the other, and their agreement on the same subset of already-easy sources is stronger evidence for the pattern than either metric could offer on its own.

Taken together, this establishes a scope condition on the readability claim rather than undermining it. The summaries reduce vocabulary difficulty substantially where the source description is jargon dense, and they offer little or no readability gain, and occasionally a small loss, where the source is already accessible. Stating this boundary explicitly strengthens the overall claim rather than weakening it, since a claim that specifies where it does and does not hold is more credible than one presented as unconditional.

CVE-2022-3062 is worth noting briefly and no further. Its persona summary improved on Dale-Chall, from 11.07 to 10.89, while its baseline summary did not, scoring 11.44. This is consistent with the broader pattern already established for ROUGE and BERTScore, that the persona arm's output sits further from the source's original wording than the baseline arm's does. As this is a single case, it is reported here as an observation rather than weighted as a finding in its own right.

Finally, none of these three disagreement cases coincide with the two CVEs flagged as weakly grounded during retrieval validation, CVE-2023-29119 and CVE-2023-43661. Retrieval grounding and readability regression therefore appear to be independent of one another in this sample, which removes a plausible confound between the retrieval validation stage and the readability results reported here.
