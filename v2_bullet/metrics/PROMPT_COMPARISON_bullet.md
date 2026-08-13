# Prompt Comparison: Automated Metrics (v2, bullet format)

This file reports evidence, not a verdict. It contains descriptive statistics and paired Cohen's d effect sizes only; interpretation of which prompt arm is "better" is left to the dissertation chapters. This is the v2 (bullet-format) counterpart to `v1_prose/metrics/PROMPT_COMPARISON_prose.md`; see METHODOLOGY_LOG.md "Stage 6d" for the FK exclusion rationale, the bullet-normalisation method, and the reasoning for dropping the significance test that v1 reported.

**Design:** paired, n=24 eval CVEs, 2 prompt arms (persona, baseline), same 24 CVEs in both arms (identical eval set to v1 prose). Small-N, exploratory. Descriptive statistics and effect sizes only -- **no significance test is reported in this run** (v1's Wilcoxon signed-rank test was deliberately dropped here, see METHODOLOGY_LOG.md).

## Descriptive statistics

Mean, median, SD, min, max for each metric, per prompt arm, and for the Dale-Chall score of the raw NVD description (n=24, not split by arm since it is the same set of 24 descriptions in both arms).

| Metric | N | Mean | Median | SD | Min | Max |
|---|---|---|---|---|---|---|
| ROUGE-1 (F) -- persona | 24 | 0.231 | 0.218 | 0.077 | 0.109 | 0.392 |
| ROUGE-2 (F) -- persona | 24 | 0.127 | 0.124 | 0.057 | 0.055 | 0.234 |
| ROUGE-L (F) -- persona | 24 | 0.156 | 0.152 | 0.054 | 0.075 | 0.256 |
| BERTScore precision -- persona | 24 | 0.819 | 0.819 | 0.017 | 0.765 | 0.837 |
| BERTScore recall -- persona | 24 | 0.906 | 0.903 | 0.016 | 0.871 | 0.930 |
| BERTScore F1 -- persona | 24 | 0.860 | 0.860 | 0.013 | 0.834 | 0.881 |
| Dale-Chall score (summary) -- persona | 24 | 11.902 | 11.982 | 0.352 | 11.128 | 12.548 |
| Word count -- persona | 24 | 279.542 | 282.500 | 20.208 | 239.000 | 311.000 |
| ROUGE-1 (F) -- baseline | 24 | 0.240 | 0.227 | 0.071 | 0.126 | 0.359 |
| ROUGE-2 (F) -- baseline | 24 | 0.123 | 0.110 | 0.045 | 0.054 | 0.238 |
| ROUGE-L (F) -- baseline | 24 | 0.163 | 0.151 | 0.050 | 0.084 | 0.259 |
| BERTScore precision -- baseline | 24 | 0.821 | 0.824 | 0.012 | 0.793 | 0.838 |
| BERTScore recall -- baseline | 24 | 0.906 | 0.907 | 0.015 | 0.869 | 0.931 |
| BERTScore F1 -- baseline | 24 | 0.861 | 0.861 | 0.011 | 0.842 | 0.882 |
| Dale-Chall score (summary) -- baseline | 24 | 11.961 | 11.877 | 0.418 | 11.305 | 12.755 |
| Word count -- baseline | 24 | 266.083 | 269.000 | 27.573 | 214.000 | 330.000 |
| Dale-Chall score -- raw NVD description | 24 | 13.650 | 13.811 | 1.688 | 10.304 | 16.469 |

## Persona vs. baseline: paired differences

Paired difference (persona minus baseline) per metric, matched by cve_id, n=24 pairs. Cohen's d (paired, d_z = mean diff / SD of diff) is the only effect size reported.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) |
|---|---|---|---|---|---|
| Persona ROUGE-1 (F) - Baseline ROUGE-1 (F) | 24 | -0.009 | -0.004 | 0.026 | -0.337 |
| Persona ROUGE-2 (F) - Baseline ROUGE-2 (F) | 24 | 0.004 | -0.002 | 0.029 | 0.133 |
| Persona ROUGE-L (F) - Baseline ROUGE-L (F) | 24 | -0.007 | -0.002 | 0.022 | -0.324 |
| Persona BERTScore precision - Baseline BERTScore precision | 24 | -0.003 | -0.000 | 0.013 | -0.217 |
| Persona BERTScore recall - Baseline BERTScore recall | 24 | -0.000 | -0.000 | 0.008 | -0.037 |
| Persona BERTScore F1 - Baseline BERTScore F1 | 24 | -0.002 | -0.000 | 0.009 | -0.191 |
| Persona Dale-Chall score (summary) - Baseline Dale-Chall score (summary) | 24 | -0.059 | -0.068 | 0.253 | -0.235 |
| Persona Word count - Baseline Word count | 24 | 13.458 | 14.500 | 18.079 | 0.744 |

## Summaries vs. raw NVD: Dale-Chall paired difference

Paired difference (summary Dale-Chall minus raw NVD Dale-Chall) per arm, matched by cve_id, n=24 pairs per arm. A negative mean difference means the summary scored lower (easier, less reliant on unfamiliar vocabulary) than the raw NVD description for that CVE.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) |
|---|---|---|---|---|---|
| Persona summary Dale-Chall - Raw NVD Dale-Chall | 24 | -1.748 | -1.748 | 1.512 | -1.156 |
| Baseline summary Dale-Chall - Raw NVD Dale-Chall | 24 | -1.689 | -1.684 | 1.427 | -1.183 |

## Bullet normalisation

Leading bullet markers (`"- "` and indentation) were stripped from every bullet line before scoring; section headers were left untouched. Example (CVE-2020-8010, baseline):

Before: `- This affects CA Unified Infrastructure Management, also known as Nimsoft or UIM, in versions 20.1, 20.3.x, and 9.20 and below.`

After: `This affects CA Unified Infrastructure Management, also known as Nimsoft or UIM, in versions 20.1, 20.3.x, and 9.20 and below.`

## Figures

See `v2_bullet/figures/` for PNG (300 dpi) and SVG versions of each figure below.

- `dc_grouped_nvd_persona_baseline_bullet` -- Dale-Chall score, raw NVD vs. persona vs. baseline
- `bertscore_persona_vs_baseline_bullet` -- BERTScore F1 and precision, persona vs. baseline
- `rouge_persona_vs_baseline_bullet` -- ROUGE-1/2/L, persona vs. baseline
- `dc_paired_slope_nvd_to_summary_bullet` -- per-CVE paired Dale-Chall change, raw NVD to summary
- `word_count_persona_vs_baseline_bullet` -- word count, persona vs. baseline
