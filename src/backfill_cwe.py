"""One-time CWE backfill for the dashboard corpus.

NVD's `weaknesses` field (CWE assignments) was never retained by the original
ingestion pipeline's clean_cve() (notebooks/CVE Pipeline - JSON Pull.ipynb) --
confirmed no local raw data has it, so this re-fetches NVD's yearly JSON feed
(same URL pattern and years as the original pipeline) purely to extract CWE
IDs, joins them onto the existing data/rag_corpus_final.jsonl by CVE ID, and
also resolves each CWE ID to a short human-readable name via MITRE's public
CWE catalog -- a bare "CWE-79" is unexplained jargon; "CWE-79 -- Cross-Site
Scripting" actually serves comprehension.

Each record gains: record["cwe"] = [{"id": "CWE-79", "name": "Cross-Site
Scripting"}, ...] (empty list if NVD assigned none). Names are embedded
directly per record so the dashboard doesn't need a second file to stay in
sync with the corpus.

Run: python src/backfill_cwe.py
Safe to re-run: writes to a new file first, verifies record-count/ID-set
parity with the original before replacing it, and keeps a .bak.
"""

import gzip
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path

import requests

CORPUS_PATH = Path("data/rag_corpus_final.jsonl")
OUTPUT_PATH = Path("data/rag_corpus_final_with_cwe.jsonl")
BACKUP_PATH = Path("data/rag_corpus_final.jsonl.bak")
CWE_NAMES_ARTIFACT_PATH = Path("data/cwe_names.json")

NVD_URL_TEMPLATE = "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz"
YEARS = list(range(2020, 2027))  # 2020-2026, matches the original pipeline

CWE_CATALOG_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
CWE_ID_RE = re.compile(r"^CWE-\d+$")


def fetch_cwe_ids_for_year(year):
    """Download one year of the NVD feed, return {cve_id: [CWE-xxx, ...]}."""
    url = NVD_URL_TEMPLATE.format(year=year)
    print(f"  [{year}] downloading NVD feed...", end=" ", flush=True)
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        print(f"HTTP {r.status_code}, skipping")
        return {}
    data = json.loads(gzip.decompress(r.content))
    cves = data.get("vulnerabilities", [])
    print(f"{len(cves)} CVEs")

    out = {}
    for entry in cves:
        cve = entry.get("cve", {})
        cve_id = cve.get("id")
        if not cve_id:
            continue
        cwe_ids = set()
        for weakness in cve.get("weaknesses", []):
            for desc in weakness.get("description", []):
                if desc.get("lang") != "en":
                    continue
                value = desc.get("value", "")
                if CWE_ID_RE.match(value):
                    cwe_ids.add(value)
        if cwe_ids:
            out[cve_id] = sorted(cwe_ids, key=lambda c: int(c.split("-")[1]))
    return out


def fetch_all_cwe_ids():
    """{cve_id: [CWE-xxx, ...]} across all years, CVEs with no real CWE omitted."""
    index = {}
    for year in YEARS:
        index.update(fetch_cwe_ids_for_year(year))
    return index


CWE_NS = {"cwe": "http://cwe.mitre.org/cwe-7"}


def _fetch_cwe_catalog_root():
    """Download + parse MITRE's CWE catalog XML once; returns the root
    Element. Shared by fetch_cwe_catalog_names() and
    fetch_cwe_catalog_descriptions() so both reuse the same download/parse
    instead of each re-fetching the ~18MB catalog separately."""
    print("Downloading MITRE CWE catalog...", end=" ", flush=True)
    r = requests.get(CWE_CATALOG_URL, timeout=60)
    r.raise_for_status()
    z = zipfile.ZipFile(BytesIO(r.content))
    xml_name = next(n for n in z.namelist() if n.endswith(".xml"))
    xml_bytes = z.read(xml_name)
    print(f"{len(xml_bytes) / 1_000_000:.1f} MB catalog")

    import xml.etree.ElementTree as ET
    return ET.fromstring(xml_bytes)


