# Prompt Comparison: Automated Metrics

This file reports evidence, not a verdict. It contains descriptive statistics, paired differences, and effect sizes only; interpretation of which prompt arm is "better" is left to the dissertation chapters.

**Design:** paired, n=24 eval CVEs, 2 prompt arms (persona, baseline), same 24 CVEs in both arms. Small-N, exploratory. Paired significance tests below are reported as supporting evidence only, not as the primary claim, and no multiple-comparison correction has been applied. **Note on sample size:** n=24 is small for any population-level inference; the Wilcoxon results should not be read as confirmatory hypothesis tests, only as a descriptive supplement to the effect sizes and raw differences.

## Descriptive statistics

Mean, median, SD, min, max for each metric, per prompt arm, and for the Flesch-Kincaid grade level of the raw NVD description (n=24, not split by arm since it is the same set of 24 descriptions in both arms).

| Metric | N | Mean | Median | SD | Min | Max |
|---|---|---|---|---|---|---|
| ROUGE-1 (F) -- persona | 24 | 0.195 | 0.188 | 0.058 | 0.102 | 0.330 |
| ROUGE-2 (F) -- persona | 24 | 0.104 | 0.095 | 0.039 | 0.045 | 0.169 |
| ROUGE-L (F) -- persona | 24 | 0.138 | 0.136 | 0.045 | 0.067 | 0.207 |
| BERTScore precision -- persona | 24 | 0.809 | 0.809 | 0.009 | 0.790 | 0.826 |
| BERTScore recall -- persona | 24 | 0.902 | 0.904 | 0.014 | 0.869 | 0.925 |
| BERTScore F1 -- persona | 24 | 0.853 | 0.855 | 0.009 | 0.834 | 0.868 |
| Flesch-Kincaid grade (summary) -- persona | 24 | 13.125 | 12.966 | 1.389 | 11.023 | 15.883 |
| Dale-Chall score (summary) -- persona | 24 | 11.778 | 11.775 | 0.407 | 10.890 | 12.666 |
| Word count -- persona | 24 | 356.792 | 348.500 | 49.835 | 272.000 | 461.000 |
| ROUGE-1 (F) -- baseline | 24 | 0.221 | 0.210 | 0.067 | 0.113 | 0.350 |
| ROUGE-2 (F) -- baseline | 24 | 0.123 | 0.127 | 0.052 | 0.043 | 0.277 |
| ROUGE-L (F) -- baseline | 24 | 0.158 | 0.153 | 0.058 | 0.071 | 0.290 |
| BERTScore precision -- baseline | 24 | 0.817 | 0.818 | 0.010 | 0.792 | 0.836 |
| BERTScore recall -- baseline | 24 | 0.906 | 0.905 | 0.014 | 0.871 | 0.937 |
| BERTScore F1 -- baseline | 24 | 0.859 | 0.857 | 0.010 | 0.839 | 0.881 |
| Flesch-Kincaid grade (summary) -- baseline | 24 | 13.501 | 13.300 | 1.753 | 9.419 | 17.781 |
| Dale-Chall score (summary) -- baseline | 24 | 12.094 | 12.116 | 0.435 | 11.206 | 12.953 |
| Word count -- baseline | 24 | 315.958 | 312.500 | 38.929 | 247.000 | 397.000 |
| Flesch-Kincaid grade -- raw NVD description | 24 | 12.342 | 12.070 | 5.234 | 2.375 | 25.782 |
| Dale-Chall score -- raw NVD description | 24 | 13.650 | 13.811 | 1.688 | 10.304 | 16.469 |

## Persona vs. baseline: paired differences

