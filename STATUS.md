# STATUS.md
_Generated from repo inspection -- 2026-07-08. Do not hand-edit; re-run the inspection command._

---

## Pipeline stage

| Stage | Status |
|---|---|
| 1. Dataset (NVD pull) | DONE |
| 2. RAG corpus sampling | DONE -- `data/rag_corpus.jsonl` (12,000 records, 2026-06-23) |
| 3. Enrich (KEV + EPSS join) | DONE -- `data/rag_corpus_enriched.jsonl` (12,000 records, 2026-06-23) |
| 4. Eval sample selection | DONE -- `data/eval_sample.jsonl` (24 CVEs), `data/rag_corpus_final.jsonl` (11,976 records) |
| 5. ChromaDB (embed + ingest) | DONE -- `data/chroma_db/` (11,976 records, 2026-07-08) |
| 6. RAG + LLM summary | DONE (eval-sample generation) -- `v2_bullet/summaries/summaries_bullet.json`; dashboard does its own on-demand generation for the rest of the corpus, see Stage 7 |
| 7. Dashboard (Plotly Dash) | NOT STARTED |
| 8. Evaluation | NOT STARTED |

---

## Data state

**Raw NVD records (no enrichment)**

| File | Records | Date range | Source method |
|---|---|---|---|
| `data/cves_all_critical.jsonl` | 17,629 | 2020-01-04 to 2026-06-12 | JSON feed (all years) |
| `data/cves_all_high.jsonl` | 57,397 | 2020-01-02 to 2026-06-16 | JSON feed (all years) |
| `data/cves_all_medium.jsonl` | 74,404 | 2020-01-03 to 2026-06-16 | JSON feed (all years) |
| `data/cves_all_low.jsonl` | 6,654 | 2020-01-10 to 2026-06-12 | JSON feed (all years) |
| `data/cves_critical.jsonl` | 5,000 | -- | API pull (capped, older run -- superseded) |
| `data/cves_high.jsonl` | 5,000 | -- | API pull (capped, older run -- superseded) |

- Total across `cves_all_*` files: **156,084 records**
- Quality filter applied: CVSS v3.1 required, English description >= 100 chars, CPE present

**Derived datasets**

| File | Records | Notes |
|---|---|---|
| `data/rag_corpus.jsonl` | 12,000 | Proportional stratified sample (seed=42); all severities; unenriched -- superseded |
| `data/rag_corpus_enriched.jsonl` | 12,000 | As above + `kev_listed`, `epss_score`, `epss_percentile`; 65 KEV-listed; EPSS coverage 99.99% |

**Enrichment files**

| File | Records | Status |
|---|---|---|
| `data/known_exploited_vulnerabilities.csv` | 1,623 entries | Downloaded 2026-06-22; join not written |
| `data/epss_scores.csv` | 156,073 CVEs scored | Downloaded 2026-06-22; join not written |

- CWE extracted: **NO** -- NVD `weaknesses` field exists but not parsed in `clean_cve()`
- Eval sample (24 CVEs): **DONE** -- `data/eval_sample.jsonl`; `data/rag_corpus_final.jsonl` (11,976 records, eval CVEs excluded) is ready for ChromaDB ingestion

---

## Code state

| File | What it does | Runs? |
|---|---|---|
| `src/nvd_client.py` | Fetches one CVE to verify NVD API connectivity; prints shape | Yes |
| `src/__init__.py` | Empty package init | Yes |
| `notebooks/Data Access Check.ipynb` | Explores NVD API response shape; drills into CVSS/CPE fields | Yes (outputs present) |
| `notebooks/Data Pipeline.ipynb` | API-based pull pipeline capped at 5k per severity (CRITICAL/HIGH) with resume support | Obsolete -- hit 503 errors; superseded by JSON feed approach |
| `notebooks/CVE Pipeline - JSON Pull.ipynb` | JSON feed pipeline; pulls all CRITICAL/HIGH/MEDIUM/LOW 2020-2026 | Yes -- completed |
| `notebooks/EPSS Pull.ipynb` | Downloads full FIRST EPSS database, filters to our 156k CVEs, saves `data/epss_scores.csv` | Yes -- completed 2026-06-22 |
| `notebooks/RAG_Corpus_Sampling.ipynb` | Proportional stratified sample across all severities; distribution + attack vector + CVSS + description length analysis; saves `data/rag_corpus.jsonl` | Yes -- completed 2026-06-23 |
| `notebooks/RAG_Corpus_Enrichment.ipynb` | Joins KEV and EPSS onto `rag_corpus.jsonl`; adds `kev_listed`, `epss_score`, `epss_percentile`; saves `data/rag_corpus_enriched.jsonl` | Not yet run |
| `src/chroma_ingest.py` | Embeds `rag_corpus_final.jsonl` descriptions with `all-MiniLM-L6-v2` (sentence-transformers), ingests into persistent ChromaDB collection `rag_corpus` at `data/chroma_db/` with CVSS/severity/attack-vector/KEV/EPSS/year metadata | Yes -- completed 2026-07-08 |

---

## Gaps vs CLAUDE.md plan

