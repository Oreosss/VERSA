# METHODOLOGY_LOG.md
_Factual record for the thesis methodology chapter. Generated from repo inspection and data files. Last updated: 2026-07-07._
_Each section notes whether values were directly measured, inferred, or still missing (TODO)._

---

## 1. Raw Pull

**Method:** NVD JSON 2.0 annual bulk feeds (gzipped JSON). Not the REST API (see note below).

**Source URL template:** `https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz`

**Years fetched:** 2020, 2021, 2022, 2023, 2024, 2025, 2026 (7 feeds)

**Pull date:** 2026-06-17 _(inferred from JSONL file modification timestamps; not explicitly logged in notebook)_

**No API key used for feed downloads.** NVD API key (`NVD_API_KEY`) was configured in `.env` and used only for the earlier REST API pilot pull (see note).

**Raw CVE counts per year in feeds** _(source: notebook cell output logged during the 2026-06-17 MEDIUM/LOW run; note NVD updates feeds continuously so counts are point-in-time):_

| Year | CVEs in feed |
|------|-------------|
| 2020 | 21,050 |
| 2021 | 23,428 |
| 2022 | 27,516 |
| 2023 | 31,204 |
| 2024 | 39,132 |
| 2025 | 44,651 |
| 2026 | 26,104 |
| **Total** | **213,085** |

> Note: feeds include all severities (CRITICAL, HIGH, MEDIUM, LOW, NONE) mixed together. Severity filtering was applied post-download.

**Abandoned approach — REST API pipeline (`notebooks/Data Pipeline.ipynb`):**
- A pilot pull using the NVD REST API was attempted but scrapped. The REST API (`https://services.nvd.nist.gov/rest/json/cves/2.0`) returned persistent 503 errors during the pull, making reliable data collection impossible. An alternative approach using the NVD annual JSON feeds was explored instead and adopted as the definitive method.
- The REST API approach also queried one severity at a time and would have been capped at 5,000 records per severity, making it unsuitable for a complete dataset regardless.
- The notebook is marked obsolete. Output files `cves_critical.jsonl` and `cves_high.jsonl` (5,000 records each, partially collected before errors) are not used in the analysis.
- All analysis relies exclusively on the feed-based pull described above.

---

## 2. Quality Filtering Funnel

**Filters applied in `clean_cve()` (all three required; applied as one pass, not sequentially logged):**

1. CVSS v3.1 metric present (`cvssMetricV31` in the NVD `metrics` field)
2. English description present and length >= 100 characters
3. At least one CPE `configurations` block present (i.e. affected product identified)

**Filter funnel — full dataset (all years, all severities):**

| Stage | Records remaining | Records removed | % of previous stage | Source |
|---|---|---|---|---|
| Raw CVEs in 2020-2026 feeds | 213,085 | — | — | Notebook output, 2026-06-17 pull |
| After CVSS v3.1 present | ~199,718 | ~14,324 | ~6.7% | Retrospective re-analysis, 2026-06-22 |
| After description >= 100 chars | ~188,529 | ~11,189 | ~5.6% | Retrospective re-analysis, 2026-06-22 |
| After CPE configurations present | ~156,620 | ~31,909 | ~16.9% | Retrospective re-analysis, 2026-06-22 |
| **Final stored (all severities)** | **156,084** | — | — | **Directly counted from JSONL files** |

> Retrospective counts (marked ~) were computed on 2026-06-22 by re-running `clean_cve()` logic against the live NVD feeds. NVD updates feeds continuously after initial publication: the re-analysis shows 214,042 raw CVEs vs 213,085 at pull time, and 156,620 post-CPE vs 156,084 stored — a 536-record drift attributable to feed updates in the 5 days since the original pull. The stored JSONL file counts (156,084) are the definitive ground truth; the intermediate stage counts are approximate.

**Filter funnel — 2020 only (exact, from retrospective re-analysis on 2026-06-22):**

| Stage | Records remaining | Records removed |
|---|---|---|
| Raw CVEs in 2020 feed | 21,056 | — |
| After CVSS v3.1 | 19,358 | 1,698 (8.1%) |
| After description >= 100 chars | 18,384 | 974 (5.0%) |
| After CPE present | 18,082 | 302 (1.6%) |

2020 severity split of post-filter records: CRITICAL 2,497 | HIGH 7,604 | MEDIUM 7,479 | LOW 502

**Post-filter record counts per severity (all years, from JSONL files — exact):**

| Severity | Records | Date range |
|---|---|---|
| CRITICAL | 17,629 | 2020-01-04 to 2026-06-12 |
| HIGH | 57,397 | 2020-01-02 to 2026-06-16 |
| MEDIUM | 74,404 | 2020-01-03 to 2026-06-16 |
| LOW | 6,654 | 2020-01-10 to 2026-06-12 |
| **Total** | **156,084** | 2020-01-02 to 2026-06-16 |

**Post-filter counts per severity per year (exact, derived from `cves_all_*.jsonl` publication dates):**

Feed files contain all severities mixed together; the pipeline filters by the `cvss_severity` field after applying `clean_cve()`. Raw counts per severity before filtering are not tracked. Post-filter counts below are exact.

| Year | Raw CVEs in feed | CRITICAL | HIGH | MEDIUM | LOW | Year total |
|---|---|---|---|---|---|---|
| 2020 | 21,050 | 1,823 | 5,784 | 7,479 | 502 | 15,588 |
| 2021 | 23,428 | 2,301 | 7,445 | 8,932 | 720 | 19,398 |
| 2022 | 27,516 | 3,329 | 8,404 | 11,034 | 825 | 23,592 |
| 2023 | 31,204 | 3,232 | 8,528 | 13,472 | 1,146 | 26,378 |
| 2024 | 39,132 | 2,603 | 9,783 | 15,022 | 1,358 | 28,766 |
| 2025 | 44,651 | 2,332 | 9,896 | 11,753 | 1,494 | 25,475 |
| 2026 | 26,104 | 2,009 | 7,557 | 6,712 | 609 | 16,887 |
| **Total** | **213,085** | **17,629** | **57,397** | **74,404** | **6,654** | **156,084** |

> "Raw CVEs in feed" is the total for all severities combined in that year's NVD feed file. Year totals (post-filter) do not sum to raw because the quality filter rejects CVEs regardless of severity.

**RATIONALE: TODO** — _Why were years 2020-2026 chosen as the date range cut-off?_

**RATIONALE: TODO** — _Why is CVSS v3.1 required (vs accepting v2 or v3.0)?_

**RATIONALE: TODO** — _Why is description length >= 100 characters used as a quality threshold?_

**RATIONALE: TODO** — _Why is CPE presence required?_

---

## 3. RAG Corpus Sampling

**Script:** `notebooks/RAG_Corpus_Sampling.ipynb`  
**Output:** `data/rag_corpus.jsonl` (produced 2026-06-23)  
**Status: COMPLETE**

### Method

Proportional stratified random sample across all four severity levels. Each severity stratum was sampled in proportion to its share of the 156,084-record quality-filtered pool, so the corpus reflects the real-world NVD severity distribution rather than artificially weighting any tier. A fixed seed (`random.Random(42)`) ensures full reproducibility: any researcher running the notebook against the same source files will obtain an identical corpus.

**Decision — all severities included (not HIGH/CRITICAL only):** An earlier plan restricted the RAG corpus to HIGH/CRITICAL to keep the retrieval context focused on serious vulnerabilities. This was revised to include all four severity levels in order to give ChromaDB a broader, more representative embedding space. A wider distribution of vulnerability descriptions improves retrieval for the full severity range and better reflects the realistic distribution of CVEs an organisation would encounter. LOW severity CVEs represent only 4.3% of the pool and 4.3% of the corpus -- their inclusion does not meaningfully dilute the HIGH/CRITICAL content but avoids a gap in retrieval coverage.

### Sampling parameters

| Parameter | Value |
|---|---|
| Source pool | `data/cves_all_*.jsonl` (4 files, all severities) |
| Pool size | 156,084 records |
| Target corpus size | 12,000 records |
| Sampling method | Proportional stratified random sample |
| Random seed | 42 |
| Rounding rule | Floor per stratum; distribute remainder to strata with largest fractional parts |

### Resulting corpus composition

**Severity distribution (exact, from `notebooks/RAG_Corpus_Sampling.ipynb`):**

| Severity | Pool records | Pool % | Corpus records | Corpus % |
|---|---|---|---|---|
| CRITICAL | 17,629 | 11.3% | 1,355 | 11.3% |
| HIGH | 57,397 | 36.8% | 4,413 | 36.8% |
| MEDIUM | 74,404 | 47.7% | 5,720 | 47.7% |
| LOW | 6,654 | 4.3% | 512 | 4.3% |
| **Total** | **156,084** | | **12,000** | |

Corpus proportions match pool proportions to one decimal place in all strata, confirming the stratified sampling worked correctly.

**Year distribution (exact):**

| Year | Records | % of corpus |
|---|---|---|
| 2020 | 999 | 8.3% |
| 2021 | 1,410 | 11.8% |
| 2022 | 1,707 | 14.2% |
| 2023 | 1,954 | 16.3% |
| 2024 | 2,288 | 19.1% |
| 2025 | 2,284 | 19.0% |
| 2026 | 1,358 | 11.3% |

The corpus skews toward recent years (2023-2025 account for ~54%), reflecting NVD's growing publication volume over time. 2026 contributes 11.3% despite covering only the first six months of the year; this reflects the accelerating rate of CVE publication and is expected given the source data is a point-in-time pull (June 2026).

### Vendor and product diversity analysis

- **Unique CPE vendors in corpus: 3,574**
- No single vendor exceeds 7.4% of the corpus

**Top 20 CPE vendors (of 3,574 total):**

| Vendor | Records | % of corpus |
|---|---|---|
| linux | 885 | 7.4% |
| google | 661 | 5.5% |
| adobe | 274 | 2.3% |
| apple | 273 | 2.3% |
| ibm | 241 | 2.0% |
| oracle | 236 | 2.0% |
| microsoft | 209 | 1.7% |
| cisco | 167 | 1.4% |
| apache | 138 | 1.2% |
| tenda | 137 | 1.1% |
| huawei | 119 | 1.0% |
| siemens | 100 | 0.8% |
| dlink | 96 | 0.8% |
| jenkins | 96 | 0.8% |
| intel | 94 | 0.8% |
| phpgurukul | 93 | 0.8% |
| dell | 90 | 0.8% |
| samsung | 90 | 0.8% |
| mozilla | 90 | 0.8% |
| gitlab | 85 | 0.7% |

### Analytic observations

