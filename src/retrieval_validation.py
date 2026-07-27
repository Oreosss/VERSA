"""Stage 6a: retrieval validation.

Retrieval only -- does not touch prompts or generation. For each eval CVE,
retrieves its top-5 nearest neighbours from the RAG corpus and writes:

- retrieval_validation.json: machine-readable neighbour records + distances
- RETRIEVAL_VALIDATION.md: human working document for manual relevance review

The embedding model (all-MiniLM-L6-v2) is general-purpose, not
security-domain-tuned, so cosine distance here is a rough similarity signal,
not ground truth. The manual same-class judgement left blank in the Markdown
output carries real weight; a domain-tuned embedding model is a documented
limitation, not something addressed by this script.
"""

import json
import statistics
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

EVAL_SAMPLE_PATH = "data/eval_sample.jsonl"
DB_PATH = "data/chroma_db"
COLLECTION_NAME = "rag_corpus"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

JSON_OUT_PATH = "data/retrieval_validation.json"
MD_OUT_PATH = "RETRIEVAL_VALIDATION.md"
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"

REQUIRED_EVAL_FIELDS = {"id", "description", "cvss_severity"}


def load_eval_sample(path):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    if not records:
        raise SystemExit(f"STOP: {path} is empty.")
    missing = REQUIRED_EVAL_FIELDS - set(records[0].keys())
    if missing:
        raise SystemExit(
            f"STOP: eval sample is missing required fields {missing}. "
            f"Actual schema: {sorted(records[0].keys())}"
        )
    return records


def connect_corpus():
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as e:
        raise SystemExit(f"STOP: could not open collection '{COLLECTION_NAME}': {e}")
    return collection


def check_distinctness(eval_records, collection):
    eval_ids = [r["id"] for r in eval_records]
    existing = collection.get(ids=eval_ids)
    overlap = set(existing["ids"])
    return overlap


def run_retrieval(eval_records, collection, embedding_fn):
    results = []
    for rec in eval_records:
        query_embedding = embedding_fn([rec["description"]])
        res = collection.query(
            query_embeddings=query_embedding,
            n_results=TOP_K,
        )
        neighbours = []
        for i in range(len(res["ids"][0])):
            neighbours.append({
                "id": res["ids"][0][i],
                "distance": res["distances"][0][i],
                "cvss_severity": res["metadatas"][0][i].get("cvss_severity"),
                "description": res["documents"][0][i],
            })
        distances = [n["distance"] for n in neighbours]
        results.append({
            "eval_id": rec["id"],
            "eval_severity": rec["cvss_severity"],
            "eval_kev_listed": rec.get("kev_listed"),
            "eval_epss_score": rec.get("epss_score"),
            "eval_exploitability": rec.get("eval_exploitability"),
            "eval_cell": rec.get("eval_cell"),
            "eval_description": rec["description"],
            "neighbours": neighbours,
            "min_distance": min(distances),
            "mean_distance": statistics.mean(distances),
            "max_distance": max(distances),
        })
    return results