Paired difference (persona minus baseline) per metric, matched by cve_id, n=24 pairs. Cohen's d (paired, d_z = mean diff / SD of diff) and Wilcoxon matched-pairs rank-biserial r are both reported as effect sizes; the Wilcoxon signed-rank test (W, p) is reported alongside as supporting evidence only.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) | Wilcoxon r | Wilcoxon W | Wilcoxon p |
|---|---|---|---|---|---|---|---|---|
| Persona ROUGE-1 (F) - Baseline ROUGE-1 (F) | 24 | -0.026 | -0.021 | 0.027 | -0.941 | -0.993 | 1.000 | 0.0000 |
| Persona ROUGE-2 (F) - Baseline ROUGE-2 (F) | 24 | -0.019 | -0.013 | 0.043 | -0.443 | -0.693 | 46.000 | 0.0020 |
| Persona ROUGE-L (F) - Baseline ROUGE-L (F) | 24 | -0.020 | -0.011 | 0.033 | -0.604 | -0.790 | 29.000 | 0.0009 |
| Persona BERTScore precision - Baseline BERTScore precision | 24 | -0.008 | -0.007 | 0.007 | -1.161 | -0.927 | 11.000 | 0.0000 |
| Persona BERTScore recall - Baseline BERTScore recall | 24 | -0.005 | -0.003 | 0.010 | -0.448 | -0.587 | 62.000 | 0.0105 |
| Persona BERTScore F1 - Baseline BERTScore F1 | 24 | -0.006 | -0.005 | 0.007 | -0.853 | -0.927 | 11.000 | 0.0000 |
| Persona Flesch-Kincaid grade (summary) - Baseline Flesch-Kincaid grade (summary) | 24 | -0.376 | -0.636 | 1.049 | -0.359 | -0.427 | 86.000 | 0.0691 |
| Persona Dale-Chall score (summary) - Baseline Dale-Chall score (summary) | 24 | -0.316 | -0.285 | 0.280 | -1.128 | -0.907 | 14.000 | 0.0000 |
| Persona Word count - Baseline Word count | 24 | 40.833 | 42.500 | 25.162 | 1.623 | 0.990 | 1.500 | 0.0000 |

## Summaries vs. raw NVD: Flesch-Kincaid paired difference

Paired difference (summary FK minus raw NVD FK) per arm, matched by cve_id, n=24 pairs per arm. A negative mean difference means the summary scored a lower (easier) grade level than the raw NVD description for that CVE.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) | Wilcoxon r | Wilcoxon W | Wilcoxon p |
|---|---|---|---|---|---|---|---|---|
| Persona summary FK - Raw NVD FK | 24 | 0.782 | 1.005 | 4.150 | 0.188 | 0.307 | 104.000 | 0.1974 |
| Baseline summary FK - Raw NVD FK | 24 | 1.159 | 1.194 | 3.757 | 0.308 | 0.387 | 92.000 | 0.1011 |

## Summaries vs. raw NVD: Dale-Chall paired difference

Paired difference (summary Dale-Chall minus raw NVD Dale-Chall) per arm, matched by cve_id, n=24 pairs per arm. As with Flesch-Kincaid, a negative mean difference means the summary scored lower (easier, less reliant on unfamiliar vocabulary) than the raw NVD description for that CVE.

| Comparison | N | Mean diff | Median diff | SD diff | Cohen's d (paired) | Wilcoxon r | Wilcoxon W | Wilcoxon p |
|---|---|---|---|---|---|---|---|---|
| Persona summary Dale-Chall - Raw NVD Dale-Chall | 24 | -1.872 | -1.857 | 1.460 | -1.282 | -0.940 | 9.000 | 0.0000 |
| Baseline summary Dale-Chall - Raw NVD Dale-Chall | 24 | -1.556 | -1.606 | 1.471 | -1.058 | -0.900 | 15.000 | 0.0000 |

## Figures

See `figures/` for PNG (300 dpi) and SVG versions of each figure below.

- `fk_grouped_nvd_persona_baseline` -- FK grade level, raw NVD vs. persona vs. baseline
- `bertscore_persona_vs_baseline` -- BERTScore F1 and precision, persona vs. baseline
- `rouge_persona_vs_baseline` -- ROUGE-1/2/L, persona vs. baseline
- `fk_paired_slope_nvd_to_summary` -- per-CVE paired FK change, raw NVD to summary
- `dc_grouped_nvd_persona_baseline` -- Dale-Chall score, raw NVD vs. persona vs. baseline
- `dc_paired_slope_nvd_to_summary` -- per-CVE paired Dale-Chall change, raw NVD to summary
- `word_count_persona_vs_baseline` -- word count, persona vs. baseline