**Vendor concentration is low and distribution is broad.** The top vendor (linux) accounts for 7.4% of the corpus; the top two together (linux + google) account for 12.9%. The remaining 3,572 vendors each account for under 5.5%. This distribution is healthy for embedding diversity: no single vendor cluster dominates the ChromaDB vector space, which reduces the risk of retrieval bias toward any one technology stack.

**The linux figure reflects kernel CVE volume, not a sampling artefact.** The Linux kernel consistently generates a large share of NVD records due to the breadth of its codebase and the number of researchers reporting findings against it. Its 7.4% share in the corpus is proportional to its share of the underlying pool.

**phpgurukul (0.8%, 93 records) is a notable outlier.** phpgurukul is a single open-source PHP web application publisher with a disproportionately large CVE footprint relative to its real-world deployment base. Its presence in the top 20 is an artefact of how NVD assigns CVEs to small prolific publishers rather than an indication of major ecosystem coverage. This does not affect corpus quality materially at 0.8%.

**LOW severity coverage is intentionally proportional and not inflated.** LOW CVEs constitute 4.3% of the corpus (512 records), mirroring their share of the quality-filtered pool. Operational security practice commonly deprioritises LOW severity vulnerabilities given their typical profile: local or physical attack vectors, high complexity, or significant prerequisites that limit real-world exploitability. Keeping LOW at its natural proportion therefore reflects realistic deployment priorities. The 512 records provide sufficient retrieval coverage for any LOW CVEs that may appear in the evaluation sample.

**Year coverage is point-in-time and skewed toward recent vulnerabilities.** The source data was pulled in June 2026; 2026 CVEs therefore represent only a partial year. Summaries for very recent CVEs may have less contextually similar material to retrieve against (fewer analogous historical CVEs in the corpus) compared to well-established vulnerability classes. This is an inherent limitation of any time-bounded corpus.

### Limitations

- CPE vendor extracted from the first CPE match in the first node of `configurations`. CVEs with multiple vendors (e.g. joint advisories) are assigned to the first-listed vendor only. This may slightly undercount multi-vendor representation.
- The corpus reflects the NVD severity distribution, which is a function of what researchers choose to report and what vendors choose to disclose -- it is not a random sample of all vulnerabilities that exist in the wild.
- EPSS scores and KEV membership have not yet been joined at this stage; the corpus is unenriched descriptions only.

### Additional corpus analysis

The following analyses were run against `data/rag_corpus.jsonl` (2026-06-23) using cells added to `notebooks/RAG_Corpus_Sampling.ipynb`.

#### Attack vector distribution

| Attack vector | Count | % of corpus |
|---|---|---|
| NETWORK | 8,362 | 69.7% |
| LOCAL | 3,182 | 26.5% |
| ADJACENT_NETWORK | 341 | 2.8% |
| PHYSICAL | 115 | 1.0% |

**By severity:**

| Severity | NETWORK | LOCAL | ADJACENT_NETWORK | PHYSICAL |
|---|---|---|---|---|
| CRITICAL | 98.7% (1,337) | 0.4% (6) | 0.9% (12) | 0.0% (0) |
| HIGH | 65.8% (2,903) | 30.9% (1,364) | 3.2% (140) | 0.1% (6) |
| MEDIUM | 66.7% (3,816) | 28.9% (1,651) | 3.0% (172) | 1.4% (81) |
| LOW | 59.8% (306) | 31.4% (161) | 3.3% (17) | 5.5% (28) |

**Observation:** The corpus is dominated by remotely exploitable vulnerabilities (69.7% NETWORK), reflecting the real-world NVD distribution. CRITICAL is almost exclusively NETWORK (98.7%), consistent with the CVSS v3.1 scoring convention where network-accessible vulnerabilities with no authentication requirement and full impact on all three pillars produce the highest scores (typically 9.8). LOW severity shows the highest proportion of PHYSICAL (5.5%), as expected -- vulnerabilities requiring physical access are harder to exploit and consequently score lower.

#### CVSS score distribution within severity bands

| Severity | n | min | median | mean | max |
|---|---|---|---|---|---|
| CRITICAL | 1,355 | 9.0 | 9.8 | 9.68 | 10.0 |
| HIGH | 4,413 | 7.0 | 7.8 | 7.87 | 8.9 |
| MEDIUM | 5,720 | 4.0 | 5.5 | 5.60 | 6.9 |
| LOW | 512 | 1.7 | 3.3 | 3.19 | 3.9 |

CRITICAL score bins:

| Range | Count | % |
|---|---|---|
| 9.0-9.3 | 208 | 15.4% |
| 9.3-9.6 | 41 | 3.0% |
| 9.6-9.9 | 1,002 | 73.9% |
| 9.9-10.0 | 104 | 7.7% |

HIGH score bins:

| Range | Count | % |
|---|---|---|
| 7.0-7.5 | 840 | 19.0% |
| 7.5-8.0 | 2,116 | 47.9% |
| 8.0-8.5 | 456 | 10.3% |
| 8.5-8.9 | 996 | 22.6% |

**Observation:** CRITICAL scores cluster sharply at 9.6-9.9 (73.9%), with 9.8 being the dominant value. This reflects CVSS v3.1 scoring arithmetic: a NETWORK/LOW complexity/NO privileges/NO user interaction/UNCHANGED scope vulnerability with HIGH impact on all three pillars scores exactly 9.8. Reaching 10.0 requires SCOPE:CHANGED, a stricter condition; the 7.7% at 9.9-10.0 represent such cases. HIGH shows a bimodal pattern: large clusters at 7.5-8.0 (47.9%) and 8.5-8.9 (22.6%), with a trough at 8.0-8.5 (10.3%). This bimodality is a property of the CVSS formula -- certain metric combinations produce 7.x scores while others jump to 8.5+ -- not a corpus artefact.

#### Description length distribution

| Metric | Value |
|---|---|
| Minimum | 100 chars |
| 25th percentile | 195 chars |
| Median | 290 chars |
| Mean | 399 chars |
| 75th percentile | 443 chars |
| 99th percentile | 2,663 chars |
| Maximum | 3,998 chars |

By severity:

| Severity | Median | Mean | Min | Max |
|---|---|---|---|---|
| CRITICAL | 241 | 317 | 100 | 3,554 |
| HIGH | 291 | 391 | 100 | 3,998 |
| MEDIUM | 297 | 426 | 100 | 3,998 |
| LOW | 379 | 400 | 101 | 2,591 |

Length bucket distribution (whole corpus):

| Range | Count | % |
|---|---|---|
| 100-199 chars | 3,162 | 26.4% |
| 200-399 chars | 5,176 | 43.1% |
| 400-699 chars | 2,521 | 21.0% |
| 700-999 chars | 602 | 5.0% |
| 1,000+ chars | 539 | 4.5% |

**Observation:** The minimum of exactly 100 confirms the quality filter floor is functioning correctly. The median of 290 characters indicates typical descriptions are two to three sentences -- sufficient for sentence-transformer embeddings to capture semantic content. CRITICAL CVEs have the shortest median description (241 chars vs corpus median 290). This is a mild concern for retrieval quality: the most severe tier has the least descriptive text per record, giving the embedding model less signal to differentiate similar critical vulnerabilities. This reflects how NVD authors write critical advisories (often terse: "X allows remote code execution via Y") rather than a corpus deficiency.

**Note on the 100-char threshold:** The analysis confirms this threshold is conservative -- 26.4% of records sit between 100-199 characters, suggesting 150 chars could have been justified. However, raising it post-hoc would alter the pool used for sampling and is not warranted given the corpus is already produced. This is documented here as a methodological note for the thesis.

---

## 4. Enrichment

**Script:** `notebooks/RAG_Corpus_Enrichment.ipynb`
**Output:** `data/rag_corpus_enriched.jsonl` (produced 2026-06-23)
**Status: COMPLETE**

Fields added per record: `kev_listed` (bool), `epss_score` (float | null), `epss_percentile` (float | null).

### CISA KEV

- **Status: JOIN COMPLETE**
- Source: `data/known_exploited_vulnerabilities.csv` — 1,623 catalogue entries (downloaded 2026-06-22; entries span 2021-11-03 to 2026-06-18)
- Columns used: `cveID` (join key). Field added: `kev_listed` (boolean).
- KEV-listed CVEs in corpus: **65 of 12,000 (0.54%)**

**KEV by severity:**

| Severity | Corpus records | KEV-listed | KEV rate |
|---|---|---|---|
| CRITICAL | 1,355 | 29 | 2.1% |
| HIGH | 4,413 | 23 | 0.5% |
| MEDIUM | 5,720 | 13 | 0.2% |
| LOW | 512 | 0 | 0.0% |
| **Total** | **12,000** | **65** | **0.54%** |

### FIRST EPSS

- **Status: JOIN COMPLETE**
- Source: `data/epss_scores.csv` — 156,073 entries (downloaded 2026-06-22; all scores dated 2026-06-22)
- Fields added: `epss_score` (float | null), `epss_percentile` (float | null).
- Coverage: **11,999 of 12,000 records** have an EPSS score (99.99%). One CVE has an empty score entry in the upstream file (registered in EPSS database but not yet scored); treated as null.
- Note: the EPSS bulk file contains rows with empty `epss` and `percentile` fields for recently registered CVEs. These are treated as null rather than causing a parse error.

**EPSS distribution (scored records, n=11,999):**

| Metric | Value |
|---|---|
| Min | 0.00062 |
| Median | 0.00487 |
| Mean | 0.01978 |
| Stdev | 0.08637 |
| Max | 0.99999 |

**EPSS score buckets:**

| Range | Count | % |
|---|---|---|
| Very low (< 0.1) | 11,670 | 97.3% |
| Low (0.1 -- 0.3) | 144 | 1.2% |
| Medium (0.3 -- 0.7) | 97 | 0.8% |
| High (>= 0.7) | 88 | 0.7% |

**EPSS by severity (mean and median):**

| Severity | n | Mean | Median |
|---|---|---|---|
| CRITICAL | 1,355 | 0.0679 | 0.0115 |
| HIGH | 4,413 | 0.0193 | 0.0057 |
| MEDIUM | 5,719 | 0.0101 | 0.0037 |
| LOW | 512 | 0.0048 | 0.0033 |

### CWE

- **Status: DEFERRED**
- NVD `weaknesses` field exists in the raw feed JSON but was not retained by `clean_cve()` when the pipeline wrote the JSONL files. The field is therefore absent from `rag_corpus.jsonl`.
- To add CWE retrospectively would require re-fetching all 12,000 corpus CVEs from the NVD API (~40 minutes of rate-limited requests) for a field that is metadata-only (not embedded). Deferred; can be added in a later pass if CWE filtering is needed.
- The KEV CSV does include a `cwes` column (CWE for the 65 KEV-listed records) but partial coverage is not useful as a standalone metadata field.

### Analytic observations