def percentile(values, pct):
    values = sorted(values)
    n = len(values)
    if n == 1:
        return values[0]
    k = (n - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, n - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def compute_cohort_stats(results):
    nearest_distances = [r["min_distance"] for r in results]
    return {
        "min": min(nearest_distances),
        "p25": percentile(nearest_distances, 25),
        "median": percentile(nearest_distances, 50),
        "p75": percentile(nearest_distances, 75),
        "max": max(nearest_distances),
    }


def coverage_grid(eval_records, corpus_severity_counts, corpus_total):
    # Grid is built only from severities actually present in the eval design
    # (eval_cell A-F). LOW is not part of the design and is deliberately
    # excluded here rather than reported as an "empty cell".
    exploitabilities = ["high", "low"]
    severities = sorted({rec["cvss_severity"] for rec in eval_records})
    grid = {sev: {exp: 0 for exp in exploitabilities} for sev in severities}
    for rec in eval_records:
        sev = rec["cvss_severity"]
        exp = rec.get("eval_exploitability", "unknown")
        grid[sev].setdefault(exp, 0)
        grid[sev][exp] += 1

    eval_severity_counts = {}
    for rec in eval_records:
        eval_severity_counts[rec["cvss_severity"]] = eval_severity_counts.get(rec["cvss_severity"], 0) + 1

    return grid, eval_severity_counts


def corpus_severity_breakdown(collection):
    total = collection.count()
    counts = {}
    batch_size = 1000
    offset = 0
    while offset < total:
        batch = collection.get(
            limit=batch_size,
            offset=offset,
            include=["metadatas"],
        )
        for m in batch["metadatas"]:
            sev = m.get("cvss_severity", "UNKNOWN")
            counts[sev] = counts.get(sev, 0) + 1
        offset += batch_size
    return counts, total


def write_json(results, cohort_stats, overlap, corpus_count, out_path):
    payload = {
        "collection_name": COLLECTION_NAME,
        "collection_count": corpus_count,
        "embedding_model": EMBEDDING_MODEL,
        "top_k": TOP_K,
        "distinctness_overlap": sorted(overlap),
        "cohort_nearest_neighbour_distance_stats": cohort_stats,
        "eval_cves": results,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)


def write_markdown(results, cohort_stats, overlap, corpus_count, eval_records,
                    corpus_sev_counts, corpus_total, grid, eval_sev_counts, out_path):
    weakly_represented = [r for r in results if r["min_distance"] > cohort_stats["p75"]]

    lines = []
    lines.append("# Retrieval Validation Log (Stage 6a)")
    lines.append("")
    lines.append("Retrieval-only validation. Does not assess prompts or generated summaries.")
    lines.append("")
    lines.append("## Interpretation (plain language)")
    lines.append("")
    if overlap:
        lines.append(f"**WARNING: {len(overlap)} eval CVE id(s) were found inside the corpus collection: "
                      f"{sorted(overlap)}. This breaks the eval/corpus distinctness requirement and "
                      "invalidates any grounding claims below until resolved.**")
    else:
        lines.append("Confirmed: none of the 24 eval CVE ids are present in the `rag_corpus` collection. "
                      "The eval sample and the retrieval corpus are strictly distinct.")
    lines.append("")
    lines.append(
        f"Nearest-neighbour distance across the 24 eval CVEs ranges from {cohort_stats['min']:.4f} "
        f"to {cohort_stats['max']:.4f} (median {cohort_stats['median']:.4f}, 75th percentile "
        f"{cohort_stats['p75']:.4f}). "
        f"{len(weakly_represented)} eval CVE(s) sit above the 75th percentile on nearest-neighbour "
        "distance and are flagged below as candidates for closer manual review -- this is a "
        "statistical prompt for attention, not a pass/fail judgement. Whether these CVEs are "
        "actually poorly grounded depends on the manual same-class relevance read in the per-CVE "
        "sections, not on distance alone."
    )
    if weakly_represented:
        lines.append("")
        lines.append("Flagged for review (nearest-neighbour distance above cohort 75th percentile):")
        for r in weakly_represented:
            lines.append(f"- {r['eval_id']} ({r['eval_severity']}, cell {r['eval_cell']}) "
                          f"-- nearest-neighbour distance {r['min_distance']:.4f}")
    lines.append("")
    lines.append(
        "Coverage is assessed against the severity x exploitability grid the eval sample was "
        "deliberately designed on, not against the corpus's severity proportions -- the eval "
        "sample is not meant to mirror the corpus, so proportional resemblance is not the test "
        "applied here. The grid populated below should be checked for empty or overloaded cells."
    )
    lines.append("")
    lines.append("This file presents evidence only. It does not compute or state an overall pass/fail "
                  "verdict for retrieval quality or eval sample quality -- that judgement is made by "
                  "the reviewer using the per-CVE manual relevance blanks below plus the coverage grid.")
    lines.append("")

    lines.append("## Setup checks")
    lines.append("")
    lines.append(f"- Eval sample: `{EVAL_SAMPLE_PATH}`, {len(eval_records)} records, fields confirmed "
                  f"(`id`, `description`, `cvss_severity`).")
    lines.append(f"- Corpus collection: `{COLLECTION_NAME}` at `{DB_PATH}`, {corpus_count} documents.")
    lines.append(f"- Distinctness: {'FAILED -- see warning above' if overlap else 'PASSED, 0 overlapping ids'}.")
    lines.append(f"- Embedding model: `{EMBEDDING_MODEL}` (matches corpus-build model in `src/chroma_ingest.py`). "
                  "General-purpose, not security-domain-tuned -- cosine distance is a rough signal, not "
                  "ground truth, which is why the manual same-class judgement below carries real weight.")
    lines.append("")

    lines.append("## Grounding: per-CVE detail and manual judgement")
    lines.append("")
    lines.append("Read the target description, read each neighbour's description, and record whether "
                  "they describe the same class of vulnerability. Descriptions are printed in full "
                  "(not truncated).")
    lines.append("")

    for r in results:
        lines.append(f"### {r['eval_id']}  [{r['eval_severity']}, cell {r['eval_cell']}, "
                      f"KEV={r['eval_kev_listed']}, EPSS={r['eval_epss_score']}]")
        lines.append("")
        lines.append(f"**TARGET:** {r['eval_description']}")
        lines.append("")
        lines.append(f"nearest-neighbour distance: {r['min_distance']:.4f}  |  "
                      f"mean top-5 distance: {r['mean_distance']:.4f}  |  "
                      f"max top-5 distance: {r['max_distance']:.4f}")
        lines.append("")
        for i, n in enumerate(r["neighbours"], start=1):
            lines.append(f"**Neighbour {i}**  |  dist {n['distance']:.4f}  |  {n['cvss_severity']}  |  "
                          f"corpus-id {n['id']}")
            lines.append("")
            lines.append(f"> {n['description']}")
            lines.append("")
        lines.append("MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)")
        lines.append("")
        lines.append("NOTES: ______________________")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Grounding summary table")
    lines.append("")
    lines.append("| Eval CVE | Severity | Cell | Nearest-neighbour dist | Mean top-5 dist | Max top-5 dist | Above cohort p75? |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        flag = "yes" if r["min_distance"] > cohort_stats["p75"] else ""
        lines.append(f"| {r['eval_id']} | {r['eval_severity']} | {r['eval_cell']} | "
                      f"{r['min_distance']:.4f} | {r['mean_distance']:.4f} | {r['max_distance']:.4f} | {flag} |")
    lines.append("")
    lines.append("**Cohort nearest-neighbour distance distribution (n=24):**")
    lines.append("")
    lines.append(f"min {cohort_stats['min']:.4f}  |  p25 {cohort_stats['p25']:.4f}  |  "
                  f"median {cohort_stats['median']:.4f}  |  p75 {cohort_stats['p75']:.4f}  |  "
                  f"max {cohort_stats['max']:.4f}")
    lines.append("")

    lines.append("## Coverage: eval sample across the severity x exploitability grid")
    lines.append("")
    lines.append("The eval sample was deliberately built to span this grid, not to mirror the corpus's "
                  "severity proportions. Coverage here means the grid cells are populated, not that the "
                  "sample resembles the corpus in shape.")
    lines.append("")
    lines.append("| Severity | low exploitability | high exploitability | total |")
    lines.append("|---|---|---|---|")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if sev not in grid:
            continue
        low = grid[sev].get("low", 0)
        high = grid[sev].get("high", 0)
        lines.append(f"| {sev} | {low} | {high} | {low + high} |")
    lines.append("")
    empty_cells = [f"{sev}/{exp}" for sev, exps in grid.items() for exp, n in exps.items() if n == 0]
    if empty_cells:
        lines.append(f"Empty cells: {', '.join(empty_cells)}.")
    else:
        lines.append("No empty cells in the populated severity bands.")
    lines.append("")

    lines.append("### Corpus severity breakdown (context only, not a coverage target)")
    lines.append("")
    lines.append("| Severity | Corpus count | Corpus % | Eval count | Eval % |")
    lines.append("|---|---|---|---|---|")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        c_count = corpus_sev_counts.get(sev, 0)
        e_count = eval_sev_counts.get(sev, 0)
        c_pct = 100 * c_count / corpus_total if corpus_total else 0
        e_pct = 100 * e_count / len(eval_records) if eval_records else 0
        lines.append(f"| {sev} | {c_count} | {c_pct:.1f}% | {e_count} | {e_pct:.1f}% |")
    lines.append("")
    lines.append("The eval sample's severity proportions are not expected to match the corpus's -- "
                  "the eval sample is a deliberate severity x exploitability grid, not a proportional "
                  "miniature of the corpus. A mismatch here is expected and by design, not a defect.")
    lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))


