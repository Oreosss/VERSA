# METHODOLOGY_LOG.md
_Factual record for the thesis methodology chapter. Generated from repo inspection and data files. Last updated: 2026-06-22._
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

**Note — earlier API-based pilot pull (superseded):**
- A separate pilot run using the NVD REST API (`https://services.nvd.nist.gov/rest/json/cves/2.0`) produced `cves_critical.jsonl` (5,000 records) and `cves_high.jsonl` (5,000 records) on 2026-06-17.
- Parameters: `resultsPerPage=2000`, `cvssV3Severity=CRITICAL|HIGH`, rate-limited at 0.6s between requests.
- These files are capped at 5,000 per severity and are superseded by the full feed pull; they are not used in the analysis pipeline.

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

**RATIONALE: TODO** — _Why were years 2020-2026 chosen as the date range cut-off?_

**RATIONALE: TODO** — _Why is CVSS v3.1 required (vs accepting v2 or v3.0)?_

**RATIONALE: TODO** — _Why is description length >= 100 characters used as a quality threshold?_

**RATIONALE: TODO** — _Why is CPE presence required?_

---

## 3. Downstream Severity Filter (RAG Corpus)

CLAUDE.md specifies the RAG retrieval corpus should be HIGH/CRITICAL only (~10k CVEs), quality-filtered but not hand-curated. No script to produce this split exists yet (see STATUS.md).

- HIGH + CRITICAL available post-quality-filter: **75,026** (17,629 + 57,397)
- Target corpus size: ~10,000
- Selection method: TODO (random sample? most recent? highest EPSS?)

**RATIONALE: TODO** — _Why HIGH/CRITICAL only for the RAG corpus (not MEDIUM/LOW)?_

---

## 4. Enrichment

### CISA KEV
- **Status: FILE DOWNLOADED** — `data/known_exploited_vulnerabilities.csv` (pulled 2026-06-22)
- Records: 1,623 entries; entries span 2021-11-03 to 2026-06-18 (latest `dateAdded`)
- Columns: `cveID`, `vendorProject`, `product`, `vulnerabilityName`, `dateAdded`, `shortDescription`, `requiredAction`, `dueDate`, `knownRansomwareCampaignUse`, `notes`, `cwes`
- Join key: `cveID` → CVE ID in JSONL files
- Field to add to CVE records: `kev_listed` (boolean), optionally `kev_date_added`, `kev_ransomware` (from `knownRansomwareCampaignUse`)
- **Join not yet executed** — no enrichment script exists yet

### FIRST EPSS
- **Status: FILE DOWNLOADED** — `data/epss_scores.csv` (pulled 2026-06-22)
- API endpoint: `https://api.first.org/data/v1/epss` (full bulk download, paginated at 10,000/request)
- Score date: 2026-06-22 (all rows carry the same date — EPSS is a daily snapshot)
- Coverage: 156,073 of 156,084 CVEs scored; 11 unscored (too recent to have a score)
- Score distribution: min 0.0005 | median 0.0049 | mean 0.0201 | max 1.0000
- Columns saved: `cve_id`, `epss`, `percentile`, `date`
- **Join not yet executed** — no enrichment script exists yet

### CWE
- **Status: NOT YET EXTRACTED**
- NVD `weaknesses` field is present in the raw feed but was not parsed by `clean_cve()`
- Field to add: `cwe_id` (first CWE ID if multiple)

---

## 5. Final Datasets

### RAG Retrieval Corpus (~10k CVEs)
- **Status: NOT YET CREATED**
- Planned: HIGH/CRITICAL, quality-filtered, not hand-curated
- Target: ~10,000 records
- Will require: KEV/EPSS enrichment + corpus split script

### Evaluation Sample (15-30 CVEs)
- **Status: NOT YET CREATED**
- Planned: deliberate slice spanning severity x exploitability cells (KEV membership + EPSS score)
- Will require: enrichment step first, then manual curation

**RATIONALE: TODO** — _Why 15-30 CVEs for the eval sample? What is the power/coverage justification?_

---

## 6. Evaluation Sample — CVE List

_Not yet created. Fill in below once the eval sample is selected._

| CVE ID | Severity | KEV | EPSS score | EPSS percentile | Severity x exploitability cell | Notes |
|---|---|---|---|---|---|---|
| TODO | | | | | | |

**Cell definitions (severity x exploitability matrix):**

| | Low exploitability (EPSS < 0.1, KEV=No) | High exploitability (EPSS >= 0.1 or KEV=Yes) |
|---|---|---|
| HIGH | Cell A | Cell B |
| CRITICAL | Cell C | Cell D |

**RATIONALE: TODO** — _How were the exploitability thresholds for cells defined (EPSS cut-offs, KEV weighting)?_

**RATIONALE: TODO** — _How many CVEs per cell, and why (equal distribution vs severity-weighted)?_

**RATIONALE: TODO** — _Purposive sampling criteria: how were specific CVEs within each cell selected (domain diversity, description length, availability of public PoC)?_

---

## Appendix — Data Files Reference

| File | Records | Method | Status |
|---|---|---|---|
| `data/cves_all_critical.jsonl` | 17,629 | JSON feed, quality-filtered | Current |
| `data/cves_all_high.jsonl` | 57,397 | JSON feed, quality-filtered | Current |
| `data/cves_all_medium.jsonl` | 74,404 | JSON feed, quality-filtered | Current |
| `data/cves_all_low.jsonl` | 6,654 | JSON feed, quality-filtered | Current |
| `data/cves_critical.jsonl` | 5,000 | REST API, capped pilot pull | Superseded |
| `data/cves_high.jsonl` | 5,000 | REST API, capped pilot pull | Superseded |
| `data/known_exploited_vulnerabilities.csv` | 1,623 | CISA KEV catalogue; entries span 2021-11-03 to 2026-06-18; downloaded 2026-06-22 | Current — join pending |
| `data/epss_scores.csv` | 156,084 | FIRST EPSS API bulk download; scores dated 2026-06-22; 11 CVEs unscored | Current — join pending |
