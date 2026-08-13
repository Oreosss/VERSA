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
| 7. Dashboard (Plotly Dash) | DONE -- `app.py`, `src/dashboard_data.py`, `src/dashboard_search.py`, `src/dashboard_generate.py` (2026-08-01) |
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
- [x] Add `plotly`, `dash` to `requirements.txt` (`dash`, `dash-bootstrap-components`; `plotly` came in as a `dash` dependency)
- [x] Build layout -- filterable/searchable CVE list + Explain detail view (`app.py`, `assets/style.css`)
- [x] Connect CVE selection to RAG+LLM pipeline -- on-demand generation + disk cache (`src/dashboard_generate.py`)
- [x] Manual smoke test -- golden path + edge cases (Playwright headless-browser run, see note below)

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


## Recent change (2026-08-12, detail-card padding fix)

Eleventh dashboard pass the same day. The scroll-reset fix (previous entry) addressed one
cause of the CVE ID looking cut off, but a screenshot showed a second, independent bug even
with scroll position correct: `.detail-header` (`assets/style.css`) had no padding rule at
all -- confirmed via computed-style inspection that `.detail-header`, `.cve-card`,
`#detail-card-body`, and `.risk-badge-row` were all `padding: 0` and `margin: 0`, so the CVE
ID heading, badges, and CWE tags sat flush against the card's top and left edges with zero
breathing room. The list view never had this problem because its cards use
`.cve-card-header` (which does carry `padding: 20px 24px`); the detail view's content never
went through that class.

Fix: `.detail-header` gets `padding: 20px 24px 0`; `.risk-badge-row` and `.cwe-tags-row`
each get `padding: 0 24px` so they line up with the header above and `.section-body` below
(which already had 24px horizontal padding). `.detail-divider`'s full-bleed edge-to-edge
line was left as-is -- not part of the reported problem.

Verified with a screenshot (clear gap above "CVE-2026-12299" now, badges/CWE tags aligned
with the sections below) and by re-running both the scroll-reset and the branding/sort
regression suites (30 checks total) -- all still pass.

## Recent change (2026-08-12, scroll-reset fix)

Tenth dashboard pass the same day. Reported symptom: "the CVE name is almost out of the
tab" on the Explain view. Root cause wasn't padding -- list-view and detail-view are the
same long page with one hidden via `style.display`, so switching between them never
changes the browser's scroll position. If you'd scrolled down at all on the list (easy to
do -- the table sits below the chart, filters, and now the header banner) before clicking
Explain, the detail view opened already scrolled past its own CVE-ID heading. Reproduced
directly: scrolling 900px down the list before clicking Explain left the CVE ID, badges,
and "What is vulnerable" heading entirely off-screen above the viewport.

Fix: `app.py` adds a `scroll-reset-store` (`dcc.Store`) and one `app.clientside_callback`
that runs `window.scrollTo(0, 0)` on every change to `selected-cve-store` -- covers both
directions (opening a CVE from a scrolled list, and returning to a scrolled detail view via
Back to list). No server round-trip, a few lines of plain JS.

Verified with Playwright: reproduced the bug first (confirmed CVE ID landed off-screen with
no fix), then confirmed scrollY resets to 0 in both directions and the CVE ID renders fully
visible with normal spacing below the header regardless of prior scroll position; regression
checked that navigating without any prior scroll still works normally.

## Recent change (2026-08-12, logo redesign)

Ninth dashboard pass the same day. Feedback on the previous pass's "CT" letter badge: too
simple, and the header placement should feel more designed. Replaced it with a real vector
mark -- a rounded-square badge with a teal-to-accent-blue gradient, a white shield
silhouette, and two two-tone horizontal swap arrows nested inside (a "translate" motif to
match the CVETranslate name), built from a reference concept image the user supplied.

`app.py`: consolidated the old separate favicon SVG and text-div logo into one shared
`_LOGO_SVG`/`LOGO_DATA_URI` -- `build_logo()` now renders `html.Img(src=LOGO_DATA_URI)`
(this Dash version's `html` module has no native `Svg`/`Rect`/`Path` tags, so the badge is
a genuine embedded vector image rather than CSS-approximated), and the favicon points at
the identical asset so the two can't drift apart. `app.index_string` also now loads Poppins
(700 weight) from Google Fonts for the wordmark.