def append_methodology_log(overlap, corpus_count, results, cohort_stats, weakly_represented_count):
    from datetime import date
    entry = []
    entry.append("")
    entry.append(f"## Stage 6a -- Retrieval Validation ({date.today().isoformat()})")
    entry.append("")
    entry.append(f"**Script:** `src/retrieval_validation.py`")
    entry.append(f"**Outputs:** `data/retrieval_validation.json`, `RETRIEVAL_VALIDATION.md`")
    entry.append("")
    entry.append(f"Ran retrieval validation against the live `rag_corpus` ChromaDB collection "
                 f"({corpus_count} documents) using the 24-CVE eval sample (`data/eval_sample.jsonl`). "
                 f"For each eval CVE, retrieved top-{TOP_K} nearest neighbours by cosine distance using "
                 f"the same embedding model as corpus build (`{EMBEDDING_MODEL}`).")
    entry.append("")
    entry.append(f"- Distinctness check: {'FAILED, overlap = ' + str(sorted(overlap)) if overlap else 'passed, 0 of 24 eval ids found in corpus'}.")
    entry.append(f"- Cohort nearest-neighbour distance: min {cohort_stats['min']:.4f}, median "
                 f"{cohort_stats['median']:.4f}, p75 {cohort_stats['p75']:.4f}, max {cohort_stats['max']:.4f}.")
    entry.append(f"- {weakly_represented_count} eval CVE(s) flagged above cohort p75 nearest-neighbour "
                 "distance for manual review (statistical flag only, not a verdict).")
    entry.append("- Manual same-class relevance judgement per eval CVE left blank in "
                 "`RETRIEVAL_VALIDATION.md` for reviewer completion; grounding and eval-sample-quality "
                 "verdicts are deliberately not computed by the script.")
    entry.append("")

    with open(METHODOLOGY_LOG_PATH, "a") as f:
        f.write("\n".join(entry))


