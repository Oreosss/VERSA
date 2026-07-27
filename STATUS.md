# STATUS.md
_Generated from repo inspection -- 2026-07-22. Do not hand-edit; re-run the inspection command._

---

## Pipeline stage

| Stage | Status |
|---|---|
| 1. Dataset (NVD pull) | DONE |
| 2. RAG corpus sampling | DONE -- `data/rag_corpus.jsonl` (12,000 records, 2026-06-23) |
| 3. Enrich (KEV + EPSS join) | DONE -- `data/rag_corpus_enriched.jsonl` (12,000 records, 2026-06-23) |
| 4. Eval sample selection | DONE -- `data/eval_sample.jsonl` (24 CVEs), `data/rag_corpus_final.jsonl` (11,976 records) |
| 5. ChromaDB (embed + ingest) | DONE -- `data/chroma_db/` (11,976 records, 2026-07-08) |
| 6. RAG + LLM summary | DONE -- retrieval validated (`src/retrieval_validation.py`, 2026-07-14) and both prompt arms generated (`src/generate_summaries.py`, `summaries.json`, 48 records, 2026-07-20) |
| 7. Dashboard (Plotly Dash) | NOT STARTED |
| 8. Evaluation | IN PROGRESS -- automated metrics (ROUGE/BERTScore/Flesch-Kincaid) done 2026-07-22; LLM-as-judge, questionnaire, and participant sessions not started |

_Hand-added 2026-07-27 (no inspection script found to regenerate this file): prompt format changed from prose to bullet points on supervisor advice. Prose (v1) summaries, prompts, and metrics frozen and filed under `v1_prose/` as read-only history. Bullet (v2) generation not yet started; `v2_bullet/` created empty pending that work._

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
| `src/retrieval_validation.py` | Queries `rag_corpus` ChromaDB collection for each of the 24 eval CVEs, checks corpus/eval-set distinctness and nearest-neighbour distance distribution; writes `data/retrieval_validation.json`, `RETRIEVAL_VALIDATION.md` | Yes -- completed 2026-07-14 |
| `src/generate_summaries.py` | Generates three-part LLM summaries for all 24 eval CVEs under both frozen prompt templates (`prompt-baseline_v1.txt`, `prompt-persona_v1.txt`), reusing saved retrieval neighbours; model `claude-opus-4-6`, temperature 0; writes `summaries.json` (48 records) | Yes -- completed 2026-07-20 |
| `src/compute_metrics.py` | Computes ROUGE-1/2/L, BERTScore (P/R/F1, `roberta-large`), and Flesch-Kincaid grade level for all 48 summaries against the raw NVD description, plus FK for the 24 NVD descriptions as baseline; writes `metrics_per_summary.csv`/`.json`, `PROMPT_COMPARISON.md`, `figures/`, appends to `METHODOLOGY_LOG.md` | Yes -- completed 2026-07-22 |

---

## Gaps vs CLAUDE.md plan

- **KEV/EPSS/CWE enrichment** -- files downloaded; no enrichment notebook yet
- **Two overlapping CRITICAL/HIGH collections** -- `cves_critical.jsonl` / `cves_high.jsonl` (5k capped, API) superseded by `cves_all_*` files; safe to drop
- **`requirements.txt` still missing `plotly`, `dash`** -- everything else added (`chromadb`, `sentence-transformers` 2026-07-08; `anthropic` by 2026-07-20; `rouge-score`, `bert-score`, `textstat`, `matplotlib`, `scipy` 2026-07-22)
- **No dashboard code** -- no Plotly Dash app
- **LLM-as-judge not implemented** -- deliberately deferred to a later evaluation stage (see `METHODOLOGY_LOG.md`, "Automated evaluation metrics")
- **No user questionnaire yet** -- design, participant recruitment, and evaluation sessions not started

---

## Current blocker

None.

## Next task

