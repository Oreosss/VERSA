# CLAUDE.md

Project context for the CVE Intelligence Dashboard. Read this for the goal and constraints before acting. For current build state, see STATUS.md (generated from the actual repo, not this file).

## Goal

MSc Cyber Security Management thesis tool (University of Warwick, WMG). An LLM-powered CVE Intelligence Dashboard that uses RAG-based summarisation to improve vulnerability comprehension for technical non-security personnel (e.g. software developers, CS students) compared to raw NVD descriptions.

Target: distinction-level result. Thesis due 2 September 2026.

## What the tool does

Pulls CVE records from the NVD API, enriches with CISA KEV and FIRST EPSS, stores in ChromaDB. On CVE selection, retrieves similar CVEs as context and feeds them to an LLM to generate a plain-language three-part summary:
1. What is vulnerable
2. How it is exploited
3. What remediation action to take

Surfaced through a Plotly Dash dashboard with a summary-vs-raw-NVD comparison view.

## Tech stack

- Python (pyenv, 3.13)
- NVD API (data source), FIRST EPSS API, CISA KEV catalogue (enrichment)
- ChromaDB (vector store)
- Plotly Dash (frontend)
- Git, `.env`-based API key management

## Locked decisions (do not relitigate)

- **Wide pull then filter.** Raw pool includes LOW/MEDIUM/HIGH/CRITICAL. Filtering happens downstream, not at pull time.
- **Two separate datasets, kept distinct:**
  - RAG retrieval corpus (~10k CVEs): quality-filtered, HIGH/CRITICAL, not hand-curated.
  - Evaluation sample (15-30 CVEs): deliberate slice spanning severity x exploitability cells (KEV membership + EPSS). Participants read these.
- **Embedding vs metadata:** embed the description (optionally CWE and CPE vendor/product). CVSS scores, severity, attack vector, KEV flag, EPSS score, CWE, year are metadata for filtering, not embedded.
- **Three-part summary structure** (above). Not four-part.
- **Evaluation:** automated metrics (ROUGE, BERTScore, Flesch-Kincaid, LLM-as-judge) plus a user questionnaire with subject matter experts (developers, CS students), purposive sampling. BSREC ethics approved.

## Conventions

- `.py` files for production components (ingestion, pipeline). Jupyter notebooks for exploration and retrieval tests.
- Code style: clear over clever, this is a research prototype not production infra. Prefer simplicity.
- Writing/comments: avoid em dashes.

## Out of scope (do not suggest or build)

- Real-time / continuous CVE ingestion
- MCP integration (future-work discussion only)
- Azure / cloud infra (local only, explicitly ruled out)
- Multi-user auth
- MITRE ATT&CK mapping