def main():
    print(f"Loading eval sample from {EVAL_SAMPLE_PATH}...")
    eval_records = load_eval_sample(EVAL_SAMPLE_PATH)
    print(f"Loaded {len(eval_records)} eval CVEs. Fields confirmed.")

    print(f"Connecting to ChromaDB collection '{COLLECTION_NAME}'...")
    collection = connect_corpus()
    corpus_count = collection.count()
    print(f"Collection count: {corpus_count}")

    print("Checking distinctness between eval sample and corpus...")
    overlap = check_distinctness(eval_records, collection)
    if overlap:
        print(f"WARNING: {len(overlap)} eval CVE ids found in corpus: {sorted(overlap)}")
    else:
        print("Distinctness confirmed: 0 overlapping ids.")

    print(f"Loading embedding model {EMBEDDING_MODEL}...")
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    print(f"Running retrieval (top {TOP_K}) for {len(eval_records)} eval CVEs...")
    results = run_retrieval(eval_records, collection, embedding_fn)

    cohort_stats = compute_cohort_stats(results)
    weakly_represented = [r for r in results if r["min_distance"] > cohort_stats["p75"]]

    print("Computing corpus severity breakdown...")
    corpus_sev_counts, corpus_total = corpus_severity_breakdown(collection)

    grid, eval_sev_counts = coverage_grid(eval_records, corpus_sev_counts, corpus_total)

    print(f"Writing {JSON_OUT_PATH}...")
    write_json(results, cohort_stats, overlap, corpus_count, JSON_OUT_PATH)

    print(f"Writing {MD_OUT_PATH}...")
    write_markdown(results, cohort_stats, overlap, corpus_count, eval_records,
                    corpus_sev_counts, corpus_total, grid, eval_sev_counts, MD_OUT_PATH)

    print(f"Appending entry to {METHODOLOGY_LOG_PATH}...")
    append_methodology_log(overlap, corpus_count, results, cohort_stats, len(weakly_represented))

    print("Done.")
    print(f"Weakly represented (above p75 nearest-neighbour distance): {len(weakly_represented)}")
    for r in weakly_represented:
        print(f"  {r['eval_id']} ({r['eval_severity']}) -- nearest dist {r['min_distance']:.4f}")


if __name__ == "__main__":
    main()
