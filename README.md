# CVE Intelligence Dashboard

An LLM-powered CVE intelligence tool that uses RAG-based summarisation to turn raw
NVD vulnerability descriptions into a plain-language, three-part explanation
(**what's vulnerable**, **how it's exploited**, **what to do about it**) for
technical non-security personnel (developers, CS students).

Built as the practical artefact for an MSc Cyber Security Management thesis
(University of Warwick, WMG), evaluated against raw NVD descriptions via
automated metrics, LLM-as-judge, and a human comprehension study.

**Live demo:** https://cve-dashboard-625382019690.us-central1.run.app

## How it works

1. Pull CVE records from the NVD API, enrich with CISA KEV (known-exploited
   flag) and FIRST EPSS (exploitation probability score).
2. Embed and store in ChromaDB.
3. On CVE selection, retrieve similar CVEs as context and prompt an LLM to
   generate the three-part summary.
4. Serve through a Plotly Dash dashboard with a summary-vs-raw-NVD comparison
   view.

## Repository structure

| Path | Contents |
|---|---|
| `app.py`, `assets/` | The Dash dashboard app |
| `src/` | Pipeline (`nvd_client.py`, `chroma_ingest.py`, `generate_summaries.py`, `dashboard_*.py`), evaluation (`llm_judge*.py`, `compute_metrics_bullet.py`, `analyze_human_study*.py`, `retrieval_validation.py`), and figure-generation scripts. A few (`add_cwe_*.py`, `backfill_cwe.py`) are one-time data migrations, not part of the regular pipeline — see their docstrings. |
| `notebooks/` | Exploratory work and one-off pipeline runs (data pull, RAG corpus sampling/enrichment, eval sample selection) |
| `v2_bullet/` | Evaluation artefacts (prompts, generated summaries, metrics, LLM-judge results, rubrics, dashboard screenshots) for the current ("bullet-format") prompt. An earlier prose-format prompt iteration (`v1`) was evaluated and superseded before this branch; only the bullet-format results are carried here. Within `v2_bullet/`, "v1" vs current (e.g. `screenshots_v1/` vs `screenshots/`, `judge/v1/` vs `judge/`) refers to a later *UI* iteration (tooltips + clear-filters fix), not the prompt version. |
| `figures/` | Thesis chapter figures (intro, methodology, usability, human study) |
| `mock-ups/` | Early UI design mock-ups |
| `data/` | Not tracked in git (see `.gitignore`) — raw/enriched CVE pulls, the RAG corpus, and the ChromaDB store. Regenerate via the notebooks/scripts above against the NVD/EPSS/KEV sources. |
| `Dockerfile`, `.dockerignore`, `requirements-space.txt`, `SPACE_README.md` | Deployment config for the hosted dashboard (Google Cloud Run) |

`STATUS.md` is a generated, internal build-progress log (not a report) —
useful for tracing what was done and when, not written for external
readers.

## Running locally

Requires Python 3.13 and API keys for NVD, Anthropic, and OpenAI (the latter
is evaluation-only — ROUGE/BERTScore/LLM-judge scripts, not the dashboard
itself).

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # full dev/eval environment
# or: pip install -r requirements-space.txt   # dashboard-only runtime subset

cp .env.example .env   # add NVD_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
python app.py          # http://127.0.0.1:8050
```

The dashboard reads only `data/rag_corpus_final.jsonl`, `data/chroma_db/`,
and `data/dashboard_summary_cache.json` at runtime — these aren't in the
repo (see above) and need to be generated first via the pipeline notebooks
and `src/chroma_ingest.py`.