Automated metrics (ROUGE, BERTScore, Flesch-Kincaid) are computed and written up. Proceed with either: (a) the Plotly Dash dashboard (CVE selector, summary-vs-raw-NVD comparison view), or (b) LLM-as-judge scoring, or (c) the user questionnaire design -- ask which before starting.

## Recent change (2026-07-22, documentation pass)

Documentation-only pass, no metrics recomputed and no script logic touched. Added a subsection to `FINDINGS_NOTES.md` Section 7 analysing the three Dale-Chall disagreement cases (CVE-2024-1781, CVE-2021-42013, CVE-2022-3062): both source description is already-simple cases converge with the same pattern already documented for Flesch-Kincaid, framed as a scope condition on the readability claim, and confirmed as non-overlapping with the two weakly-grounded retrieval CVEs (CVE-2023-29119, CVE-2023-43661). Audited `METHODOLOGY_LOG.md` for undocumented Stage 6b/6c decisions and added: model/temperature selection rationale, generation count, the dev-iteration-vs-lock separation, the retrieval-freeze rationale, the reference-URL label limitation, the KEV/EPSS display-only decision, the summary text extraction rule for metrics, and an explicit statistical-approach note. See conversation record for the full before/after audit list.

## Recent change (2026-07-22)

Wrote `src/compute_metrics.py` and computed ROUGE-1/2/L, BERTScore (precision/recall/F1, `roberta-large`), and Flesch-Kincaid grade level for all 48 generated summaries (`summaries.json`) against the raw NVD description for each eval CVE (`data/eval_sample.jsonl`), plus Flesch-Kincaid for the 24 raw NVD descriptions as a readability baseline. Reference-text choice (NVD description, for all three text-comparison metrics) and the per-metric favourable direction (FK: lower is better; BERTScore: closeness is evidence of grounding, not the goal; ROUGE: low is expected, not a failure) were confirmed with the user before implementation and documented in `METHODOLOGY_LOG.md`. `summaries.json` output text carries a trailing `Reference` URL section (and one record uses `**bold**` headers instead of `##`); both are stripped/normalised before scoring per user confirmation. Wrote per-summary results (`metrics_per_summary.csv`/`.json`), a paired small-N analysis with effect sizes reported as evidence not verdict (`PROMPT_COMPARISON.md`), four publication-quality figures at `figures/` (PNG 300dpi + SVG), and an "Automated evaluation metrics" section in `METHODOLOGY_LOG.md` covering all four metric families (LLM-as-judge noted as deferred) with pinned library/model versions for reproducibility. LLM-as-judge was explicitly out of scope for this task.

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
- [x] Write prompt template -- three-part structure (what's vulnerable / how exploited / remediation) (`prompt-baseline_v1.txt`, `prompt-persona_v1.txt`)
- [x] Write retrieval pipeline -- query ChromaDB for similar CVEs, feed as context (`src/retrieval_validation.py`)
- [x] Wire retrieval + generation end-to-end -- `src/generate_summaries.py`, `summaries.json` (48 records, 2026-07-20)

**Dashboard**
- [ ] Add `plotly`, `dash` to `requirements.txt`
- [ ] Build layout -- CVE selector, LLM summary panel, raw NVD description panel side-by-side
- [ ] Connect CVE selection to RAG+LLM pipeline
- [ ] Manual smoke test -- golden path + edge cases

**Evaluation**
- [x] Add `rouge-score`, `bert-score` to `requirements.txt` (also `textstat`, `matplotlib`, `scipy`)
- [x] Write automated metrics script -- ROUGE, BERTScore, Flesch-Kincaid readability (`src/compute_metrics.py`, `metrics_per_summary.csv`/`.json`, `PROMPT_COMPARISON.md`, `figures/`, 2026-07-22)
- [ ] LLM-as-judge -- deliberately deferred, not yet started
- [ ] Design user questionnaire
- [ ] Recruit participants (developers + CS students, purposive sampling, BSREC approved)
- [ ] Run evaluation sessions
- [ ] Analyse results and write up