**EPSS is heavily right-skewed (power-law distribution).** 97.3% of the corpus scores below 0.1. The mean (0.020) is four times the median (0.005), driven by a small tail of high-scoring CVEs. This distribution is consistent with the broader CVE ecosystem: the vast majority of publicly disclosed vulnerabilities never see real-world exploitation. This has a direct implication for the evaluation sample: a cell defined as "high exploitability" cannot rely on EPSS >= 0.5 alone (only 2.5% of the corpus, 302 records) without either casting a wider threshold or combining EPSS with KEV membership.

**KEV and EPSS are correlated but not redundant.** KEV-listed CVEs have a mean EPSS of 0.52 vs 0.017 for non-KEV CVEs, confirming that confirmed exploitation (KEV) and predicted exploitation probability (EPSS) are related signals. However, the correlation is imperfect: 94 corpus CVEs score >= 0.5 on EPSS but are not in KEV. These are high-probability exploitation candidates that have not (yet) been confirmed as exploited in the wild. Using both signals in the eval sample matrix therefore provides more complete coverage of the exploitability space than either signal alone.

**CVSS severity and EPSS are weakly correlated within the corpus.** Even for CRITICAL CVEs (n=1,355), the median EPSS is only 0.0115 -- meaning the typical CRITICAL CVE has approximately a 1.2% predicted exploitation probability. CVSS measures potential impact if exploited; it is not a measure of likelihood. This misalignment between CVSS severity and EPSS is a recurring empirical finding in the security literature and provides an explicit justification for enriching the corpus with EPSS: users who see only a CRITICAL badge may overestimate real-world risk unless contextualised.

**HIGH EPSS non-KEV CVEs (EPSS >= 0.5, not KEV-listed): 94 records.** By severity: CRITICAL 37, HIGH 37, MEDIUM 20, LOW 0. These represent a "shadow zone" -- vulnerabilities with high exploitation potential that have not been formally catalogued as exploited. The eval sample should include at least one CVE from this group to test whether LLM summarisation helps users identify elevated risk that the raw NVD record obscures.

**KEV coverage in MEDIUM.** 13 MEDIUM-severity CVEs in the corpus are KEV-listed. The existing evaluation sample cell matrix (Section 6) covers only HIGH and CRITICAL; this means 20% (13/65) of available KEV-listed CVEs are excluded from the matrix. The Section 6 matrix should be revised to include a MEDIUM row, or the KEV-listed MEDIUM CVEs should be explicitly noted as out of scope for the eval sample with a justification.

**Low EPSS floor.** The minimum EPSS score in the corpus is 0.00062, slightly above zero. No CVE with an EPSS score of exactly 0 appears in the corpus. This is expected: EPSS v3 uses a calibrated model with a non-zero baseline probability for all scored CVEs.

---

## 5. Final Datasets

### RAG Retrieval Corpus (12,000 CVEs)
- **Status: ENRICHED** — `data/rag_corpus_enriched.jsonl`, produced 2026-06-23
- Method: proportional stratified random sample across all severities (see Section 3), enriched with KEV and EPSS (see Section 4)
- Fields: all fields from `rag_corpus.jsonl` plus `kev_listed` (bool), `epss_score` (float | null), `epss_percentile` (float | null)
- Next step: ChromaDB ingestion (embed descriptions, load with metadata)

### Evaluation Sample (24 CVEs)
- **Status: COMPLETE** -- `data/eval_sample.jsonl`, produced 2026-07-02, regenerated 2026-07-07 (EPSS threshold revised to 0.5)
- Method: purposive selection across 3x2 severity x exploitability matrix; 4 CVEs per cell; see Section 6 for full details and rationale
- `data/rag_corpus_final.jsonl` (11,976 records) is the version with eval CVEs removed -- use this for ChromaDB ingestion

---

## 6. Evaluation Sample — CVE List

**Script:** `notebooks/Eval_Sample_Selection.ipynb`
**Output:** `data/eval_sample.jsonl` (produced 2026-07-02; EPSS threshold revised and file regenerated 2026-07-07)
**Status: COMPLETE -- 24 CVEs selected**

### Cell matrix and selection rationale

**Cell definitions (severity x exploitability, 3x2 matrix):**

| | Low exploitability (EPSS < 0.5, KEV=No) | High exploitability (EPSS >= 0.5 OR KEV=Yes) |
|---|---|---|
| CRITICAL | Cell A | Cell B |
| HIGH | Cell C | Cell D |
| MEDIUM | Cell E | Cell F |

**Exploitability threshold — revised 2026-07-07: EPSS >= 0.1 -> EPSS >= 0.5.**

The threshold was originally set at EPSS >= 0.1, chosen because it corresponds to roughly the 97th percentile of the corpus's EPSS distribution (see Section 4) -- already a meaningfully elevated bar given how right-skewed EPSS is (median 0.005, mean 0.020). This was revised to EPSS >= 0.5 for a more intuitive and defensible framing: **0.5 represents "more likely than not to be exploited"** -- a majority-probability threshold that is easier to justify and explain than an arbitrary percentile cutoff, and maps more directly onto how a non-expert reader would interpret "high exploitability."

**Pool-size impact of the revision** (records available per cell, before within-cell selection):

| Severity | Low pool (0.1) | Low pool (0.5) | High pool (0.1) | High pool (0.5) |
|---|---|---|---|---|
| CRITICAL | 1,202 | 1,289 | 153 | 66 |
| HIGH | 4,285 | 4,353 | 128 | 60 |
| MEDIUM | 5,653 | 5,687 | 67 | 33 |

Tightening the threshold shrinks the "high exploitability" pools substantially (e.g. MEDIUM high-pool falls from 67 to 33), but every cell retains well over the 4 records needed for selection, so the revision did not create a feasibility problem.

**Tradeoff noted for the thesis:** raising the threshold to 0.5 increases the proportion of "high exploitability" records that are KEV-listed rather than EPSS-only (e.g. for CRITICAL, KEV-listed records rise from 19% of the high pool at 0.1 to 44% at 0.5). This makes the EPSS and KEV signals within the "high" cells more correlated with each other than they were at 0.1, slightly reducing how independent the two signals are within that bucket. This is an accepted tradeoff in exchange for a threshold that is easier to justify conceptually (majority probability vs. an empirical percentile).

**MEDIUM included:** MEDIUM severity CVEs were included because the corpus contains KEV-listed and high-EPSS MEDIUM CVEs (see Section 4). Excluding MEDIUM would misrepresent the realistic distribution of vulnerabilities developers encounter. MEDIUM-severity vulnerabilities commonly affect widely deployed software (browsers, office tools, firmware) and form a realistic part of a developer's patching workload.

**4 CVEs per cell:** 24 total CVEs, at the upper end of the 15-30 range. 4 per cell provides sufficient within-cell variation for automated metrics comparison while keeping participant reading burden manageable. Equal cell sizes avoid weighting any severity-exploitability combination in the aggregate evaluation.

### Within-cell selection algorithm

A greedy deterministic algorithm was applied (see notebook for full code):
1. Candidates were vendor-deduplicated (one CVE per CPE vendor per cell), prioritising KEV-listed CVEs, then highest EPSS.
2. Candidates were assigned to four quadrants: `{NETWORK, other} x {short (<=250 chars), long (>250 chars)}`.
3. One CVE was selected from each quadrant in priority order, subject to no vendor repeat.
4. Any remaining slots were filled from the most-populated quadrant maintaining vendor uniqueness.

### Manual overrides (2026-07-07, after threshold revision)

Re-running the algorithm at the new 0.5 threshold reselects Cells A, C, E, and F from different underlying pools (Cells B and D are anchored by KEV-listed records and are threshold-invariant). This resurfaced two issues previously fixed at the 0.1 threshold, plus a new cross-cell vendor overlap introduced by the smaller high-exploitability pools:

- **CVE-2026-2701 -> CVE-2020-8010** (Cell A): the original was a 2026 CVE (progress), which has minimal analogous historical context in the RAG corpus. Same rationale as the 0.1-threshold fix for Cell C. Replaced with CVE-2020-8010 (broadcom, NETWORK, 250 chars).
- **CVE-2025-20362 -> CVE-2022-28810** (Cell F): the same 1139-char Cisco CVE with an "Update:"-prefixed description that was overridden at the 0.1 threshold resurfaced under 0.5. Same fix applied: replaced with CVE-2022-28810 (Zoho ManageEngine, NETWORK, 474 chars).
- **CVE-2024-34787 -> CVE-2021-21974** (Cell C): the smaller 0.5-threshold pool surfaced an Ivanti pick for Cell C that duplicated Ivanti entries already anchoring Cells B and D. Replaced with CVE-2021-21974 (VMware, ADJACENT_NETWORK, 352 chars) -- this also adds attack-vector diversity to Cell C.
- **CVE-2021-28554 -> CVE-2021-22717** (Cell C): removes a second cross-cell repeat (Adobe, also present in Cell D). Replaced with CVE-2021-22717 (Schneider Electric, NETWORK, 217 chars).
- **CVE-2020-2039 -> CVE-2023-0157** (Cell E): removes a cross-cell repeat (Palo Alto Networks, also present in Cell B). Replaced with CVE-2023-0157 (UpdraftPlus, NETWORK, 325 chars).

**One repeat intentionally retained:** Ivanti still appears in both Cell B and Cell D. Both are the top EPSS/KEV picks for their respective cells (EPSS 1.000 and 0.965) and represent genuinely near-certain real-world exploitation. Removing either in favour of a lower-confidence record purely for cosmetic vendor diversity was judged not worth the tradeoff -- Ivanti's outsized presence in both cells reflects a real pattern in the CVE landscape (Ivanti products have had a high volume of actively exploited vulnerabilities), not a selection artefact.

### Final selection