`assets/style.css`: `.app-header` now gets the same card treatment as every other section
(`.cve-card`'s background/border/radius/shadow) instead of sitting bare on the page
background; `.app-logo-badge` sized up slightly (40px -> 44px) for the more detailed mark;
`.app-title` switched to Poppins and `var(--accent)` (was near-black system font), matching
the reference image's bold blue wordmark while staying inside the existing palette.

Verified with Playwright: logo renders as an `<img>` with the new SVG (screenshot-confirmed
gradient/shield/arrows), computed `font-family` on `.app-title` resolves to Poppins, header
reads as a bordered/shadowed banner at both desktop and 390px mobile widths. Re-ran the
prior pass's 22-check regression suite (sort control, filters, detail view, exports) --
all still pass; needed one viewport-height fix in the test harness itself (the taller
header pushed the sort dropdown's popup down into Dash's dev-mode debug bar in the old
1000px-tall test viewport -- not an app bug, bumped the test to 1300px).

## Recent change (2026-08-12, branding + onboarding header + sort control)

Eighth dashboard pass the same day, prompted by a live usability review (Nielsen-style
walkthrough of the running app) that flagged two gaps: the dashboard had no page identity
at all (opened directly on a bar chart, no name/header/explanation for a first-time user),
and the vulnerability list had no way to sort by severity or CVSS despite those being the
axes the thesis frames as interesting.

Tool named **CVETranslate** (checked via web search -- no existing tool with that name),
with a small "CT" monogram badge as its mark. `app.py`: new `build_logo()`/`build_header()`
render a header (badge + wordmark + one-line tagline) as the first child of the page
container, so it's visible on both list and detail views; `app.title` updated and a new
`app.index_string` adds a data-URI SVG favicon of the same badge (Dash's `html` module in
this version has no native `Svg`/`Rect`/`Text` tags, so the header badge is a plain CSS div
and the favicon is the one place an actual SVG string is used, for the browser tab icon).

New "Sort by" dropdown next to the search bar (`SORT_OPTIONS`, `apply_sort()`): Newest
first (default, byte-for-byte the old always-on behavior), Oldest first, Severity:
Critical -> Low, CVSS score: High -> Low (EPSS deliberately excluded, per direction).
`compute_filtered_results()` gained a `sort_by` param -- an explicit non-default sort
overrides search relevance ordering; the default leaves search and filter-only behavior
unchanged. Wired through `render_list`, `export_csv`, and `export_json` so CSV/JSON exports
honor the active sort too.

Filter visibility was also reviewed (12 total controls felt heavy for a non-security
audience) but the user's chosen option -- keep the front row visible, keep the existing
"More filters" collapse for the other 8 -- turned out to already match today's layout, so
no filter code changed.

Verified with a 22-check Playwright smoke test (header/title/favicon present, each sort
option actually reorders the list including a CVSS-descending and oldest-first check, sort
composes correctly with an active search, existing filters/pagination/export/detail-view
navigation still work, header holds up at a 390px mobile viewport, no console errors) --
all passed. Screenshots confirm the header reads cleanly at both desktop and mobile widths.

## Recent change (2026-08-12, CWE details toggle)

Seventh dashboard pass the same day. `app.py`, `assets/style.css`,
`src/backfill_cwe.py`, new `src/add_cwe_descriptions.py`.

The CWE tags/tooltips added so far give an id and a name (short, then full
on hover) but never explain what the weakness category actually *means*.
MITRE's own catalog carries a `Description` field per weakness -- a
genuine, factual paragraph (confirmed non-trivial length across several
samples: CWE-79, CWE-89, CWE-917, CWE-288, CWE-612, all 120-450 chars),
free to fetch via the same catalog download already used for names, no LLM
cost. Confirmed with the user this should be a new disclosure toggle
matching the existing "Show original NVD description"/"Show technical
details"/"Show references" pattern, not a real tab-bar restructuring of
the detail view (the word "tab" was being used loosely).

`backfill_cwe.py`'s catalog-download-and-parse step was extracted into a
shared `_fetch_cwe_catalog_root()` (existing `fetch_cwe_catalog_names()`
behavior unchanged) so a new `fetch_cwe_catalog_descriptions()` can reuse
it. New `src/add_cwe_descriptions.py` -- third script in this family after
`backfill_cwe.py` and `add_cwe_full_names.py`, same shape: load the
existing corpus, one MITRE catalog fetch (no NVD re-fetch, CWE assignments
are already correct), add `record["cwe"][i]["description"]`, verify
record-count/ID-set parity, back up (`.bak3`) and swap in. Ran for real:
**10,917/11,976 records updated** (same coverage as the earlier CWE
backfills), 14 CWE IDs with no catalog description (same deprecated/
withdrawn set already flagged, e.g. `CWE-264`, `CWE-19`).

New `build_cwe_details()` in `app.py`: one heading+description block per
attached CWE, behind a `show-cwe-details-btn`/`cwe-details-collapse` pair
placed between the raw-NVD-description toggle and the technical-details
toggle. Same shape as `build_references()` for CVEs with none -- the
toggle button is omitted *entirely*, not left showing empty content, for
the ~8.8% of CVEs with no CWE. New `toggle_cwe_details` callback, same
mount-guard (`if not n_clicks`) as the three existing toggle callbacks.

Verified with a Playwright smoke test (15 checks, all passing) against a
live `python app.py`: toggle collapsed by default, expands with correct
per-CWE heading+description (spot-checked CWE-288 and CWE-917, both
substantial non-placeholder text); toggle absent entirely (not empty) on a
confirmed no-CWE CVE (`CVE-2020-16139`); no state leak between this and
the other three toggles; fresh CVE selection after Back-to-list confirmed
collapsed (no phantom auto-expand, the same mount-guard regression class
already fixed twice this project); no console errors.

## Recent change (2026-08-12, tooltip fixes)

Sixth dashboard pass the same day -- two small bug fixes from continued
review. `app.py`, `assets/style.css`, new `src/add_cwe_full_names.py`.

1. **Tooltip clipping fixed.** The `[data-tooltip]` hover tooltips (KEV/
   EPSS/CVSS badges, now also CWE chips) opened *upward* (`bottom: 125%`)
   -- fine everywhere except the detail view, where the risk badges sit
   close enough to the top of `.cve-card` that the tooltip's own top edge
   landed above the card's top edge and got clipped by the card's
   `overflow: hidden`. Confirmed via computed-style measurement before
   fixing, not just eyeballed (tooltip top at viewport y=63 vs. the card's
   own top edge at y=74). Flipped to open downward (`top: 125%`) instead --
   there's always room below since every badge has page content under it.
2. **CWE names were being silently truncated at the data level, not just
   visually.** `backfill_cwe.py`'s `short_name()` cuts long names to ~60
   chars for the compact chip display (by design, for the chips) -- but
   the *full* name was never persisted anywhere, so there was nothing to
   show on hover for the truncated ones. New `src/add_cwe_full_names.py`
   re-fetches only the MITRE catalog (not NVD's yearly feeds again -- CWE
   *assignments* were already correct, this only needed the name lookup)
   and adds a `full_name` field per CWE entry; same integrity-check/backup
   discipline as `backfill_cwe.py`. `build_cwe_tags()` (detail view) and
   `build_tags()` (list view) both now carry `data-tooltip` with the full
   name on each CWE chip, reusing the just-fixed tooltip mechanism.

Verified against a live `python app.py`: tooltip's rendered position
confirmed below the card's top edge via `getBoundingClientRect`/computed-
style math, not just a screenshot; CWE full-name backfill confirmed via a
genuinely-truncated real example (`CVE-2020-9297`'s CWE-917, chip shows
"Expression Language Injection", tooltip shows the full "Improper
Neutralization of Special Elements used in an Expression Language
Statement ('Expression Language Injection')"); corpus record count and ID
set confirmed unchanged (11,976) after the full-name backfill; no console
errors.

**Addendum:** list-view table column order swapped so CVE ID leads
(CVE ID | Severity | Tags | Explain, was Severity | CVE ID | Tags |
Explain) -- `build_row()`/`build_list()`, `app.py`. Class-based CSS
(`.col-severity`/`.col-cve-id`), not position-based, so no styling broke;
the selected-row left accent bar (`:first-child`) automatically follows
the new first column.

## Recent change (2026-08-12, review fixes)

Fifth dashboard pass the same day -- four fixes from reviewing the feature
consolidation pass live, all refinements not new features. `app.py`,
`assets/style.css`.

1. **Chart tabs repositioned.** Were squeezed into a `width=4` side column
   next to the "Distribution" title/subtitle; now sit in their own
   full-width row below the subtitle, as expected. Same `chart-dimension-dropdown`
   id, so `render_list`'s wiring needed zero changes -- only the layout
   nesting changed.
2. **KEV-only and CWE promoted to the always-visible front filter row.**
   Front row is now Severity | Attack vector | Published | CWE, plus a
   second always-visible row for the KEV-only checkbox and the "More
   filters" toggle. Confirmed with the user which two to promote (Attack
   complexity was offered but not picked). The two components were moved,
   not duplicated -- component ids are unique across the layout, verified
   via grep before testing. "More filters" keeps Privileges/User
   interaction/OS/Vendor, Attack complexity/CIA impact, and Recency
   (renamed "Published within" to disambiguate from the front-row
   "Published" year dropdown, now that both are visible at once).
3. **Fixed a real indentation bug**, not cosmetic-only: `.similar-cves-section`
   had its own 24px horizontal padding stacking on top of `.section-heading`'s
   own 24px margin (58px total), while every other section heading
   ("What is vulnerable" etc.) has no such wrapping padding at all (34px).
   Removed the section's own padding and moved the card row's alignment to
   its own margin instead, mirroring how `.section-body` already handles
   this independently of the heading for `build_section()`'s sections.
   Verified via bounding-box comparison, not eyeballed -- both headings now
   sit at the identical pixel x-position.
4. **CWE now explicitly visible on the detail view without expanding
   anything.** New `build_cwe_tags()`, placed right after the risk badges,
   shows the full `"CWE-79 — Cross-Site Scripting"` (id + name, unlike the
   space-constrained list-row tags which show only the name) using the
   same `.tag-chip.tag-chip-cwe` style already established. The collapsed
   technical-details table's own CWE column is untouched, kept as the
   complete reference; this is the always-visible summary of the same
   data. CVEs with no CWE render nothing extra in that spot (no empty
   "CWE:" label).

Verified with a Playwright smoke test (27 checks, all passing) against a
live `python app.py`: tabs row confirmed below the subtitle via bounding-box
y-comparison, not just visually; CWE and KEV-only filters confirmed absent
from inside `#more-filters-collapse` and present/functional from their new
front-row position (KEV-only narrows to exactly 53, matching the known KEV
count); "More filters" still opens/closes correctly with its smaller
remaining field set, no duplicate-id errors on load; CWE tags row confirmed
visible pre-toggle showing the full id+name format; the indentation fix
confirmed via exact pixel-x equality between the "What is vulnerable" and
"Similar vulnerabilities" headings (and their content rows); no console
errors.

## Recent change (2026-08-12, feature consolidation pass)

Fourth dashboard pass the same day -- the largest so far, consolidating a
long discussion into one build: CWE data, a table-based list with tag
chips, tabs, a hover preview, seven new filters, two "context-awareness"
features grounded directly in the thesis's own literature review, and a
risk-matrix removal. `app.py`, `assets/style.css`, `src/dashboard_data.py`,
new `src/backfill_cwe.py`.

1. **CWE backfill.** NVD's `weaknesses` field was never retained by the
   original ingestion (`clean_cve()` in `notebooks/CVE Pipeline - JSON
   Pull.ipynb` drops it, and no raw pre-clean data survives on disk --
   confirmed, not assumed). New `src/backfill_cwe.py` re-fetches NVD's
   yearly JSON feed (same URLs/years as the original pipeline, bulk
   download, no rate limiting), extracts real `CWE-\d+` values (dropping
   NVD's own `NVD-CWE-Other`/`NVD-CWE-noinfo` placeholders), and joins them
   onto `data/rag_corpus_final.jsonl` by CVE ID -- verified identical
   record count and ID set before swapping the file in, original kept as
   `.bak`. Also resolves each CWE ID to a short human-readable name via
   MITRE's public CWE catalog (`cwec_latest.xml.zip`, ~1,400 entries,
   fetched once) -- a bare "CWE-79" is unexplained jargon; "Cross-site
   Scripting" serves the comprehension mission the bare code doesn't.
   Names are embedded per-record (`record["cwe"] = [{"id":..., "name":...}]`)
   rather than kept in a side-file the dashboard would need to stay in sync
   with. Result: **10,917/11,976 records (91.2%) now carry at least one
   real CWE**; a `data/cwe_names.json` reference table was also written for
   methodology documentation. Ran for real, not simulated -- output
   captured in this session's transcript.
2. **Seven new filters** (`dashboard_data.py`): CWE (membership filter,
   since it's a per-record list), Attack complexity, Confidentiality/
   Integrity/Availability impact (three separate filters), a KEV-only
   checkbox, and a Last-30/90-days recency filter. All land in the existing
   "More filters" collapse, which grows from 4 fields to 11.
3. **Risk matrix removed.** Reconsidered after shipping it last pass: it
   answers "where does risk concentrate across the corpus" -- a
   fleet-analyst question -- not "is this one CVE bad and what do I do,"
   which is what this tool's stated audience (developers, CS students) is
   actually asking. Cut rather than kept as unused density.
4. **On-screen list rebuilt as a real table** (`build_row`/`build_list`):
   Severity | CVE ID | Tags | Explain, replacing the card-row layout. The
   old plain-text product subtitle is now tag chips -- Vendor and Product
   as separate neutral chips (deduplicated when they're the same token,
   e.g. "Netty" not "Netty Netty"), plus up to 2 CWE-name chips with a
   "+N" overflow indicator, reusing the existing accent-blue chip style
   already used for the detail view's action cues. CSV and JSON exports
   both gained separate Vendor/Product columns, Affected Type (new
   `derive_affected_type()`, from the CPE `part` field: Application/
   Operating System/Hardware), and CWE IDs/names -- JSON keeps these as
   real arrays, CSV as comma-joined strings. A new "Export JSON" button
   sits next to the existing CSV one; both share `compute_filtered_results()`
   via a new `EXPORT_FILTER_STATES`/`_export_filtered_results()` pair so
   the two formats can't drift apart.
5. **Chart "Break down by" dropdown -> tabs.** Same component id, so the
   existing `render_list` wiring didn't need to change at all -- only the
   layout component swapped from `dcc.Dropdown` to `dcc.Tabs`.
6. **Hover preview on CVE ID.** Hovering a CVE ID in the list shows the
   risk badges and technical-context table instantly -- confirmed via a
   Playwright network listener that this fires zero API calls, since it's
   pure already-loaded record data. `build_technical_context_table()` was
   extracted out of `build_technical_context()` so the detail view's
   (still-collapsible) version and this new always-instant preview share
   one implementation, now including the CWE column. Implemented as a
   hidden sibling revealed via CSS `:hover` (not the `data-tooltip`
   mechanism from last pass, which only supports plain text via `attr()`
   -- this needed real HTML).
7. **Two context-awareness features**, deliberately grounded in specific
   passages from the thesis draft (Section 2.3's critique of Walkowski et
   al.'s asset-database dependency, and the security-champion paragraph's
   "transparent, contextually relevant, non-alarmist" framing) rather than
   generic additions:
   - **Similar vulnerabilities panel** -- genuinely free: the 5
     nearest-neighbour CVE IDs are already retrieved and cached per summary
     (`neighbours_used`, previously computed and discarded). Now rendered
     as always-visible, unprompted clickable cards after the 3-part
     summary (not behind a toggle -- proactive delivery without being
     searched for is what makes this "content context-awareness" rather
     than just another search feature). Clicking one navigates via the
     same pattern-matching mechanism as Explain buttons (`select_cve`
     extended to handle both `explain-btn` and `similar-cve-link` pattern
     types, same mount-guard).
   - **Corpus-relative CVSS framing** -- `CorpusStore.cvss_percentile()`
     (bisect over a precomputed sorted score list) added to the CVSS
     badge's hover tooltip, e.g. "More severe than 98% of tracked CVEs" --
     mirrors the EPSS badge's existing percentile language.
8. **Section headings more visible.** `.section-heading` (shared by the
   3-part summary, references, raw description, and the new similar-CVEs
   heading) bumped from 0.75rem muted grey to 0.9rem accent blue with a
   3px left-border bar -- kept the uppercase/letter-spacing deliberately,
   part of the calm/non-alarmist presentation the thesis argues for, not
   just left alone by default. `.filter-zone` got a 3px accent top border
   and slightly bolder filter labels for the same "more visible" ask.

One real data-quality nuance caught while widening the hover preview (not
by guessing): the technical-context table has 8 columns including the new
CWE one, and a 480px-wide hover popup made it wrap illegibly. Widened the
popup (`max-width: min(700px, 90vw)`) and added `overflow-x: auto` to
`.tech-table-wrap` (both the popup's and the detail view's) as a safety net
for narrower viewports.

Verified with a Playwright smoke test (30 checks, all passing) against a
live `python app.py`: table renders with the new 4 columns; a multi-CWE CVE
(`CVE-2024-21518`, 3 CWEs) shows exactly 2 name chips plus a "+1" overflow
chip; all 7 new filters present and narrow the list/stat cards correctly
(KEV-only alone narrows to 53, matching the known KEV count); risk-matrix
confirmed absent from the DOM; all 4 chart tabs present and switch the
chart correctly with selected-state styling; hovering a CVE ID shows the
preview with zero network calls to Anthropic; the Similar Vulnerabilities
section is present and un-toggled on a real cached CVE, its cards link to
real different CVEs, and clicking one correctly navigates to that CVE's
own detail view (not a stale one); the CVSS badge's tooltip contains
correct percentile language; CSV and JSON exports both carry the full
11,976-row corpus with the new Vendor/Product/Affected-type/CWE columns,
JSON's list fields confirmed as real arrays; no console errors.

**Deferred, discussed but explicitly not started this pass:** Hugging Face
hosting (paused mid-session at the user's request -- "more features need
to be added before we move to do that"; the previous session's Docker/
Spaces plan is not lost, just not executed).

## Recent change (2026-08-12, polish pass)

Third dashboard pass the same day. `app.py`, `assets/style.css`.

1. **Reliable hover tooltips.** The EPSS/KEV badge tooltips added in the
   previous pass used the native HTML `title` attribute, which reported as
   "absent" in practice -- browsers only show it after a ~1-1.5s hover
   delay, in a small low-contrast system box, easy to miss entirely.
   Replaced with a `data-tooltip` attribute + a pure-CSS `::after` hover
   tooltip (dark box, appears instantly, styled to match the app). No new
   dependency; `title=` dropped entirely rather than kept alongside the new
   mechanism.
2. **EPSS badge colored by its own risk band.** Previously flat grey
   regardless of the actual EPSS value. Now uses `epss_band()` (the same
   LOW/MEDIUM/HIGH classifier the chart's "Exploitation likelihood"
   dimension already uses) to pick `.severity-pill.epss-{low,medium,high}`.
   The chart's validated bar-fill ramp (`#86b6ef`/`#256abf`/`#0d366b`)
   turned out to fail WCAG text contrast at badge size (checked via the
   dataviz validator's `contrast()` export, not eyeballed -- e.g. `#86b6ef`
   is only 1.87:1 against a pale tint, well under the 4.5:1 floor for small
   text). Used three darker documented ramp steps instead
   (`#1c5cab`/`#184f95`/`#0d366b`) on a shared pale tint (`#cde2fb`),
   confirmed >=5:1 across all three bands. KEV's "No" badge stays neutral
   grey on purpose (deliberate contrast against the violet "Yes" state, not
   an oversight) -- confirmed with the user, left untouched.
3. **Page size 25 -> 10.** Raised once two new sections (below) started
   living under the list -- 25 rows pushed them too far down to reach
   without scrolling past a wall of rows. `PAGE_SIZE` is the only changed
   line; the pagination mechanics from the previous pass are unaffected.
4. **Severity x EPSS-band risk matrix**, new, below pagination. A 4x3 count
   table (`build_risk_matrix()`) reusing the same `epss_band()` classifier
   as the badge and chart -- one function, three consumers. Answers a
   different question than the single-dimension chart above it ("where
   does risk concentrate" vs. "what's the breakdown of one dimension"), and
   reuses a concept the thesis methodology already has (the severity x
   exploitability eval-sample grid, METHODOLOGY_LOG.md Section 6). Plain
   count table, no heatmap shading, consistent with this project's
   restraint-over-density stance. One real data-quality wrinkle caught by
   testing, not guessed: one corpus record (`CVE-2025-38553`) has no EPSS
   score (the ingestion's `-1.0` "missing" sentinel, METHODOLOGY_LOG.md),
   so `epss_band()` returns `None` for it and it's excluded from all 12
   cells -- consistent with that same record's EPSS badge already being
   omitted elsewhere, but previously silent. The matrix now surfaces the
   exclusion as a caption ("1 CVE excluded (no EPSS data available)")
   instead of letting the total quietly undercount by one.
5. **CSV export**, new, next to pagination. Extracted the filter/search
   logic at the top of `render_list` into a shared `compute_filtered_results()`
   so a new `export_csv` callback (triggered by a static "Export CSV"
   button, not rebuilt per render) can reuse it instead of duplicating it.
   Exports the full current filtered set via Python's stdlib `csv` module
   (no pandas -- not used elsewhere in this app), not just the visible
   page: CVE ID, Published, Severity, CVSS score, Attack vector, KEV
   listed, EPSS score, EPSS percentile, Product.

Verified with a Playwright smoke test (19 checks, all passing) against a
live `python app.py`: page size confirmed at 10 rows/~1,198 total pages for
the unfiltered corpus; the risk matrix's 12 cells plus its exclusion
caption account for all 11,976 CVEs, and a Severity=Critical filter reduces
it to only the Critical row populated, matching the stat card's count
exactly; CSV export downloads `cve_results.csv` with the correct header and
a row count matching the active filter (not the full corpus); the EPSS
badge switches between `epss-high`/`epss-low` classes correctly across two
different CVEs; both KEV and EPSS badges carry `data-tooltip` (not
`title`), and hovering measurably flips the `::after` pseudo-element's
computed opacity from 0 to 1 immediately, reverting on mouse-out; no
console errors.

## Recent change (2026-08-12, follow-up pass)

Second dashboard pass the same day, triggered by using the live app: a bug
report, three usability requests, and a mid-session ask for an interactive
chart. `app.py`, `assets/style.css`, `src/dashboard_generate.py`, new
`src/prime_dashboard_cache.py`.

1. **Search bar truncation fixed.** Root cause: `.search-row input` had no
   explicit `width`, relying entirely on Bootstrap's CDN-loaded
   `.form-control{width:100%}` rule (`dbc.themes.BOOTSTRAP` is a
   `cdn.jsdelivr.net` URL, not a bundled local file) -- when that fetch is
   slow/blocked the input silently falls back to the browser's ~20-character
   default width. Added an explicit `width:100%; box-sizing:border-box`
   rule so the input no longer depends on the CDN. Full CDN removal
   (vendoring Bootstrap locally) is deferred to the Hugging Face/offline
   work below, since that's the same fix needed there.
2. **KEV badge redesigned.** Previously omitted entirely when
   `kev_listed=False` (deliberately, to avoid noise on a 0.44%-KEV corpus).
   Now always renders "CISA KEV: Yes"/"No" -- violet for Yes (existing
   `.severity-pill.kev`), a new neutral `.severity-pill.neutral` for No --
   for consistency with the always-shown EPSS badge. Both the EPSS and KEV
   badges now carry a native HTML `title` tooltip spelling out the
   abbreviation on hover (zero JS/CSS dependency, works offline).
3. **Interactive severity-distribution chart.** A "Break down by" dropdown
   next to the chart (same visual pattern as the existing filter dropdowns)
   switches the list-view bar chart across 4 dimensions: Severity (existing
   default), Attack vector, Published year, and Exploitation likelihood
   (EPSS, binned Low `<1%` / Medium `1-50%` / High `>=50%` -- the 50% cutoff
   reuses the eval-sample methodology's existing "more likely than not"
   threshold, METHODOLOGY_LOG.md Section 6). Colors for the three new
   dimensions were chosen via the dataviz skill's validator (not
   eyeballed): Attack vector is a flat, uniform green (`#008300`, nominal
   categorical -- swapping bar order wouldn't change meaning, so hue
   doesn't need to carry per-bar identity); Year and EPSS band each use a
   validated 1-hue blue ordinal ramp (light->dark = earlier->later /
   lower->higher risk) -- the documented ramp's named steps don't have
   enough adjacent-lightness separation to support one distinct shade per
   year cleanly, so 7 years are bucket-mapped onto a validated 5-step
   subset rather than inventing new hex values. None of the new colors
   reuse a `SEVERITY_COLORS` hue, so a reader never reads "attack vector" or
   "year" as implying severity. The chart remains reactive to active
   filters (from the earlier pass today) and its subtitle now names the
   active dimension.
4. **Real pagination, replacing the flat 200-row cap.** The list previously
   sliced to the first 200 matching CVEs with a "narrow filters to see
   more" caption -- anything past row 200 was simply unreachable. Replaced
   with Previous/Next + "Page X of Y" (page size 25, chosen so a page is a
   short scan rather than a long scroll -- the same shape of problem STATUS.md
   already recorded once before, 2026-08-04's "10,000+ pixels down the
   page" bug, just smaller). Every filtered CVE is now reachable by paging;
   Previous/Next are static layout buttons (not rebuilt per-render), which
   deliberately avoids the mount-guard bug class already fixed twice this
   project (`select_cve` 2026-08-04, the three disclosure toggles earlier
   today). Page resets to 1 on a real filter/search change, but is
   preserved across an Explain/Back round trip and across a chart-dimension
   switch (neither changes which CVEs are in the list).
5. **Batch pre-cache script, `src/prime_dashboard_cache.py`.** Addresses
   dislike of the ~5-10s live "Explain" latency without paying for the full
   corpus. Extracted `SummaryGenerator._retrieve_neighbours` to a
   module-level `retrieve_neighbours()` (thin class wrapper preserved) so
   the live path and this new batch script share retrieval logic instead
   of duplicating it; same for cache load/write (`load_cache`/
   `write_cache`). Selects ~100 CVEs (all not-yet-cached KEV-listed
   records, up to a cap, plus a severity x EPSS-band stratified pull to
   fill the rest -- `random.seed(42)`), submits them as one Anthropic Batch
   API job (`client.messages.batches`, ~50% cheaper than live calls, no
   per-request latency pressure), and merges parsed results into the same
   `data/dashboard_summary_cache.json` the dashboard already reads --
   no dashboard code changes needed for pre-cached CVEs to take effect.
   Real per-CVE cost was measured (not guessed) via Anthropic's free
   token-counting endpoint against an actual dashboard prompt: ~4,311 input
   / ~528 output tokens/CVE; at Opus 4.6 pricing (~$5/$25 standard,
   ~$2.50/$12.50 via Batch API per third-party trackers) that's
   ~$0.017/CVE via Batch API, ~$1.74 for the ~100-CVE run. Full-corpus
   pre-cache (~11,969 remaining CVEs, ~$208 via Batch API) was explicitly
   discussed and deferred -- it's the offline/Hugging-Face use case, not
   this pass.

**Explicitly deferred, discussed but not built:** hosting on Hugging Face
with offline capability. Needs, on top of items 1 and 5 above: the
embedding model bundled for fully offline use (it already runs local per
METHODOLOGY_LOG.md Section 7, no change needed there), a decision on
full-corpus vs partial summary coverage for genuinely offline browsing, a
Docker-based HF Space (Dash has no native HF SDK), and a secrets story for
the Anthropic API key for any CVE that isn't pre-cached. Flagged as its own
future planning session, not started.

Verified with an extended Playwright smoke test (27 checks, all passing) run
against a live `python app.py`: search input spans ~94%+ of the filter-zone
width (previously ~200px fixed); pagination shows exactly 25 rows/page,
Previous/Next advance and disable correctly at the ends, changing a filter
resets to page 1, and the page number survives an Explain/Back round trip
to a different CVE (not a stale/reset page); all 4 chart dimensions render
correct bars/order/colors and the subtitle names the active dimension; a
live KEV CVE (`CVE-2024-27198`, real Anthropic call) shows 3 badges
including "CISA KEV: Yes" in violet with a hover tooltip spelling out the
abbreviation, and a cached non-KEV CVE (`CVE-2022-39180`) shows "CISA KEV:
No" in neutral styling (still 3 badges, not 2); the three disclosure
sections from the earlier pass today remain collapsed-by-default with no
regression from the pagination/chart changes; no unexpected console errors.

The ~100-CVE batch pre-cache job was run for real after this verification
(dry-run selection first confirmed 100 unique CVEs, 40 KEV-listed, a
reasonable severity/EPSS-band spread, zero overlap with the existing
cache). Batch id `msgbatch_016w119ubbLrv47gXPG5VWxu`: **100/100 succeeded, 0
failed**. `data/dashboard_summary_cache.json` grew from 8 to 108 entries.

## Recent change (2026-08-12)

Dashboard comprehension pass on `app.py`/`assets/style.css`, addressing three
gaps flagged against the thesis's own comprehension goal (visualisation
supports Level 1 perception well but Level 2 comprehension poorly per the
dissertation's literature review; the dashboard's job is closing that gap,
not adding SOC-analyst density):

1. **Risk badge row** -- CVSS score, KEV status, and EPSS score/percentile
   were fed to the LLM as generation input (`build_target_cve_block` in
   `src/dashboard_generate.py`) but never rendered anywhere in the UI. Added
   `build_risk_badges()`, rendered always-visible at the top of the detail
   view: a CVSS badge (reuses the existing locked severity-pill colors), a
   KEV badge shown only when `kev_listed=True` (53/11,976 records, 0.44% --
   a new violet color was introduced for this one case, since KEV is a
   distinct fact from severity and needed its own color, contrast-checked
   against white and its own tint background), and an EPSS badge (neutral
   styling, no color-coded threshold since none is validated in this
   project). Reuses `ordinal()` from `src/dashboard_generate.py` by import
   so the badge's percentile phrasing never diverges from the generated
   summary text.
2. **Progressive disclosure inside the detail view** -- the 7-column
   technical-context table and the references list were previously always
   fully expanded alongside the 3-part summary. Both are now collapsed by
   default behind "Show technical details ▾" / "Show references ▾" toggles,
   using the same interaction idiom as the pre-existing "More filters"
   collapse. A third, new toggle callback exists for each; all three carry
   the same `if not n_clicks: return False, ...` mount-guard as
   `toggle_more_filters`, because `detail-card-body` is rebuilt from scratch
   on every CVE selection and a freshly-mounted button reports
   `n_clicks=None` -- without the guard every new CVE would silently
   auto-expand all three sections on load (the same bug class already fixed
   for `select_cve` on 2026-08-04).
3. **Raw-NVD-vs-summary comparison view** -- the view named in CLAUDE.md's
   spec ("summary-vs-raw-NVD comparison view") and explicitly deferred when
   the dashboard was first built (2026-08-01) is now implemented: a "Show
   original NVD description ▾" toggle sits directly below the 3-part
   summary (collapsed by default, same idiom as above) and reveals
   `record["description"]` verbatim in a visually distinct tinted/bordered
   block, so a reader can verify the summary against its source without
   losing the summary from view. No changes to `src/dashboard_generate.py`,
   the frozen prompt, or ChromaDB -- the raw description was already loaded
   in memory via `CorpusStore`.

Small independent addendum: the severity-distribution bar chart (list view)
was static (always the full 11,976-CVE corpus, regardless of active
filters). It now takes `records` as a parameter and is re-rendered by the
existing `render_list` callback (two extra `Output`s, no new callback), with
its subtitle switching between "N CVEs across the full corpus" and "N CVEs
matching current filters."

`app.py` also gained `suppress_callback_exceptions=True` on the `dash.Dash`
constructor, required because the three new toggle/collapse pairs are
created dynamically inside `detail-card-body` rather than existing in the
initial server-rendered layout.

Verified with a Playwright smoke test (30 checks, all passing): initial
list-view load unaffected; filtering to Severity=Critical re-renders the
chart to the filtered count/subtitle and reverts on clearing; a live KEV CVE
(`CVE-2024-27198`, generated fresh via the Anthropic API) shows all 3 badges
with correct copy/styling; a cached non-KEV CVE (`CVE-2022-39180`) shows
exactly 2 badges with the KEV badge element absent from the DOM entirely
(not just hidden); all three new sections render collapsed by default and
expand/collapse correctly on click with unchanged inner content; going back
to the list and Explaining a different CVE confirms no leaked expand state
and no phantom auto-expand (the mount-guard regression check); the existing
golden path (`scrollY===0` on Explain, list hidden, Back to list restores
filter state, no auto-navigation on list re-render) is unaffected by
`suppress_callback_exceptions=True`; no console errors or Dash debug-overlay
appearances beyond the known harmless dash-version.plotly.com CORS warning.

**Next task:** none of this changes Stage 8 (human comprehension study),
which remains complete at pilot scale (`HUMAN_STUDY_18P_FINDINGS.md`) and
was run against static Qualtrics stimuli, not the live dashboard -- so this
pass has no existing participant feedback to validate against; noted as a
gap for any future dashboard-based study. **Correction (2026-08-13):** the
vendor/OS dropdown was previously described here as "~3,600 / ~10,000
unvirtualized alphabetical values." Measured directly against the running
app with Playwright (opening the dropdown, wheel-scrolling it, and typing
into it): only ~7 DOM option nodes render at a time regardless of the
10,239/3,569 underlying option count, and scrolling swaps which rows are
rendered -- this is a genuinely virtualised, windowed list, not a DOM
dump, and typing to search works correctly. There is no confirmed
performance/usability bug here; this note was stale or never verified.


## Recent change (2026-08-04)

Fixed two dashboard bugs the user hit in real use, plus added a chart:

1. **"Explain does nothing."** Root cause: the layout stacked the detail card
   after the full (up to 200-row) vulnerability list, so the detail view
   rendered ~10,000+ pixels down the page -- it worked, but nobody would
   scroll that far to see it. Fixed by restructuring `app.py` into a
   `list-view` / `detail-view` toggle: clicking "Explain" now swaps the whole
   page to the detail card at the top (with a "← Back to list" control),
   instead of appending it below the list. Filter state is preserved across
   the round trip since the filter dropdowns are separate components untouched
   by the swap.
2. **A real second bug surfaced while fixing the first one and was fixed
   too**: the pattern-matching `select_cve` callback
   (`Input({"type": "explain-btn", "index": ALL}, "n_clicks")`) was firing
   every time the Explain buttons were freshly mounted (page load, or any
   filter change re-rendering the list) -- not just on an actual click --
   because a newly-mounted button's `n_clicks` is `None`/`0` and Dash still
   treats its appearance as a triggering input. This silently auto-selected
   the first row's CVE (and fired a live Anthropic call for it) on every list
   re-render. It was invisible before bug 1's fix because the detail card was
   buried off-screen; fixing bug 1 made it immediately visible as an
   unwanted auto-navigation into detail view on page load. Fixed by checking
   `ctx.triggered[0]["value"]` is truthy before treating a pattern-matching
   trigger as a real click.
3. **"Renders like a mobile view."** `assets/style.css`'s `.page-container`
   was hard-capped at `max-width: 900px`; widened to `1280px`.
4. **Added a severity-distribution bar chart** above the Vulnerabilities card
   (`build_overview_chart()` in `app.py`, Critical/High/Medium/Low counts
   over the full 11,976-CVE corpus, computed once at startup, colors matched
   to the existing severity-pill CSS variables). Consulted the dataviz skill
   before building it; the existing pill colors (locked by the original task
   spec -- Critical red, High amber, Medium slate-blue, Low grey) fail the
   skill's categorical-palette validator on two checks (chroma floor on
   medium/low, and a hard-fail normal-vision floor between medium and low).
   Kept the colors anyway for visual consistency with the pills rather than
   introducing a fifth, better-validated but inconsistent palette, since
   every bar also carries a text axis label and a direct value label, so
   identity is never carried by hue alone -- flagging this tradeoff rather
   than silently shipping it.

Verified with a Playwright smoke test: chart renders with correct counts
summing to 11,976; clicking Explain swaps views with zero scroll
(`window.scrollY === 0` immediately after) and hides the list; "Back to
list" restores the list with filter state intact; selecting a second CVE
after going back correctly shows *that* CVE's detail, not a stale one. No
console errors besides a harmless Dash version-check CORS warning.

## Recent change (2026-08-01)

Built the Plotly Dash dashboard (Stage 7). New files: `app.py` (repo root --
layout + callbacks, run with `python app.py`, serves on
`http://127.0.0.1:8050`), `src/dashboard_data.py` (loads
`data/rag_corpus_final.jsonl`, 11,976 CVEs, once at startup; derives
UI-only display fields -- `product_subtitle`, primary `vendor`, `os_options`,
`year` -- from each record's CPE data; exposes filter option lists and a
plain equality `filter_corpus()`), `src/dashboard_search.py` (free-text /
CVE-ID search: exact CVE-ID lookup, else embeds the query with the same
`all-MiniLM-L6-v2` model and queries the existing persistent `rag_corpus`
ChromaDB collection read-only, top 20 by distance), `src/dashboard_generate.py`
(on-demand PERSONA summary generation for whichever CVE the user clicks
"Explain" on: retrieves top-5 neighbours from `rag_corpus`, builds the same
target/neighbour text blocks as `src/generate_summaries.py`, substitutes them
into the **unmodified** `v2_bullet/prompts/prompt-persona_v2.txt`, calls
`claude-opus-4-6` at temperature 0, parses the bullet-format output into
three sections + references, and caches the parsed result to
`data/dashboard_summary_cache.json` so repeat clicks and app restarts don't
re-call the API). `assets/style.css` implements the light-theme visual
design from `mock-ups/`.

Scope decision (confirmed with the user before building): the dashboard
browses and explains **any of the 11,976 corpus CVEs**, not just the 24
pre-generated eval-sample CVEs -- summaries are generated live on first
click and cached thereafter. A free-text/semantic search box was added even
though it isn't in the mockups (the mockups only show the dropdown filters).
A raw-NVD side-by-side comparison view was explicitly deferred, not built.

No prompt files, embeddings, or the `chroma_db` collection were modified --
`src/dashboard_generate.py` reads the frozen persona prompt file as-is and
duplicates (rather than imports) the small target/neighbour block builders
from `src/generate_summaries.py` so that frozen thesis-evaluation script
stays untouched. `requirements.txt` gained `dash` and
`dash-bootstrap-components` (the only two packages missing for this stage).

Verified end-to-end with a headless-browser (Playwright) smoke test against
the running app: initial unfiltered load (11,976 tracked, no stat cards,
list capped at 200 rows with a "showing N of M" caption); applying Severity
= Critical (stat cards appear with correct matching/critical/KEV counts);
"More filters" expand/collapse; clicking "Explain" on an uncached CVE
(live Anthropic call, ~5-10s, renders three bullet sections, a role-based
"Code fix"/"Config change" cue, the technical context table, and working
reference links with the "not re-verified since ingestion" caption); the
clicked row got the left accent bar + highlight; repeat "Explain" clicks on
other rows hit the cache correctly (`data/dashboard_summary_cache.json`);
the search box combined with an active severity filter correctly returned
the intersection, ranked by semantic relevance. No console errors other
than a harmless Dash version-check CORS warning (network telemetry Dash
itself makes, unrelated to this app).

**Next task:** the questionnaire-based human evaluation (Stage 8) is still
not started. A raw-NVD comparison view was a candidate follow-up here; see
the 2026-08-13 dashboard-usability entry below for what was actually built
instead (a disclosure toggle, not a comparison view) and why. The
large-vendor/OS dropdown usability concern noted here turned out, on direct
measurement (2026-08-13 entry below), not to be a confirmed bug -- see that
entry rather than this one.

**Next task (superseded, see the 2026-08-01 note above):** the dashboard has
since been built; the questionnaire-based human evaluation (Stage 8) is the
remaining item.

