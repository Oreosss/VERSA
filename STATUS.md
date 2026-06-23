# STATUS.md
_Generated from repo inspection — 2026-06-22. Do not hand-edit; re-run the inspection command._

---

## Pipeline stage

| Stage | Status |
|---|---|
| 1. Dataset (NVD pull) | DONE |
| 2. Enrich (KEV + EPSS join) | IN PROGRESS — files downloaded, join not yet written |
| 3. ChromaDB (embed + ingest) | NOT STARTED |
| 4. RAG + LLM summary | NOT STARTED |
| 5. Dashboard (Plotly Dash) | NOT STARTED |
| 6. Evaluation | NOT STARTED |

---

## Data state

**Raw NVD records (no enrichment)**

| File | Records | Date range | Source method |
|---|---|---|---|
| `data/cves_all_critical.jsonl` | 17,629 | 2020-01-04 to 2026-06-12 | JSON feed (all years) |
| `data/cves_all_high.jsonl` | 57,397 | 2020-01-02 to 2026-06-16 | JSON feed (all years) |
| `data/cves_all_medium.jsonl` | 74,404 | 2020-01-03 to 2026-06-16 | JSON feed (all years) |
| `data/cves_all_low.jsonl` | 6,654 | 2020-01-10 to 2026-06-12 | JSON feed (all years) |
| `data/cves_critical.jsonl` | 5,000 | — | API pull (capped, older run) |
| `data/cves_high.jsonl` | 5,000 | — | API pull (capped, older run) |

- Total across `cves_all_*` files: **156,084 records**
- Quality filter applied: CVSS v3.1 required, English description >= 100 chars, CPE present
- KEV file: **DOWNLOADED** — `data/known_exploited_vulnerabilities.csv` (1,623 entries, pulled 2026-06-22); join not written
- EPSS file: **DOWNLOADED** — `data/epss_scores.csv` (156,073/156,084 CVEs scored, pulled 2026-06-22); join not written
- CWE extracted: **NO** (NVD `weaknesses` field exists but not parsed in `clean_cve()`)
- RAG corpus split (~10k HIGH/CRITICAL): **NOT CREATED**
- Eval sample (15-30 CVEs): **NOT CREATED**

---

## Code state

| File | What it does | Runs? |
|---|---|---|
| `src/nvd_client.py` | Fetches one CVE to verify NVD API connectivity; prints shape | Yes |
| `src/__init__.py` | Empty package init | Yes |
| `notebooks/Data Access Check.ipynb` | Explores NVD API response shape; drills into CVSS/CPE fields | Yes (outputs present) |
| `notebooks/Data Pipeline.ipynb` | API-based pull pipeline capped at 5k per severity (CRITICAL/HIGH) with resume support | Partial — last execution hit 503 (NVD outage), underlying code is correct |
| `notebooks/CVE Pipeline - JSON Pull.ipynb` | JSON feed pipeline; pulls all CRITICAL/HIGH/MEDIUM/LOW 2020-2026 | Yes — MEDIUM/LOW completed in last run; CRITICAL/HIGH pulled in a prior run (files exist, lines in notebook are commented out) |
| `notebooks/EPSS Pull.ipynb` | Downloads full FIRST EPSS database, filters to our 156k CVEs, saves `data/epss_scores.csv` | Yes — completed 2026-06-22 |

---

## Gaps vs CLAUDE.md plan

- **KEV/EPSS join** — both files downloaded; no script yet to join them onto the JSONL records
- **CWE not extracted** — `clean_cve()` ignores the `weaknesses` field; CWE is metadata required for filtering per plan
- **Corpus / eval split** — no script to derive the ~10k RAG corpus or 15-30 CVE eval sample from the raw files
- **Two overlapping CRITICAL/HIGH collections** — `cves_critical.jsonl` / `cves_high.jsonl` (5k capped, API) and `cves_all_critical.jsonl` / `cves_all_high.jsonl` (full, JSON feed); purpose of the 5k files is now superseded; likely safe to drop
- **`requirements.txt` incomplete** — missing: `chromadb`, `sentence-transformers` (or similar), `plotly`, `dash`, `anthropic` (or LLM SDK), `rouge-score`, `bert-score`
- **No ChromaDB code** — nothing for embedding generation or vector store ingestion
- **No LLM integration** — no prompt templates, no summarisation pipeline, no three-part summary logic
- **No dashboard code** — no Plotly Dash app
- **No evaluation code** — no ROUGE/BERTScore/Flesch-Kincaid/LLM-as-judge scripts, no questionnaire tooling

---

## Current blocker

<!-- Fill in: -->

## Next task

<!-- Fill in: -->

---

## Full project checklist

**Data & enrichment**
- [x] NVD pull — all severities, 2020-2026 (156,084 records)
- [x] KEV catalogue downloaded
- [x] EPSS scores downloaded
- [ ] Write enrichment join — add `kev_listed`, `epss`, `percentile`, `cwe_id` to JSONL records
- [ ] Create RAG corpus — ~10k HIGH/CRITICAL from enriched records
- [ ] Create eval sample — 15-30 CVEs across severity × exploitability cells

**ChromaDB**
- [ ] Add `chromadb`, `sentence-transformers` to `requirements.txt`
- [ ] Write ingestion script — embed descriptions, load into ChromaDB with metadata
- [ ] Ingest RAG corpus

**RAG + LLM summary**
- [ ] Add LLM SDK (`anthropic`) to `requirements.txt`
- [ ] Write prompt template — three-part structure (what's vulnerable / how exploited / remediation)
- [ ] Write retrieval pipeline — query ChromaDB for similar CVEs, feed as context
- [ ] Wire retrieval + generation end-to-end

**Dashboard**
- [ ] Add `plotly`, `dash` to `requirements.txt`
- [ ] Build layout — CVE selector, LLM summary panel, raw NVD description panel side-by-side
- [ ] Connect CVE selection to RAG+LLM pipeline
- [ ] Manual smoke test — golden path + edge cases

**Evaluation**
- [ ] Add `rouge-score`, `bert-score` to `requirements.txt`
- [ ] Write automated metrics script — ROUGE, BERTScore, Flesch-Kincaid readability, LLM-as-judge
- [ ] Design user questionnaire
- [ ] Recruit participants (developers + CS students, purposive sampling, BSREC approved)
- [ ] Run evaluation sessions
- [ ] Analyse results and write up