| Cell | CVE ID | Severity | KEV | EPSS | Attack vector | Desc len | Vendor |
|---|---|---|---|---|---|---|---|
| A | CVE-2020-8010 | CRITICAL | No | 0.4867 | NETWORK | 250 | broadcom |
| A | CVE-2023-50919 | CRITICAL | No | 0.4780 | NETWORK | 323 | gl-inet |
| A | CVE-2023-29119 | CRITICAL | No | 0.0033 | ADJACENT_NETWORK | 122 | enelx |
| A | CVE-2021-23894 | CRITICAL | No | 0.0224 | ADJACENT_NETWORK | 290 | mcafee |
| B | CVE-2024-21887 | CRITICAL | Yes | 1.0000 | NETWORK | 248 | ivanti |
| B | CVE-2021-26084 | CRITICAL | Yes | 1.0000 | NETWORK | 374 | atlassian |
| B | CVE-2024-3400 | CRITICAL | Yes | 1.0000 | NETWORK | 399 | paloaltonetworks |
| B | CVE-2021-42013 | CRITICAL | Yes | 0.9996 | NETWORK | 544 | apache |
| C | CVE-2020-8958 | HIGH | No | 0.4664 | NETWORK | 248 | gpononu |
| C | CVE-2023-43661 | HIGH | No | 0.4690 | NETWORK | 325 | all-three |
| C | CVE-2021-21974 | HIGH | No | 0.4506 | ADJACENT_NETWORK | 352 | vmware |
| C | CVE-2021-22717 | HIGH | No | 0.3891 | NETWORK | 217 | schneider-electric |
| D | CVE-2020-8260 | HIGH | Yes | 0.9648 | NETWORK | 184 | ivanti |
| D | CVE-2023-44221 | HIGH | Yes | 0.7493 | NETWORK | 263 | sonicwall |
| D | CVE-2020-8655 | HIGH | Yes | 0.5726 | LOCAL | 217 | eyesofnetwork |
| D | CVE-2023-21608 | HIGH | Yes | 0.6148 | LOCAL | 342 | adobe |
| E | CVE-2022-3062 | MEDIUM | No | 0.3740 | NETWORK | 163 | simplefilelist |
| E | CVE-2023-0157 | MEDIUM | No | 0.3246 | NETWORK | 325 | updraftplus |
| E | CVE-2021-30970 | MEDIUM | No | 0.1345 | LOCAL | 192 | apple |
| E | CVE-2024-1781 | MEDIUM | No | 0.1469 | ADJACENT_NETWORK | 467 | totolink |
| F | CVE-2021-37976 | MEDIUM | Yes | 0.1990 | NETWORK | 192 | google |
| F | CVE-2022-28810 | MEDIUM | Yes | 0.7042 | NETWORK | 474 | zohocorp |
| F | CVE-2021-22204 | MEDIUM | Yes | 0.9998 | LOCAL | 158 | exiftool_project |
| F | CVE-2022-40765 | MEDIUM | Yes | 0.1048 | ADJACENT_NETWORK | 255 | mitel |

### Sample characteristics

| Metric | Value |
|---|---|
| Total CVEs | 24 |
| Unique CVE IDs | 24 |
| KEV-listed | 12 (50%) -- all in high-exploitability cells |
| EPSS range | 0.0033 -- 1.0000 |
| Attack vectors | NETWORK 15, ADJACENT_NETWORK 5, LOCAL 4 |
| Description length range | 122 -- 544 chars (median 259) |
| Unique vendors | 23/24 (Ivanti appears twice, retained deliberately -- see overrides above) |
| Year range | 2020 -- 2024 |

**Year distribution:** 2020: 4, 2021: 8, 2022: 3, 2023: 4, 2024: 5. The 2021 concentration (8/24) reflects that several KEV-listed, high-EPSS CVEs anchoring the high-exploitability cells (B, D, F) originate from 2021 (e.g. Confluence OGNL injection, Apache path traversal, ExifTool DjVu flaw) -- well-established vulnerabilities with a long confirmed-exploitation history.

**Longest description: CVE-2021-42013 (Cell B, 544 chars).** Apache HTTP Server path traversal (the incomplete fix for CVE-2021-41773). Retained as the upper bound of description length in this sample -- shorter overall than the 0.1-threshold sample's outliers (previously up to 1118 and 1139 chars) since both length-outlier records were removed by the overrides above.

### Data leakage prevention

The 24 eval CVE IDs were removed from `rag_corpus_enriched.jsonl` before ChromaDB ingestion, producing `data/rag_corpus_final.jsonl` (11,976 records). This ensures that when the RAG pipeline retrieves similar CVEs as context for an eval CVE, it cannot trivially return the query CVE itself as its top neighbour.

---

## 7. ChromaDB Ingestion

**Script:** `src/chroma_ingest.py`
**Input:** `data/rag_corpus_final.jsonl` (11,976 records)
**Output:** persistent ChromaDB store at `data/chroma_db/`, collection `rag_corpus`

### Vector store choice: ChromaDB

ChromaDB was selected as the vector store because it is an embedded, file-backed database rather than a hosted service: it persists directly to disk (`data/chroma_db/`) with no separate server process, container, or cloud account required. This fits the project's locked constraint of a local-only tool with no cloud infrastructure (see CLAUDE.md "Out of scope"). It also natively supports storing arbitrary metadata alongside each vector and filtering on that metadata at query time (e.g. restrict retrieval to `cvss_severity=CRITICAL` or `kev_listed=true`), which the RAG pipeline and dashboard will rely on. As a single-user local research prototype, ChromaDB's lack of multi-user/auth features is not a limitation here (multi-user auth is itself out of scope).

### Embedding model choice: `all-MiniLM-L6-v2`

Embeddings are generated with `sentence-transformers`' `all-MiniLM-L6-v2`, a Sentence-BERT (SBERT) model (Reimers & Gurevych, 2019, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"). Rationale:

