# Faithfulness Sensitivity Check: Description-Only vs. Description+CVSS Reference

This file reports evidence, not a verdict. Descriptive statistics and paired Cohen's d effect sizes only, exploratory and small-N (n=24 eval CVEs). Judge model `gpt-4.1-2025-04-14`, temperature 0, 3 passes per text. Extended-reference scores are new (this run); description-only scores are Stage 6e's original results, reused unchanged from `v2_bullet/judge/llm_judge_per_text.csv`. See METHODOLOGY_LOG.md "Stage 6f" for the full rationale on which fields were added to the reference and why KEV/EPSS were deliberately excluded.

## Descriptive statistics

| Arm / reference | N | Mean | Median | SD | Min | Max |
|---|---|---|---|---|---|---|
| persona -- faithfulness (description only) | 24 | 3.181 | 3.000 | 0.481 | 3.000 | 5.000 |
| persona -- faithfulness (description + CVSS) | 24 | 3.819 | 4.000 | 0.786 | 3.000 | 5.000 |
| baseline -- faithfulness (description only) | 24 | 3.042 | 3.000 | 0.266 | 2.667 | 4.000 |
| baseline -- faithfulness (description + CVSS) | 24 | 3.681 | 3.500 | 0.758 | 3.000 | 5.000 |
| nvd -- faithfulness (description only) | 24 | 5.000 | 5.000 | 0.000 | 5.000 | 5.000 |
| nvd -- faithfulness (description + CVSS) | 24 | 5.000 | 5.000 | 0.000 | 5.000 | 5.000 |

## Paired comparison: extended reference vs. original (description-only) reference

Matched by CVE, n=24 pairs, per arm. A positive mean diff means the extended reference scored higher.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) |
|---|---|---|---|---|---|
| persona extended - persona original | 24 | 0.639 | 0.500 | 0.722 | 0.885 |
| baseline extended - baseline original | 24 | 0.639 | 0.333 | 0.728 | 0.877 |
| nvd extended - nvd original | 24 | 0.000 | 0.000 | 0.000 | n/a |

## Figures

See `v2_bullet/figures/` for PNG (300 dpi) and SVG versions.

- `llm_judge_faithfulness_ext_bullet` -- faithfulness scores under the extended reference, by text
- `llm_judge_faithfulness_original_vs_ext_bullet` -- per-CVE paired change, description-only to description+CVSS reference, persona and baseline
