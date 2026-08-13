"""Add a plain-English description to each corpus record's CWE entries --
what the MITRE weakness category actually means, not just its name.

The CWE tags/chips show an id + short name (e.g. "CWE-79 -- Cross-Site
Scripting"); the detail view's CWE tags carry the full name as a hover
tooltip (src/add_cwe_full_names.py). Neither explains what the weakness
category actually *is*. MITRE's own catalog carries a Description field per
weakness -- a genuine, factual paragraph, free to fetch (no LLM cost),
reusing the same catalog download already used for names.

Deliberately doesn't touch CWE *assignments* (which CVE has which CWE) --
those are already correct in the corpus, and getting them required
re-fetching NVD's yearly feeds. This only needs the much smaller MITRE
catalog re-fetch (reuses backfill_cwe.fetch_cwe_catalog_descriptions, no
NVD calls), so it doesn't repeat that work.

Run: python src/add_cwe_descriptions.py
Safe to re-run: writes to a new file first, verifies record-count/ID-set
parity with the original before replacing it, and keeps a .bak.
"""

import json
from pathlib import Path

from backfill_cwe import fetch_cwe_catalog_descriptions

CORPUS_PATH = Path("data/rag_corpus_final.jsonl")
OUTPUT_PATH = Path("data/rag_corpus_final_with_cwe_descriptions.jsonl")
BACKUP_PATH = Path("data/rag_corpus_final.jsonl.bak3")
CWE_NAMES_ARTIFACT_PATH = Path("data/cwe_names.json")


def main():
    print("Loading existing corpus...")
    records = []
    with open(CORPUS_PATH) as f:
        for line in f:
            records.append(json.loads(line))
    print(f"  {len(records):,} records loaded")

    print("Fetching MITRE CWE catalog for descriptions (no NVD re-fetch needed)...")
    catalog_descriptions = fetch_cwe_catalog_descriptions()

    updated = 0
    missing = set()
    for r in records:
        cwe_list = r.get("cwe") or []
        if not cwe_list:
            continue
        for entry in cwe_list:
            desc = catalog_descriptions.get(entry["id"])
            if desc is None:
                missing.add(entry["id"])
            entry["description"] = desc or "No description available for this CWE."
        updated += 1
    print(f"  {updated:,} records had CWE entries updated with a description")
    if missing:
        print(f"  {len(missing)} CWE IDs had no catalog description "
              f"(deprecated/withdrawn, same set backfill_cwe.py already flagged): {sorted(missing)}")

    original_ids = {r["id"] for r in records}
    with open(OUTPUT_PATH, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Verify integrity before touching the live file, same discipline as
    # backfill_cwe.py / add_cwe_full_names.py.
    new_records = []
    with open(OUTPUT_PATH) as f:
        for line in f:
            new_records.append(json.loads(line))
    new_ids = {r["id"] for r in new_records}
    assert len(new_records) == len(records), \
        f"record count changed: {len(records)} -> {len(new_records)}"
    assert new_ids == original_ids, "CVE ID set changed -- refusing to swap in"

    CORPUS_PATH.rename(BACKUP_PATH)
    OUTPUT_PATH.rename(CORPUS_PATH)

    # Refresh the reference artifact too (name + full_name + description per
    # CWE id), preserving whatever fields are already there.
    cwe_names_full = {}
    for r in new_records:
        for entry in r.get("cwe") or []:
            cwe_names_full[entry["id"]] = {
                "name": entry["name"],
                "full_name": entry.get("full_name", entry["name"]),
                "description": entry.get("description"),
            }
    with open(CWE_NAMES_ARTIFACT_PATH, "w") as f:
        json.dump(cwe_names_full, f, indent=2, sort_keys=True)

    print(f"Done. Original corpus backed up to {BACKUP_PATH}")
    print(f"Reference table refreshed at {CWE_NAMES_ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