def fetch_cwe_catalog_names():
    """{CWE-xxx: full MITRE Name} for the entire public catalog."""
    root = _fetch_cwe_catalog_root()
    names = {}
    for weakness in root.findall(".//cwe:Weakness", CWE_NS):
        wid = weakness.get("ID")
        name = weakness.get("Name")
        if wid and name:
            names[f"CWE-{wid}"] = name
    return names


def fetch_cwe_catalog_descriptions():
    """{CWE-xxx: plain-English Description} for the entire public catalog --
    what the weakness category actually means, not just its name."""
    root = _fetch_cwe_catalog_root()
    descriptions = {}
    for weakness in root.findall(".//cwe:Weakness", CWE_NS):
        wid = weakness.get("ID")
        desc_el = weakness.find("cwe:Description", CWE_NS)
        if wid and desc_el is not None and desc_el.text:
            descriptions[f"CWE-{wid}"] = " ".join(desc_el.text.split())
    return descriptions


def short_name(full_name):
    """Prefer the parenthetical common name MITRE includes for well-known
    CWEs (e.g. "...('Cross-site Scripting')" -> "Cross-Site Scripting"),
    else fall back to the full name, capped to a reasonable display length."""
    match = re.search(r"\(['\"]?([^()'\"]+)['\"]?\)\s*$", full_name)
    if match:
        return match.group(1).strip()
    return full_name if len(full_name) <= 60 else full_name[:57] + "..."


def main():
    print("Step 1/4: fetching CWE assignments from NVD's yearly feeds...")
    cwe_by_cve = fetch_all_cwe_ids()
    print(f"  {len(cwe_by_cve):,} CVEs (across all NVD years) have at least one real CWE.")

    print("\nStep 2/4: loading the existing corpus...")
    records = []
    with open(CORPUS_PATH) as f:
        for line in f:
            records.append(json.loads(line))
    print(f"  {len(records):,} records loaded from {CORPUS_PATH}")

    corpus_cwe_ids = set()
    for r in records:
        for cwe_id in cwe_by_cve.get(r["id"], []):
            corpus_cwe_ids.add(cwe_id)
    print(f"  {len(corpus_cwe_ids)} distinct CWE IDs actually present in this corpus.")

    print("\nStep 3/4: resolving CWE names from the MITRE catalog...")
    catalog_names = fetch_cwe_catalog_names()
    cwe_names = {}
    unresolved = []
    for cwe_id in corpus_cwe_ids:
        full = catalog_names.get(cwe_id)
        if full is None:
            unresolved.append(cwe_id)
            continue
        cwe_names[cwe_id] = short_name(full)
    if unresolved:
        print(f"  {len(unresolved)} CWE IDs not found in the current catalog "
              f"(deprecated/withdrawn IDs, kept as ID-only): {unresolved}")

    print("\nStep 4/4: writing the enriched corpus...")
    with_cwe_count = 0
    original_ids = {r["id"] for r in records}
    with open(OUTPUT_PATH, "w") as f:
        for r in records:
            cwe_ids = cwe_by_cve.get(r["id"], [])
            r["cwe"] = [
                {"id": cwe_id, "name": cwe_names.get(cwe_id, cwe_id)}
                for cwe_id in cwe_ids
            ]
            if r["cwe"]:
                with_cwe_count += 1
            f.write(json.dumps(r) + "\n")

    # Verify integrity before touching the live file: same records, same IDs,
    # only the new field differs.
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
    with open(CWE_NAMES_ARTIFACT_PATH, "w") as f:
        json.dump(cwe_names, f, indent=2, sort_keys=True)

    print(f"\nDone. {with_cwe_count:,}/{len(records):,} records "
          f"({with_cwe_count / len(records) * 100:.1f}%) now have at least one CWE.")
    print(f"Original corpus backed up to {BACKUP_PATH}")
    print(f"CWE name reference table (for methodology docs, not a runtime "
          f"dependency) written to {CWE_NAMES_ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