- **KEV/EPSS/CWE enrichment** -- files downloaded; no enrichment notebook yet
- **Two overlapping CRITICAL/HIGH collections** -- `cves_critical.jsonl` / `cves_high.jsonl` (5k capped, API) superseded by `cves_all_*` files; safe to drop
- **`requirements.txt` incomplete** -- missing: `plotly`, `dash`, `anthropic`, `rouge-score`, `bert-score` (`chromadb`, `sentence-transformers` added 2026-07-08)
- **No LLM integration** -- no prompt templates, no summarisation pipeline, no three-part summary logic
- **No dashboard code** -- no Plotly Dash app
- **No evaluation code** -- no ROUGE/BERTScore/Flesch-Kincaid/LLM-as-judge scripts

---

## Current blocker

None.

## Next task

ChromaDB is ingested and query-verified. Proceed to RAG + LLM summary: add `anthropic` to `requirements.txt`, write the three-part prompt template, and write the retrieval pipeline that queries the `rag_corpus` collection for similar CVEs as context.

## Recent change (2026-07-08)

Wrote `src/chroma_ingest.py` and ingested `data/rag_corpus_final.jsonl` (11,976 records) into a persistent ChromaDB collection (`data/chroma_db/`, collection `rag_corpus`), embedding descriptions with `all-MiniLM-L6-v2` and storing `cvss_score`, `cvss_severity`, `attack_vector`, `kev_listed`, `epss_score`, `epss_percentile`, `year` as metadata. One record with a null EPSS score (`CVE-2025-38553`) is stored with a `-1.0` sentinel since ChromaDB metadata cannot hold `None`. First run failed partway on that same null-value issue (batch 27/47); fixed and re-ingested cleanly from scratch. Verified with a sample similarity query (SQL injection prompt correctly retrieved SQL injection CVEs). Model and vector-store choice justified in METHODOLOGY_LOG.md Section 7.

## Recent change (2026-07-07)

Eval sample exploitability threshold raised from EPSS >= 0.1 to EPSS >= 0.5 ("more likely than not to be exploited" -- more defensible than an arbitrary percentile cutoff). `notebooks/Eval_Sample_Selection.ipynb` was updated and re-executed; `data/eval_sample.jsonl` and `data/rag_corpus_final.jsonl` were regenerated. Five within-cell CVEs changed as a result (2 reused overrides from the 0.1 pass, 3 new overrides to fix cross-cell vendor repeats introduced by the smaller high-exploitability pools at 0.5). Full rationale and before/after pool sizes documented in METHODOLOGY_LOG.md Section 6.

---

## Full project checklist

**Data & enrichment**
- [x] NVD pull -- all severities, 2020-2026 (156,084 records)
- [x] KEV catalogue downloaded
- [x] EPSS scores downloaded
- [x] RAG corpus sampled -- 12,000 records, all severities, seed=42 (`data/rag_corpus.jsonl`)
- [x] Write enrichment notebook -- adds `kev_listed`, `epss_score`, `epss_percentile` to corpus records (CWE deferred)
- [x] Run enrichment notebook -- `data/rag_corpus_enriched.jsonl` produced 2026-06-23
- [x] Create eval sample -- 24 CVEs across severity x exploitability cells (`data/eval_sample.jsonl`, `data/rag_corpus_final.jsonl`)

**ChromaDB**
- [x] Add `chromadb`, `sentence-transformers` to `requirements.txt`
- [x] Write ingestion script -- embed descriptions, load into ChromaDB with metadata
- [x] Ingest RAG corpus -- `data/chroma_db/`, collection `rag_corpus`, 11,976 records

**RAG + LLM summary**
- [x] Add LLM SDK (`anthropic`) to `requirements.txt`
- [x] Write prompt template -- three-part structure (what's vulnerable / how exploited / remediation) -- `v2_bullet/prompts/prompt-persona_v2.txt` (bullet format, locked)
- [x] Write retrieval pipeline -- query ChromaDB for similar CVEs, feed as context
- [x] Wire retrieval + generation end-to-end -- eval-sample batch (`src/generate_summaries.py`) and on-demand per-CVE (`src/dashboard_generate.py`)

**Dashboard**
- [ ] Add `plotly`, `dash` to `requirements.txt`
- [ ] Build layout -- CVE selector, LLM summary panel, raw NVD description panel side-by-side
- [ ] Connect CVE selection to RAG+LLM pipeline
- [ ] Manual smoke test -- golden path + edge cases

**Evaluation**
- [ ] Add `rouge-score`, `bert-score` to `requirements.txt`
- [ ] Write automated metrics script -- ROUGE, BERTScore, Flesch-Kincaid readability, LLM-as-judge
- [ ] Design user questionnaire
- [ ] Recruit participants (developers + CS students, purposive sampling, BSREC approved)
- [ ] Run evaluation sessions
- [ ] Analyse results and write up

## Note (2026-07-27, not part of the generated inspection above)

This whole file predates the `prompt-prose` and `prompt-bullet` branch work and is
stale outside this note. On `prompt-bullet`: added `v2_bullet/prompts/prompt-baseline_v2.txt`
and `prompt-persona_v2.txt` (bullet-format three-part summary prompts), ported
`src/generate_summaries.py` from `prompt-prose` (repointed at the v2 prompts and a
new output path), and ran it against all 24 eval CVEs. Result: 48 records
(24 CVEs x baseline/persona) written to `v2_bullet/summaries/summaries_bullet.json`,
0 failures, model `claude-opus-4-6`, temperature 0. Details in `METHODOLOGY_LOG.md`
("Stage 6c").

