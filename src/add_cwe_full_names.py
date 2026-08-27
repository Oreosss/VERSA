"""Add the full (untruncated) MITRE CWE name to each corpus record's CWE
entries, alongside the short display name backfill_cwe.py already added.

The CWE tag chips in the UI show the short name (backfill_cwe.py's
short_name(), either the parenthetical common name or the first ~60 chars
of the full one) -- that's still what's displayed. This adds a "full_name"
field so a hover tooltip can show the complete, untruncated official name
for the ones that got cut off.

Deliberately doesn't touch CWE *assignments* (which CVE has which CWE) --
those are already correct in the corpus from backfill_cwe.py, and getting
them required re-fetching NVD's yearly feeds. This only needs the much
smaller MITRE catalog re-fetch (reuses backfill_cwe.fetch_cwe_catalog_names,
no NVD calls), so it doesn't repeat that work.

Run: python src/add_cwe_full_names.py
Safe to re-run: writes to a new file first, verifies record-count/ID-set
parity with the original before replacing it, and keeps a .bak.
"""

import json
from pathlib import Path

from backfill_cwe import fetch_cwe_catalog_names

CORPUS_PATH = Path("data/rag_corpus_final.jsonl")
OUTPUT_PATH = Path("data/rag_corpus_final_with_cwe_fullnames.jsonl")
BACKUP_PATH = Path("data/rag_corpus_final.jsonl.bak2")
CWE_NAMES_ARTIFACT_PATH = Path("data/cwe_names.json")


def main():
    print("Loading existing corpus...")
    records = []
    with open(CORPUS_PATH) as f:
        for line in f:
            records.append(json.loads(line))
    print(f"  {len(records):,} records loaded")

    print("Fetching MITRE CWE catalog for full names (no NVD re-fetch needed)...")
    catalog_names = fetch_cwe_catalog_names()

    updated = 0
    for r in records:
        cwe_list = r.get("cwe") or []
        if not cwe_list:
            continue
        for entry in cwe_list:
            entry["full_name"] = catalog_names.get(entry["id"], entry["name"])
        updated += 1
    print(f"  {updated:,} records had CWE entries updated with a full_name")

    original_ids = {r["id"] for r in records}
    with open(OUTPUT_PATH, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Verify integrity before touching the live file, same discipline as
    # backfill_cwe.py.
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

    # Refresh the reference artifact too (short + full name per CWE id).
    cwe_names_full = {}
    for r in new_records:
        for entry in r.get("cwe") or []:
            cwe_names_full[entry["id"]] = {
                "name": entry["name"],
                "full_name": entry.get("full_name", entry["name"]),
            }
    with open(CWE_NAMES_ARTIFACT_PATH, "w") as f:
        json.dump(cwe_names_full, f, indent=2, sort_keys=True)

    print(f"Done. Original corpus backed up to {BACKUP_PATH}")
    print(f"Reference table refreshed at {CWE_NAMES_ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
