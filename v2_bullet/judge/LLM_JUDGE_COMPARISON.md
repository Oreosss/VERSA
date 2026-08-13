# LLM-as-Judge Comparison: Comprehension and Faithfulness (v2, bullet format)

This file reports evidence, not a verdict. Descriptive statistics and paired Cohen's d effect sizes only, exploratory and small-N (n=24 eval CVEs). Judge model `gpt-4.1-2025-04-14`, temperature 0, 3 passes per text per dimension. See METHODOLOGY_LOG.md "Stage 6e" for the rubric verbatim, the blinding and multi-pass design, and the pros/limitations of LLM-as-judge as a method.

## Descriptive statistics

Per-arm, per-dimension mean judge score (1-5), computed from each text's mean across 3 passes, n=24.

| Arm / dimension | N | Mean | Median | SD | Min | Max |
|---|---|---|---|---|---|---|
| persona -- comprehension | 24 | 5.000 | 5.000 | 0.000 | 5.000 | 5.000 |
| baseline -- comprehension | 24 | 5.000 | 5.000 | 0.000 | 5.000 | 5.000 |
| nvd -- comprehension | 24 | 4.014 | 4.000 | 0.752 | 3.000 | 5.000 |
| persona -- faithfulness | 24 | 3.181 | 3.000 | 0.481 | 3.000 | 5.000 |
| baseline -- faithfulness | 24 | 3.042 | 3.000 | 0.266 | 2.667 | 4.000 |
| nvd -- faithfulness | 24 | 5.000 | 5.000 | 0.000 | 5.000 | 5.000 |

## Paired comparisons

Matched by CVE, n=24 pairs. Persona vs. NVD, baseline vs. NVD, and persona vs. baseline, for each dimension.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) |
|---|---|---|---|---|---|
| Persona comprehension - NVD comprehension | 24 | 0.986 | 1.000 | 0.752 | 1.312 |
| Baseline comprehension - NVD comprehension | 24 | 0.986 | 1.000 | 0.752 | 1.312 |
| Persona comprehension - Baseline comprehension | 24 | 0.000 | 0.000 | 0.000 | n/a |
| Persona faithfulness - NVD faithfulness | 24 | -1.819 | -2.000 | 0.481 | -3.780 |
| Baseline faithfulness - NVD faithfulness | 24 | -1.958 | -2.000 | 0.266 | -7.368 |
| Persona faithfulness - Baseline faithfulness | 24 | 0.139 | 0.000 | 0.339 | 0.409 |

## Figures

See `v2_bullet/figures/` for PNG (300 dpi) and SVG versions.

- `llm_judge_scores_bullet` -- comprehension and faithfulness scores, raw NVD vs. persona vs. baseline