- **Performance-to-size tradeoff.** 384-dimensional output, ~80MB model size, fast inference on CPU -- suitable for embedding ~12,000 CVE descriptions and for embedding a query CVE at dashboard runtime without a GPU or noticeable latency.
- **Runs entirely locally.** No API calls, no per-embedding cost, no external dependency at inference time -- consistent with the project's local-only, offline-capable design.
- **Standard baseline.** `all-MiniLM-L6-v2` is one of the most widely used general-purpose sentence embedding models in RAG literature and tooling (including as ChromaDB's own default embedding function), making it a defensible, easily-reproduced choice for a thesis prototype rather than a bespoke or unvalidated one.

No comparative benchmarking of alternative embedding models (e.g. `all-mpnet-base-v2`, OpenAI/other API embeddings) was performed; this is noted as a **limitation** -- retrieval quality is not necessarily optimal, only adequate for the prototype's purpose, and formal embedding-model comparison is flagged as out-of-scope / future work.

### What is embedded vs. stored as metadata

Per the locked embedding decision (see CLAUDE.md), only the CVE `description` field is embedded. CVSS score, severity, attack vector, KEV flag, EPSS score/percentile, and publication year are stored as ChromaDB metadata for filtering, not embedded. CPE vendor/product and CWE are not embedded either -- CWE was deferred at the enrichment stage (Section 4) and was therefore never available to embed; CPE vendor/product was judged unnecessary given the "description only" baseline is the locked default (see decision log for this task).

**Metadata schema per record:** `cvss_score`, `cvss_severity`, `attack_vector`, `kev_listed`, `epss_score`, `epss_percentile`, `year` (parsed from `published`).

### Limitation: max-token truncation on long descriptions

`all-MiniLM-L6-v2` truncates input at 256 word-piece tokens (roughly ~1,000-1,300 characters of English text). Per the corpus description-length analysis (Section 3), the median description is 290 characters (well within the limit), but 4.5% of the corpus exceeds 1,000 characters and the maximum is 3,998 characters. For these longer records (concentrated in HIGH/MEDIUM severity, per Section 3's length-by-severity table), the embedding is computed only from the truncated (leading) portion of the description -- content beyond the token limit does not influence the vector. This is flagged as a limitation of using a fixed-length sentence embedding model on CVE text of variable length, rather than corrected for (e.g. via chunking), since CVE descriptions are typically front-loaded with the most salient information (what is vulnerable, how) and truncation is expected to have a modest impact in the majority of cases.

### Reproducibility parameters

| Parameter | Value |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` (sentence-transformers) |
| Vector store | ChromaDB, `PersistentClient` |
| Persistence path | `data/chroma_db/` |
| Collection name | `rag_corpus` |
| Batch size | 256 records per `add()` call |
| Source corpus | `data/rag_corpus_final.jsonl` (11,976 records, eval CVEs excluded) |

---


## Appendix — Data Files Reference

| File | Records | Method | Status |
|---|---|---|---|
| `data/cves_all_critical.jsonl` | 17,629 | JSON feed, quality-filtered | Current |
| `data/cves_all_high.jsonl` | 57,397 | JSON feed, quality-filtered | Current |
| `data/cves_all_medium.jsonl` | 74,404 | JSON feed, quality-filtered | Current |
| `data/cves_all_low.jsonl` | 6,654 | JSON feed, quality-filtered | Current |
| `data/cves_critical.jsonl` | 5,000 | REST API pilot (abandoned — persistent 503 errors) | Not used |
| `data/cves_high.jsonl` | 5,000 | REST API pilot (abandoned — persistent 503 errors) | Not used |
| `data/known_exploited_vulnerabilities.csv` | 1,623 | CISA KEV catalogue; entries span 2021-11-03 to 2026-06-18; downloaded 2026-06-22 | Current — join pending |
| `data/epss_scores.csv` | 156,084 | FIRST EPSS API bulk download; scores dated 2026-06-22; 11 CVEs unscored | Current — join pending |
| `data/rag_corpus.jsonl` | 12,000 | Proportional stratified sample from all 4 severity JSONL files; seed=42; produced 2026-06-23 | Superseded by enriched version |
| `data/rag_corpus_enriched.jsonl` | 12,000 | `rag_corpus.jsonl` + `kev_listed`, `epss_score`, `epss_percentile`; produced 2026-06-23 | Current — use this for ChromaDB ingestion |


## Note on Stages 6a-6d below

Stages 6a and 6b (and the "Automated Evaluation Metrics -- Prose (v1)" section) were originally recorded only in this file's history on the `prompt-prose` branch (commit `9c65bd8`), which diverged from `prompt-bullet` before those stages were run. They are ported here so this file is a single combined methodology record covering both the prose (v1) and bullet-format (v2) prompt arms, in run order. Two corrections were made during the port, both confirmed against the actual repository state rather than assumed:

- **File paths.** The auto-generated log entries on `prompt-prose` recorded pre-reorganisation, repo-root paths (e.g. `summaries.json`, `metrics_per_summary.csv`, `PROMPT_COMPARISON.md`, `figures/`) because they were written by the scripts at generation time, before those outputs were moved into `v1_prose/` (mirroring the later `v2_bullet/` layout used for the bullet arm). The paths below have been corrected to the final locations (`v1_prose/summaries/summaries_prose.json`, `v1_prose/metrics/...`, `v1_prose/figures/...`, `v1_prose/prompts/...`). File contents and the recorded SHA-256 prompt hashes were diffed against the actual files at commit `9c65bd8` and are unchanged by the move.
- **Retrieval review completion.** Stage 6a below originally stated the manual same-class relevance judgement was left blank for reviewer completion. That review has since been completed for all 24 eval CVEs in `RETRIEVAL_VALIDATION_VALIDATED.md` (committed 2026-07-27); this is noted inline in Stage 6a.

`src/compute_metrics.py` (used in the prose metrics stage) and the original `v1_prose_prompt-*_v1.txt` prompt filenames exist only on the `prompt-prose` branch history, not in this branch's working tree; `src/generate_summaries.py` and `src/retrieval_validation.py` are shared and present on both.

## Stage 6a -- Retrieval Validation (2026-07-14)

**Script:** `src/retrieval_validation.py`
**Outputs:** `data/retrieval_validation.json`, `RETRIEVAL_VALIDATION.md`

Ran retrieval validation against the live `rag_corpus` ChromaDB collection (11976 documents) using the 24-CVE eval sample (`data/eval_sample.jsonl`). For each eval CVE, retrieved top-5 nearest neighbours by cosine distance using the same embedding model as corpus build (`all-MiniLM-L6-v2`).

- Distinctness check: passed, 0 of 24 eval ids found in corpus.
- Cohort nearest-neighbour distance: min 0.0068, median 0.3418, p75 0.4032, max 0.6224.
- 6 eval CVE(s) flagged above cohort p75 nearest-neighbour distance for manual review (statistical flag only, not a verdict).
- Manual same-class relevance judgement per eval CVE was initially left blank in `RETRIEVAL_VALIDATION.md` for reviewer completion; grounding and eval-sample-quality verdicts were deliberately not computed by the script itself. This review was subsequently completed for all 24 eval CVEs and recorded in `RETRIEVAL_VALIDATION_VALIDATED.md` (committed 2026-07-27), which pairs each target description with its top-5 neighbours and a same-class assessment (e.g. "borderline", with notes on where neighbour classes diverge from the target).

## Stage 6b -- Baseline vs Persona Summary Generation, Prose (v1) (2026-07-20)

**Script:** `src/generate_summaries.py`
**Output:** `v1_prose/summaries/summaries_prose.json`

Ran both frozen prompt templates (`v1_prose/prompts/prompt-baseline_v1_prose.txt`, `v1_prose/prompts/prompt-persona_v1_prose.txt`) against all 24 eval CVEs, reusing the saved neighbours from `data/retrieval_validation.json` (no re-querying ChromaDB). Model and temperature were fixed across all calls: model `claude-opus-4-6`, temperature 0.

- Prompt hash (baseline): `5425b0919df5f085de3d751abe0e041e6ed50ff2aae688f49647c2fb460806cf`
- Prompt hash (persona): `e51f932d77c325eddee6fb45f7c723b004e04a21b9a8b73759628c2d6012229b`
- Records written this run: 48
- Records skipped (already present): 0
- Records failed after retries: 0
- Run timestamp: 2026-07-20T17:41:35.917227+00:00
- Generation only -- no metrics (ROUGE, BERTScore, Flesch-Kincaid, LLM-as-judge) computed in this step.

### Model and temperature selection rationale

The study required a fixed, low-temperature generation configuration so that outputs would be reproducible across prompt arms and across any later re-run. `claude-opus-4-6` was selected as the most capable model that still exposed a temperature parameter suitable for this constraint. The model choice was therefore driven by this methodological requirement rather than by an unconstrained ranking of model capability.

### Number of generations

One generation was produced per (CVE, prompt arm) pair, with no repeated sampling at a given configuration. 24 eval CVEs x 2 prompt arms = 48 generations, matching the 48 records written to `summaries_prose.json`.

### Development iteration vs. formal measurement

Informal iteration on both prompt templates took place before the prompt lock recorded above (the hashed, frozen `prompt-baseline_v1_prose.txt` and `prompt-persona_v1_prose.txt`, run under the fixed model and temperature settings noted above). No output produced during that informal iteration is reported as a result anywhere in this study. Only the 48 generations produced after the lock are used in the automated metrics or carried forward to later evaluation stages.

### Retrieval frozen rather than re-queried

Neighbours used for generation were reused from the saved Stage 6a output (`data/retrieval_validation.json`) rather than re-queried from the live ChromaDB collection at generation time. Freezing retrieval this way means any difference observed between the two prompt arms' output is attributable to the prompt itself, not to incidental drift in which neighbours happened to be retrieved for one arm's call versus the other's.

### Reference URLs: no source label available

The ingestion pipeline (Sections 1-4 above) does not capture a source or label field for reference URLs, a gap present in the raw NVD data itself rather than introduced at generation time. Summaries therefore surface each reference as a bare URL with no source label. The raw NVD reference lists in the eval data contain each URL more than once; these are deduplicated in first-seen order before being passed to the model. Inventing a plausible source label (e.g. "vendor advisory") was considered and rejected: no label data exists anywhere in the corpus to support one, and asserting a label the source data does not contain would breach the study's rule against introducing information not present in the source.

### KEV and EPSS: shown to the reader, not interpreted by the model

KEV and EPSS values are included in the header block shown to the reader alongside each summary, but both prompt templates explicitly instruct the model not to describe or interpret them ("The KEV and EPSS values are provided for the reader's context only. Do not describe or interpret them in the summary" -- `prompt-baseline_v1_prose.txt`, `prompt-persona_v1_prose.txt`). This keeps the variable being compared between the two prompt arms clean, since neither arm's summary text is shaped by exploitability signals that are identical across arms. It extends the same display-governed approach already used for the three CVSS-derived fields the prompts do permit the model to reason about (attack vector, privileges required, user interaction) to a second pair of fields that are shown to the reader but placed out of bounds for the model to describe or interpret.

## Automated Evaluation Metrics -- Prose (v1)

**Script:** `src/compute_metrics.py`
**Outputs:** `v1_prose/metrics/metrics_per_summary_prose.csv`, `v1_prose/metrics/metrics_per_summary_prose.json`, `v1_prose/metrics/PROMPT_COMPARISON_prose.md`, figures in `v1_prose/figures/`

Computed ROUGE, BERTScore, Flesch-Kincaid grade level, Dale-Chall readability score, and word count for all 48 generated summaries (24 persona, 24 baseline, paired across the same 24 eval CVEs), each scored against the raw NVD description for its CVE. Flesch-Kincaid grade level and Dale-Chall readability score were also computed for the 24 raw NVD descriptions themselves, as readability baselines. Full descriptive statistics, paired differences, and effect sizes are reported in `v1_prose/metrics/PROMPT_COMPARISON_prose.md` as evidence, not as an interpretive verdict.

### Reference text used for ROUGE and BERTScore

The raw NVD `description` field (from `data/eval_sample.jsonl`) is the reference text for both ROUGE and BERTScore, for every summary in both prompt arms. This is fixed because the research question is defined as improving comprehension relative to the raw NVD description, so NVD is the thing being compared against, not an alternative reference summary.

### Favourable direction differs per metric

The same NVD reference is used for all three text-comparison metrics, but a favourable result does not mean the same thing for each of them, and this distinction is preserved throughout the reporting in this project rather than treated as a single similarity score.

Flesch-Kincaid treats the NVD description as a baseline to beat. A summary grade level lower than the NVD grade level is the favourable outcome, since a lower grade level means the text is easier to read. This is a before/after comparison, not a similarity score.

Dale-Chall is treated the same way as Flesch-Kincaid. A summary Dale-Chall score lower than the NVD score is the favourable outcome, since a lower score means the text relies less on unfamiliar vocabulary. As with Flesch-Kincaid, NVD is the baseline to beat, not a similarity target.

BERTScore treats NVD as a fidelity anchor rather than a target to maximise. A summary that stays semantically close to the NVD description indicates it has not drifted from or fabricated beyond the source. A higher BERTScore is favourable only as evidence of grounding, not as evidence that comprehension has improved. A summary scoring near 1.0 would mean it barely transformed the source text at all, which is not the goal of this study.

ROUGE is expected to be low, and that is not a failure. Because the summaries deliberately rephrase the NVD description into plainer language, low lexical overlap with NVD is the anticipated and desired result. ROUGE is retained mainly as a conventional reference point rather than as a primary success measure. Low ROUGE alongside high BERTScore is read as the signature of faithful rephrasing, meaning preserved, wording changed.

### ROUGE

**What it measures.** ROUGE measures n-gram overlap between a generated text and a reference text. ROUGE-1 and ROUGE-2 count overlapping single words and word pairs respectively, and ROUGE-L measures the longest common subsequence of words, all reported here as F-measure against the raw NVD description. Porter stemming is applied before matching (`use_stemmer=True`), so words are reduced to a common root and grammatical variants such as "vulnerability" and "vulnerabilities" or "exploited" and "exploits" count as matches rather than mismatches. This is the standard configuration used in the original ROUGE toolkit and avoids penalising the summaries for ordinary morphological variation on top of the deliberate rephrasing already discussed below.
**Why it is included.** ROUGE is one of the most widely used automated metrics in summarisation research, and reporting it allows this study's results to sit alongside the broader summarisation literature, even though it is not expected to be the metric that best captures this study's goal.
**Pros for this task.** It is fast to compute, requires no external model, and gives a simple, well-understood lexical baseline that other summarisation studies also report.
**Limitations for this task.** ROUGE penalises the deliberate rephrasing the summaries are designed to perform. A summary that expresses the same vulnerability in plainer language will necessarily share fewer surface words with the NVD description, so a low ROUGE score here reflects successful transformation rather than infidelity to the source. It is retained mainly as a conventional reference point rather than as a measure this study optimises for or draws conclusions from in isolation.

### BERTScore

**What it measures.** BERTScore measures semantic similarity between a generated text and a reference text using contextual embeddings from a pretrained language model (`roberta-large`), matching tokens by embedding similarity rather than exact surface form. Precision, recall, and F1 are all recorded here rather than F1 alone, so that over-generation and under-coverage relative to the source can be distinguished.
**Why it is included.** It captures meaning preservation in a way ROUGE cannot, since it can recognise paraphrase and synonymy rather than requiring literal word overlap, which matters directly for summaries that are meant to rephrase, not copy, the source.
**Pros for this task.** Combined with low ROUGE, a high BERTScore supports the argument that a summary has preserved the meaning of the NVD description while changing its wording, which is the intended behaviour of the summarisation pipeline.
**Limitations for this task.** BERTScore supports a faithfulness argument but it is not a hallucination detector. It measures how semantically close the summary sits to the reference overall, not whether every specific claim in the summary is actually supported by the source, so a fabricated but topically plausible sentence can still score reasonably well. It is also weaker in specialised domains such as vulnerability descriptions, since the underlying language model is trained on general-purpose text rather than security-specific corpora.

### Flesch-Kincaid grade level

**What it measures.** Flesch-Kincaid grade level estimates the US school grade level needed to understand a piece of text, calculated from average sentence length and average word length (syllable count) only.
**Why it is included.** Readability relative to the raw NVD description is a central comparison in this study, since the tool's stated goal is to improve comprehension for technical non-security personnel, and grade level is a widely used, cheaply computed proxy for how approachable a piece of text is.
**Pros for this task.** It is simple, reproducible, requires no external model, and gives a direct before/after comparison against the raw NVD description for every eval CVE.
**Limitations for this task.** Flesch-Kincaid measures reading ease from sentence and word length only, not clarity, logical structure, or factual correctness. A summary can score a lower grade level while still being confusing, poorly organised, or wrong, so this metric supports the comprehension claim but cannot establish it alone. It is reported alongside, and is intended to be read alongside, the questionnaire-based comprehension evidence from the study's human evaluation.

### Dale-Chall readability score

**What it measures.** The Dale-Chall readability score estimates how difficult a text is to read by checking each word against a list of words familiar to most readers and penalising the proportion of words that fall outside that list, combined with average sentence length.
**Why it is included.** Flesch-Kincaid uses only sentence length and syllable count, so it has no way to detect vocabulary or jargon. A word such as "authentication" is short and scores as easy under Flesch-Kincaid, even though it is unfamiliar to a non-security reader and is exactly the kind of jargon this study's summaries are meant to explain. Dale-Chall targets that vocabulary barrier directly by scoring against a familiar-word list rather than word length, so it is included as a complementary readability proxy that may reveal a jargon-reduction effect Flesch-Kincaid structurally cannot see.
**Pros for this task.** It is simple, reproducible, requires no external model, and gives a direct before/after comparison against the raw NVD description for every eval CVE, on a dimension (word familiarity) that Flesch-Kincaid does not cover.
**Limitations for this task.** The familiar-word list underlying Dale-Chall was built for general English reading material, not for technical or security vocabulary specifically, so it will flag many correct and necessary security terms as unfamiliar regardless of how clearly they are explained. Proper names and regular inflections of listed words are also counted as difficult words by this implementation, which can inflate the score for text that names specific products, vendors, or CVE identifiers. As with Flesch-Kincaid, a lower score does not by itself establish that a text is genuinely clearer, only that it draws on more common vocabulary.

### Word count

**What it measures.** Whitespace-delimited token count (`len(text.split())`) of the same extracted three-part summary body used for the other text metrics, i.e. after the trailing reference/URL block is stripped.
**Why it is included.** To check for a length confound between the two prompt arms: if one arm is systematically more verbose than the other, that difference in raw length could itself explain part of any gap seen in the readability or comprehension metrics, rather than the prompt's plain-language framing being responsible.
**Limitations for this task.** Word count says nothing about whether the extra length is useful (e.g. more concrete remediation detail) or just padding, so it is read alongside the readability and comprehension metrics, not as a quality signal on its own.

### LLM-as-judge (deferred)

LLM-as-judge scoring is part of this study's evaluation design but is not implemented in this stage. It is deferred to a later stage and is out of scope for `src/compute_metrics.py`.

### Reproducibility

| Component | Pinned value |
|---|---|
| ROUGE library | `rouge-score` 0.1.2, `RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)` |
| BERTScore model | `roberta-large` (`bert-score` 0.3.13, lang=`en`, 17 layers, idf=False) |
| Flesch-Kincaid library | `textstat` 0.7.13, `flesch_kincaid_grade()` |
| Dale-Chall library | `textstat` 0.7.13, `dale_chall_readability_score()` |
| Word count method | `len(text.split())`, no external library |
| Statistics library | `scipy` 1.18.0, `scipy.stats.wilcoxon` |
| Random seeds | None used; all metrics in this script are deterministic given fixed model weights |

## Stage 6c -- Baseline vs Persona Bullet-Format Summary Generation (2026-07-27)

**Script:** `src/generate_summaries.py`
**Output:** `v2_bullet/summaries/summaries_bullet.json`

Ran both frozen bullet-format prompt templates (`prompt-baseline_v2.txt`, `prompt-persona_v2.txt`) against all 24 eval CVEs, reusing the saved neighbours from `data/retrieval_validation.json` (no re-querying ChromaDB). Model and temperature were fixed across all calls: model `claude-opus-4-6`, temperature 0.

- Prompt hash (baseline): `4c7e91f352255208649f2a9720a4b538f89d504dfd3c7daf33bf058ed229ce5a`
- Prompt hash (persona): `ffa21e43ddac83bba2f23e284d10c09515591d05b9dfebe269be29081a3e4761`
- Records written this run: 48
- Records skipped (already present): 0
- Records failed after retries: 0
- Run timestamp: 2026-07-27T16:45:50.094303+00:00
- Generation only -- no metrics (ROUGE, BERTScore, Flesch-Kincaid, LLM-as-judge) computed in this step.



## Stage 6d -- Automated Metrics on Bullet-Format Summaries (v2) (2026-07-28)

**Script:** `src/compute_metrics_bullet.py`
**Outputs:** `v2_bullet/metrics/metrics_per_summary_bullet.csv`, `v2_bullet/metrics/metrics_per_summary_bullet.json`, `v2_bullet/metrics/PROMPT_COMPARISON_bullet.md`, figures in `v2_bullet/figures/`

Computed ROUGE, BERTScore, Dale-Chall readability score, and word count for all 48 generated bullet-format summaries (24 persona, 24 baseline, paired across the same 24 eval CVEs used in v1 prose), each scored against the raw NVD description for its CVE. Dale-Chall was also computed for the 24 raw NVD descriptions themselves, as a readability baseline. Descriptive statistics and paired Cohen's d are reported in `v2_bullet/metrics/PROMPT_COMPARISON_bullet.md` as evidence, not as an interpretive verdict.

### Reused from v1 prose, unchanged

`src/compute_metrics_bullet.py` reuses the scoring logic from `src/compute_metrics.py` (frozen on `v1_prose/`, `prompt-prose` branch commit `9c65bd8`) directly: same ROUGE config (`rouge-score` 0.1.2, stemmed ROUGE-1/2/L), same BERTScore config (`bert-score` 0.3.13, `roberta-large`, 17 layers, idf=False), same Dale-Chall implementation (`textstat` 0.7.13), same word-count method (`len(text.split())`), same NVD reference text (`data/eval_sample.jsonl` `description` field), and the same Reference-section stripping regex applied to `output_text` before scoring. This preserves method parity between the v1 and v2 metric runs.

### Flesch-Kincaid excluded from this run

Flesch-Kincaid grade level was deliberately dropped for the bullet-format run. FK is computed from average sentence length and syllable count only, and the bullet format confounds sentence length directly: each bullet line is a short, single-clause "sentence" by construction, so a bullet-format FK score would largely reflect the formatting choice (many short lines) rather than genuine readability. Dale-Chall is the primary readability metric for this run instead, since it scores vocabulary familiarity rather than sentence length and is not subject to this confound.

### Bullet marker normalisation

Bullet markers are not words and must not leak into scoring. Before any metric is computed, `strip_bullet_markers()` removes the leading `"- "` marker and its indentation from every bullet line via `re.sub(r"(?m)^[ \t]*-[ \t]+", "", text)`, applied after the trailing Reference/URL section is stripped and before section headers (`## What is vulnerable` etc., left untouched) and body text are scored. Example, taken from CVE-2020-8010 baseline:

Before:
```
- This affects CA Unified Infrastructure Management, also known as Nimsoft or UIM, in versions 20.1, 20.3.x, and 9.20 and below.
```
After:
```
This affects CA Unified Infrastructure Management, also known as Nimsoft or UIM, in versions 20.1, 20.3.x, and 9.20 and below.
```

### No significance test in this run

v1 reported the Wilcoxon signed-rank test (W, p) and rank-biserial r alongside Cohen's d as supporting evidence. For v2, only paired Cohen's d is reported, per the exploratory, small-N (24) framing carried through this whole evaluation stage: descriptives and effect sizes, no population-level significance testing. This is a deliberate difference from v1's method, not an oversight.

### Reproducibility

| Component | Pinned value |
|---|---|
| ROUGE library | `rouge-score` 0.1.2, `RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)` |
| BERTScore model | `roberta-large` (`bert-score` 0.3.13, lang=`en`, 17 layers, idf=False) |
| Dale-Chall library | `textstat` 0.7.13, `dale_chall_readability_score()` |
| Word count method | `len(text.split())`, no external library |
| Random seeds | None used; all metrics in this script are deterministic given fixed model weights |

This run processed 48 rows. Files written were v2_bullet/metrics/metrics_per_summary_bullet.csv, v2_bullet/metrics/metrics_per_summary_bullet.json, v2_bullet/metrics/PROMPT_COMPARISON_bullet.md. 10 figures were written (dc_grouped_nvd_persona_baseline_bullet.png, dc_grouped_nvd_persona_baseline_bullet.svg, bertscore_persona_vs_baseline_bullet.png, bertscore_persona_vs_baseline_bullet.svg, rouge_persona_vs_baseline_bullet.png, rouge_persona_vs_baseline_bullet.svg, dc_paired_slope_nvd_to_summary_bullet.png, dc_paired_slope_nvd_to_summary_bullet.svg, word_count_persona_vs_baseline_bullet.png, word_count_persona_vs_baseline_bullet.svg).


## Stage 6e -- LLM-as-Judge Evaluation (2026-07-28)

**Script:** `src/llm_judge.py`
**Outputs:** `v2_bullet/judge/llm_judge_raw.json`, `v2_bullet/judge/llm_judge_mapping.json`, `v2_bullet/judge/llm_judge_per_text.csv`, `v2_bullet/judge/llm_judge_aggregate.json`, `v2_bullet/judge/LLM_JUDGE_COMPARISON.md`, figures in `v2_bullet/figures/`

Scored all 24 eval CVEs across three arms (persona summary, baseline summary, raw NVD description; `v2_bullet/summaries/summaries_bullet.json` and `data/eval_sample.jsonl`) on two dimensions (comprehension support, faithfulness to source) using an OpenAI model as judge, run 3 times per text per dimension at temperature 0. 432 judge calls in the full design; 432 made this run, 0 already present (resumed), 0 failed after retries.

### Judge model and independence rationale

**Judge model:** `gpt-4.1-2025-04-14`, temperature 0, pinned by exact dated snapshot for reproducibility, mirroring the fixed model/temperature discipline used for generation (Stage 6c). The judge is deliberately drawn from a different provider (OpenAI) than the generator (Anthropic, `claude-opus-4-6`), so that the model producing a summary is never the same model scoring it. This avoids self-evaluation bias: an LLM judge from the same family as the generator has been shown in the literature to rate outputs in its own stylistic register more favourably, independent of actual quality.

### Rubric (verbatim, locked and hashed)

- Comprehension rubric hash: `2ec3864652eb026778d13f9d2077a83f371c967a628de7bf5adb48d5c0e46bd7` (`v2_bullet/rubric/rubric_comprehension.txt`)
- Faithfulness rubric hash: `b06ddc055f39ad0b9508dec92bd218f1e7fbfc69922c7db4c08c0185d0422d69` (`v2_bullet/rubric/rubric_faithfulness.txt`)

**Comprehension rubric** (scored on the text alone, no reference supplied):

```
You are evaluating a short vulnerability write-up for a reader who is
technically capable (for example, a software developer or computer science
student) but does not work in security.

Score ONLY comprehension support: whether a reader like this could come away
understanding three things from the text alone:

1. What is vulnerable: the affected system, component, or software.
2. How it is exploited: the attack mechanism and the practical conditions
   needed (for example, access level, privileges, or user interaction).
3. What remediation action to take, or its scope (for example, what to check,
   what to update, or that the reader should escalate to a vendor), even if no
   fix currently exists.

This measures comprehension only. Do not score writing style, brevity, or
whether the text is faithful to any external source, that is scored
separately. Score the text exactly as written. Do not use outside knowledge of
this CVE, or of any other vulnerability, to fill in gaps the text itself
leaves open. If the text does not state something, treat it as absent, not as
implied.

No reference text is supplied for this dimension. Judge comprehension of the
text on its own terms.

Score on a 1 to 5 scale using these anchors:

5 - A technically capable non-security reader would clearly understand all
    three of what/how/remediation-scope from this text alone, with no
    significant ambiguity.
4 - The reader would understand at least two of the three clearly, and the
    third is present but only partially clear or requires some inference.
3 - The reader would understand roughly half the picture: some of
    what/how/remediation-scope is clear, but at least one is missing,
    confusing, or too vague to act on.
2 - The reader would come away with only a fragmentary understanding: most of
    what/how/remediation-scope is missing, contradictory, or too
    jargon-laden to follow without security expertise.
1 - The reader would not understand what is vulnerable, how it is exploited,
    or what to do about it from this text at all.

Return your answer as a single JSON object with exactly two fields and no
other text:

{"score": <integer 1-5>, "justification": "<one or two sentences citing what is or is not present in the text that drove this score>"}

TEXT TO SCORE:
<text under evaluation>
```

**Faithfulness rubric** (scored with the target CVE's own raw NVD description as reference):

```
You are evaluating whether a vulnerability write-up's claims are supported by
a specific reference description of the same vulnerability.

Score ONLY faithfulness to the reference supplied below: whether every
mechanism, version or product detail, and remediation claim made in the text
is actually present in, or a reasonable and directly supported restatement
of, the reference text. Do not use outside knowledge of this CVE, or of any
other, similar, or neighbouring vulnerability, to decide whether a claim is
supported. A claim is only supported if the reference text itself contains
it. If a claim happens to be true of a different but similar vulnerability,
and is not supported by this reference, treat it as unsupported here.

This measures faithfulness only. Do not score comprehension, writing style,
or brevity, those are scored separately.

Score on a 1 to 5 scale using these anchors:

5 - Every material claim in the text (mechanism, affected versions or
    products, remediation) is directly supported by the reference. No
    fabricated or unsupported detail.
4 - Nearly all claims are supported. At most one minor, non-central detail is
    not directly traceable to the reference.
3 - Most claims are supported, but at least one claim of moderate importance
    (for example, a specific mechanism or version detail) is not present in
    the reference.
2 - Multiple claims, including at least one central claim (what is
    vulnerable, how it is exploited, or the remediation action), are not
    supported by the reference.
1 - The text's central claims are substantially unsupported by, or contradict,
    the reference.

Return your answer as a single JSON object with exactly two fields and no
other text:

{"score": <integer 1-5>, "justification": "<one or two sentences citing the specific claim(s) that are or are not supported by the reference>"}

REFERENCE TEXT (the source of truth for this scoring; the text below is
scored against this and only this):
<target CVE's raw NVD description>

TEXT TO SCORE:
<text under evaluation>
```

### Split call design: why comprehension and faithfulness use different setups

The two dimensions measure different things and are deliberately scored with different call setups rather than a single combined prompt. Comprehension support is scored on the candidate text alone, with no reference material supplied, because it operationalises Endsley Level 2 situational-comprehension: whether a technically capable non-security reader could understand what is vulnerable, how it is exploited, and the remediation scope from that text by itself. Supplying the raw NVD description alongside it would let the judge fill comprehension gaps in the summary using the reference, which is not what a real reader of the summary alone could do. Faithfulness to source, conversely, is only meaningful relative to a ground truth, so it is scored with the target CVE's own raw NVD description supplied as reference material, and the rubric explicitly instructs the judge not to credit a claim as supported unless it is present in that specific reference (a claim that happens to be true of a neighbouring or similar CVE, but absent from this CVE's own description, is marked unsupported). For the raw NVD arm itself, faithfulness is scored against its own text as a control: this is expected to score at or near the top of the scale, and functions as a sanity check on the rubric and the judge rather than a result of interest.

### Blinding and multi-pass design

The judge is never told which arm (persona, baseline, or raw NVD) a text belongs to; every call presents the text under a neutral "TEXT TO SCORE" label with no framing about its origin, generation method, or source. This is a stronger form of blinding than swapping labels inside the prompt, since the model is given no arm identity to key off in the first place. A/B labelling is applied at the bookkeeping layer only: for each CVE, which of persona/baseline is "A" is randomised (`random.Random(42)`, consistent with this project's existing sampling-seed convention), and the raw per-call output file (`v2_bullet/judge/llm_judge_raw.json`) records only the label (A, B, or nvd for the raw-NVD arm), never the words "persona" or "baseline" directly. The true mapping is written to a separate file (`v2_bullet/judge/llm_judge_mapping.json`) and is only rejoined with the raw scores during aggregation in this same script, so the raw judge output is anonymised as an artefact in its own right, not just at prompt-construction time. The order in which the full set of (CVE, arm, dimension, pass) calls is dispatched is also randomised per run (`random.Random(42).shuffle`), rather than processed CVE-by-CVE or arm-by-arm in a fixed sequence, as a conservative mitigation against any incidental ordering effect, even though each call is an independent, stateless API request. Each (CVE, arm, dimension) is scored 3 times at temperature 0 to evidence stability: every pass, score, and justification is retained in `v2_bullet/judge/llm_judge_raw.json`, and per-text mean and standard deviation across passes are reported rather than a single-shot score, since some model backends are not perfectly deterministic even at temperature 0.

### Aggregation and framing

Per-text scores (mean of 3 passes) are aggregated to per-arm means, standard deviations, and paired Cohen's d effect sizes (persona vs. raw NVD, baseline vs. raw NVD, persona vs. baseline), matched by CVE, for both dimensions, following the same descriptive-statistics-and-effect-sizes-only framing used throughout this evaluation stage (Stage 6d): exploratory and small-N (24 CVEs), no significance claims.

### Pros and limitations of LLM-as-judge

**Pros.** LLM-as-judge scales to scoring dimensions (comprehension, faithfulness) that automated lexical/embedding metrics (ROUGE, BERTScore) cannot directly measure, since both require reading comprehension and claim-level fact-checking rather than surface or embedding similarity. It is far cheaper and faster than recruiting human raters for every candidate text, and the 3-pass design gives a direct, reportable measure of its own scoring stability, which a single human rating would not.

**Limitations, and how this design mitigates them where possible:**

- *Self-evaluation / self-preference bias.* An LLM judge tends to rate text in its own stylistic register more favourably. Mitigated by using a judge from a different provider (OpenAI) than the generator (Anthropic).
- *Position bias.* LLM judges asked to directly compare two options in the same call are known to favour whichever option is presented first (or second). This design avoids pairwise comparison entirely: every call scores exactly one text in isolation against a fixed rubric, so there is no position for the judge to be biased by. The residual processing-order randomisation (above) is a conservative extra measure, not a correction for a comparison the design does not otherwise perform.
- *Verbosity bias.* LLM judges are known to rate longer, more elaborated text more favourably independent of actual quality, which matters here since the persona and baseline prompt arms produce summaries of different typical length (see word-count results, Stage 6d). The rubric anchors are written around concrete, checkable content criteria (whether what/how/remediation-scope is present and clear, or whether specific claims are supported) rather than an open-ended holistic quality judgement, and explicitly instructs the judge not to score brevity or style. This reduces but cannot fully eliminate the risk that a more elaborate summary scores higher for its length rather than its content; it is noted here as a residual limitation rather than a solved problem.
- *Leniency/severity clustering and imperfect determinism.* LLM judges can cluster scores toward one end of a scale, and are not guaranteed to be perfectly deterministic even at temperature 0 depending on backend. Mitigated empirically, not assumed away, by running 3 passes per text per dimension and reporting the observed mean and standard deviation rather than a single score; see `v2_bullet/judge/llm_judge_per_text.csv` for the per-text spread actually observed.
- *No ground truth for comprehension.* Unlike faithfulness, which has the raw NVD description as a reference, there is no independent ground truth for what a real technically capable non-security reader would understand. The comprehension score is this judge model's estimate of that, not a measurement of an actual reader; the questionnaire-based human evaluation (Stage 8, see below) is the check on this dimension that LLM-as-judge alone cannot provide.

- Run timestamp: 2026-07-28T20:17:19.644562+00:00

### Manual note (2026-07-28, added after inspecting results, not part of the script-generated entry above): why faithfulness scored persona/baseline around 3, not near 5

Both summary arms scored consistently lower on faithfulness (persona mean 3.18, baseline mean 3.04) than the raw-NVD control (5.0, by construction). Inspecting a sample of the `justification` strings in `llm_judge_raw.json` shows this is not the judge detecting fabrication. The faithfulness reference used here is the bare NVD `description` field only, per this stage's own definition of "the target CVE's own raw NVD description" (`data/eval_sample.jsonl`'s `description` field). That field does not include the CVSS sub-fields (attack vector, privileges required, user interaction, confidentiality/integrity/availability impact) or KEV/EPSS values. However, `src/generate_summaries.py`'s `build_target_cve_block()` supplies those fields to the generator directly, as structured data separate from the description string (see Stage 6b/6c), and both prompt templates instruct the model to use them. The result is that both summary arms correctly restate real, sourced facts (e.g. "the attack vector is NETWORK", "no user interaction is required") that are true and were given to the generator, but are not present in the specific reference text this rubric scores against. The judge is applying the rubric exactly as written -- credit a claim only if the reference text itself contains it -- and is therefore correctly marking these restatements as unsupported *by that reference*, even though they are not hallucinated. This is a scope consequence of defining "faithfulness to the raw NVD description" narrowly as the free-text description field rather than the full structured CVE record, not a defect in the rubric or the judge, but it must be stated explicitly when interpreting the faithfulness results: a persona/baseline faithfulness score below the NVD control does not by itself indicate fabrication, and the `justification` fields in `llm_judge_raw.json` should be read alongside the numeric scores before drawing that conclusion in the Findings chapter.


## Stage 6f -- Faithfulness Sensitivity Check: Description-Only vs. Description+CVSS Reference (2026-08-07)

**Script:** `src/llm_judge_faithfulness_ext.py`
**Outputs:** `v2_bullet/judge/llm_judge_raw_faithfulness_ext.json`, `v2_bullet/judge/llm_judge_per_text_faithfulness_ext.csv`, `v2_bullet/judge/LLM_JUDGE_FAITHFULNESS_EXT_COMPARISON.md`, figures in `v2_bullet/figures/`

Stage 6e's faithfulness dimension scored each summary against the target CVE's bare `description` field only. That reference excludes the CVSS sub-fields (attack vector, attack complexity, privileges required, user interaction, CIA impact, CVSS score/severity) even though `generate_summaries.py`'s `build_target_cve_block()` supplies those fields to the generator directly, as structured data alongside the description, and both prompt templates instruct the model to use them. Inspecting Stage 6e's raw justifications (see METHODOLOGY_LOG.md's Stage 6e manual note) confirmed that most 'unsupported claim' flags on the persona/baseline arms were the judge correctly following its rubric while marking real, sourced CVSS-derived restatements as unsupported, simply because they were not literally present in the bare description string being used as the reference.

This stage re-scores faithfulness only (comprehension is not reference-based and is unaffected) using an EXPANDED reference: the description plus the CVSS sub-fields listed above, i.e. the same fields the generator was actually given. Two categories are deliberately still excluded from the expanded reference:

- **KEV listed / EPSS score.** External enrichment this project's own pipeline joined on from CISA and FIRST, not something NVD itself publishes on the record, and both prompt templates explicitly forbid the model from describing or interpreting them in the summary text. Including them in the faithfulness reference would blur 'faithful to NVD' with 'faithful to this project's own enrichment', a different claim.
- **Neighbour CVEs.** The Stage 6e brief was explicit that a claim supported only by a neighbouring CVE must not be credited as faithful. Still excluded here for the same reason.

The CVSS sub-fields, by contrast, are native NVD record data: they come from the same `cvssMetricV31` block on the same NVD record as the description, just a different field on it. Including them tests a stricter, more meaningful hallucination question (did the summary invent or misstate anything beyond the full structured NVD record it was given) rather than Stage 6e's narrower question (does the summary hold up against just the free-text description paragraph a reader would see).

Both results are kept and reported side by side, not merged or overwritten. Stage 6e's original scores remain valid evidence for its own, narrower question and are reused directly from `v2_bullet/judge/llm_judge_per_text.csv` rather than re-queried. This stage made 216 new judge calls (faithfulness only, expanded reference): 216 made this run, 0 already present (resumed), 0 failed after retries.

### Reference field composition

Extended reference = `description` + `"Attack vector: ... | Attack complexity: ... | Privileges required: ... | User interaction: ..."` + `"Confidentiality impact: ... | Integrity impact: ... | Availability impact: ..."` + `"CVSS score: ... (severity)"`, all pulled directly from `data/eval_sample.jsonl` fields, in the same field set and order `build_target_cve_block()` uses for generation (minus KEV, EPSS, references, and neighbours).

### Reuse of rubric, mapping, and blinding design

Same faithfulness rubric text and hash as Stage 6e (`b06ddc055f39ad0b9508dec92bd218f1e7fbfc69922c7db4c08c0185d0422d69`, `v2_bullet/rubric/rubric_faithfulness.txt`) -- only the reference content changes, not the judge's instructions. Same A/B mapping loaded from Stage 6e's `v2_bullet/judge/llm_judge_mapping.json` (not regenerated), so the same CVEs are anonymised the same way across both faithfulness runs and can be directly paired for comparison. Same blinding design: the judge is never told which arm a text belongs to. Model, temperature, and pass count unchanged (gpt-4.1-2025-04-14, temperature 0, 3 passes).

- Run timestamp: 2026-08-07T15:15:18.407031+00:00

---


## Dashboard Usability -- LLM-as-Judge Evaluation (2026-08-13)

**Script:** `src/capture_dashboard_screenshots.py`, `src/llm_judge_usability.py`
**Outputs:** `v2_bullet/judge/llm_judge_usability_raw.json`, `v2_bullet/judge/llm_judge_usability_per_screenshot.csv`, `v2_bullet/judge/llm_judge_usability_aggregate.json`, `v2_bullet/judge/LLM_JUDGE_USABILITY_COMPARISON.md`, figures in `v2_bullet/figures/`

Scores the live dashboard's usability, not the generated summary text -- every other evaluation method in this project (automated text metrics, Stage 6e LLM-as-judge, the human comprehension study) scores the summary text, never the dashboard it is surfaced through. This addresses Objective 3 ("surface these summaries through an interactive dashboard") and the Table 2.1 differentiation claim ("visual triage dashboard"), neither of which had any supporting evaluation before this stage.

6 representative dashboard states were captured with Playwright (v2_bullet/screenshots/) and each scored against all 10 of Nielsen's usability heuristics in a single call per pass, 3 passes per screenshot at temperature 0, using an OpenAI model as judge (18 judge calls in the full design; 18 made this run, 0 already present (resumed), 0 failed after retries).

### Judge model and independence rationale

**Judge model:** `gpt-4.1-2025-04-14`, temperature 0, the same model and convention used for the text judge (Stage 6e), for the same reason: a different provider (OpenAI) from the Anthropic generator, so no model ever evaluates output associated with its own family.

### Why heuristic evaluation, and why this is single-system, not blinded

Heuristic evaluation (Nielsen, 1994) is inspector-based, not user-based: an evaluator walks the interface and checks it against a fixed heuristic set, which is what this project's own informal "Nielsen-style walkthrough" (STATUS.md) already did once, ad hoc and undocumented. This script formalises and repeats that same walkthrough with multiple independent passes. Unlike the text judge (Stage 6e), which scores 3 arms and must be blinded to which is which, there is only one dashboard design here -- this is a single-system inspection, not a comparison, so no blinding scheme applies.

### Holistic-but-anchored scoring

Each call scores one PRIMARY screenshot against all 10 heuristics at once, rather than 10 separate calls, since a human evaluator would naturally notice several heuristic violations on the same screen at once. The other 5 screenshots are supplied as CONTEXT images in every call (not scored themselves), since heuristics such as consistency and standards cannot be judged validly from a single isolated frame.

### Rubric (verbatim, locked and hashed)

- Rubric hash: `a4ba0b278288f8bda6abfbe707664ee01e2f561676cdb78857d15a0993b16875` (`v2_bullet/rubric/rubric_usability.txt`)

```
You are conducting a heuristic evaluation of a CVE vulnerability-triage
dashboard, in the tradition of Nielsen's usability inspection method. The
dashboard is built for technical non-security personnel (developers, IT
staff, CS students) who need to find, understand, and act on vulnerability
data without formal security training.

You are shown one screenshot under evaluation (PRIMARY SCREEN) plus
screenshots of the other states of the same dashboard (CONTEXT SCREENS), so
that heuristics concerned with consistency and flow across the interface,
not just a single frame, can be judged validly. Score the PRIMARY SCREEN,
using the CONTEXT SCREENS only to judge consistency, transitions, and
system status across states.

PRIMARY SCREEN caption: {primary_caption}

Score all ten of Nielsen's usability heuristics against the PRIMARY SCREEN,
each on a 1 to 5 scale, where 5 means the screen strongly exemplifies the
heuristic and 1 means it clearly violates it. For each heuristic, ground
your score in what is actually visible on screen, not general assumptions
about dashboards. If a heuristic genuinely cannot be judged from what is
shown (for example, error prevention on a screen with no input controls
visible), score it 3 and say so in the justification rather than guessing.

1. Visibility of system status: does the screen make clear what is
   currently shown (result counts, active filters, which record is
   selected) and what the system is doing?
2. Match between system and the real world: is the language plain and
   suited to a reader without security training, or does it lean on raw
   security jargon, unexplained acronyms, or CVSS vector strings?
3. User control and freedom: can the user back out of the current state
   (close an expanded panel, clear a filter, deselect a record) without a
   dead end, based on what's visible?
4. Consistency and standards: do interactive elements (buttons, toggles,
   badges, dropdowns) look and behave the same way across the PRIMARY and
   CONTEXT screens?
5. Error prevention: do visible inputs (filters, search, dropdowns) guide
   the user toward valid choices, or is it easy to reach a confusing or
   invalid state?
6. Recognition rather than recall: is the information needed to judge a
   vulnerability's severity and relevance visible in place (badges, tags,
   summaries), or does it require the user to already know what a score or
   code means?
7. Flexibility and efficiency of use: do the visible filtering, search, and
   sorting controls let a user narrow down to what they need quickly?
8. Aesthetic and minimalist design: is the screen focused on what matters,
   or cluttered with information that competes for attention?
9. Help users recognize, diagnose, and recover from errors: if this screen
   shows an empty result, an error, or an edge case, is it communicated
   clearly with a way forward? If no such state is visible, score 3 and say
   so.
10. Help and documentation: is there any in-context explanation (labels,
    tooltips, helper text) of what a badge, score, or filter term means to
    a reader without security training?

Return your answer as a single JSON object with exactly these ten keys, and
no other text. Each value must be an object with a "score" (integer 1-5)
and a "justification" (one sentence citing what is or is not visible on the
PRIMARY SCREEN that drove the score):

{
  "visibility_of_system_status": {"score": <1-5>, "justification": "<...>"},
  "match_real_world": {"score": <1-5>, "justification": "<...>"},
  "user_control_freedom": {"score": <1-5>, "justification": "<...>"},
  "consistency_standards": {"score": <1-5>, "justification": "<...>"},
  "error_prevention": {"score": <1-5>, "justification": "<...>"},
  "recognition_not_recall": {"score": <1-5>, "justification": "<...>"},
  "flexibility_efficiency": {"score": <1-5>, "justification": "<...>"},
  "aesthetic_minimalist": {"score": <1-5>, "justification": "<...>"},
  "error_recovery": {"score": <1-5>, "justification": "<...>"},
  "help_documentation": {"score": <1-5>, "justification": "<...>"}
}
```

### Limitations

- *Not a substitute for real users.* However many independent passes, a single LLM judge is not the same as multiple independent human evaluators -- Nielsen's original method assumes evaluator diversity catches a broader set of distinct problems than repeated passes of the same evaluator can. No live-dashboard user study has been run (the human comprehension study, Stage 8, used static Qualtrics stimuli, never the dashboard itself); this method is a proxy, not a replacement, for that gap.
- *Screenshot-bound.* The judge sees static images of 6 states, not a live interactive session, so heuristics concerned with real-time responsiveness or multi-step interaction sequences beyond what a screenshot can show are judged only as far as the captured states allow.

- Run timestamp: 2026-08-12T23:25:40.215332+00:00
