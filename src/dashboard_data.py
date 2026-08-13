"""Loads the RAG corpus for the dashboard and derives UI-only display fields.

Reads data/rag_corpus_final.jsonl (11,976 records, the same corpus ingested
into ChromaDB by src/chroma_ingest.py) once at import time. Derived fields
(product_subtitle, os_options, vendor, year) are display heuristics computed
here in the UI layer from the CPE configurations already present in each
record; they are not sourced from the LLM and do not touch the corpus file,
embeddings, or prompts.
"""

import bisect
import json
from datetime import datetime, timedelta
from pathlib import Path

CORPUS_PATH = "data/rag_corpus_final.jsonl"

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
PRIVILEGES_ORDER = ["NONE", "LOW", "HIGH"]
USER_INTERACTION_ORDER = ["NONE", "REQUIRED"]
ATTACK_VECTOR_ORDER = ["NETWORK", "ADJACENT_NETWORK", "LOCAL", "PHYSICAL"]
ATTACK_COMPLEXITY_ORDER = ["LOW", "HIGH"]
IMPACT_ORDER = ["NONE", "LOW", "HIGH"]
AFFECTED_TYPE_LABELS = {"a": "Application", "o": "Operating System", "h": "Hardware"}


def _iter_cpe_matches(record):
    for cfg in record.get("configurations") or []:
        for node in cfg.get("nodes") or []:
            for match in node.get("cpeMatch") or []:
                yield match


def _humanize(token):
    return token.replace("_", " ").replace("-", " ").title()


def _version_fragment(match):
    parts = match["criteria"].split(":")
    version = parts[5] if len(parts) > 5 else "*"
    if version not in ("*", "-"):
        return version
    if match.get("versionEndIncluding"):
        return f"up to {match['versionEndIncluding']}"
    if match.get("versionEndExcluding"):
        return f"before {match['versionEndExcluding']}"
    if match.get("versionStartIncluding") and match.get("versionEndIncluding"):
        return f"{match['versionStartIncluding']}–{match['versionEndIncluding']}"
    return ""


def derive_product_subtitle(record):
    for match in _iter_cpe_matches(record):
        parts = match["criteria"].split(":")
        if len(parts) < 5:
            continue
        vendor, product = parts[3], parts[4]
        label = f"{_humanize(vendor)} {_humanize(product)}"
        version = _version_fragment(match)
        return f"{label} {version}".strip() if version else label
    return "Affected product not identified in CPE data"


def derive_primary_vendor(record):
    for match in _iter_cpe_matches(record):
        parts = match["criteria"].split(":")
        if len(parts) < 4:
            continue
        return parts[3]
    return None


def derive_primary_product(record):
    for match in _iter_cpe_matches(record):
        parts = match["criteria"].split(":")
        if len(parts) < 5:
            continue
        return parts[4]
    return None


def derive_os_options(record):
    options = set()
    for match in _iter_cpe_matches(record):
        parts = match["criteria"].split(":")
        if len(parts) < 5:
            continue
        part_type, vendor, product = parts[2], parts[3], parts[4]
        if part_type == "o":
            options.add(f"{_humanize(vendor)} {_humanize(product)}")
    return options


def derive_affected_type(record):
    for match in _iter_cpe_matches(record):
        parts = match["criteria"].split(":")
        if len(parts) < 3:
            continue
        return AFFECTED_TYPE_LABELS.get(parts[2], "Unknown")
    return "Unknown"


def _prepare_record(record):
    record = dict(record)
    record["product_subtitle"] = derive_product_subtitle(record)
    record["vendor"] = derive_primary_vendor(record)
    record["product"] = derive_primary_product(record)
    record["os_options"] = derive_os_options(record)
    record["affected_type"] = derive_affected_type(record)
    record["year"] = int(record["published"][:4])
    return record


def load_corpus(path=CORPUS_PATH):
    records = []
    with open(path) as f:
        for line in f:
            records.append(_prepare_record(json.loads(line)))
    return records


class CorpusStore:
    """In-memory corpus plus precomputed filter option lists, built once."""

    def __init__(self, path=CORPUS_PATH):
        self.records = load_corpus(path)
        self.by_id = {r["id"]: r for r in self.records}

        years = sorted({r["year"] for r in self.records}, reverse=True)
        vendors = sorted({r["vendor"] for r in self.records if r["vendor"]})
        os_values = sorted({o for r in self.records for o in r["os_options"]})

        cwe_names = {}
        for r in self.records:
            for c in r.get("cwe") or []:
                cwe_names[c["id"]] = c["name"]
        cwe_options = sorted(
            ({"id": cid, "name": name} for cid, name in cwe_names.items()),
            key=lambda c: int(c["id"].split("-")[1]),
        )

        def _present(order, field):
            return [v for v in order if any(r.get(field) == v for r in self.records)]

        self.filter_options = {
            "severity": _present(SEVERITY_ORDER, "cvss_severity"),
            "attack_vector": _present(ATTACK_VECTOR_ORDER, "attack_vector"),
            "attack_complexity": _present(ATTACK_COMPLEXITY_ORDER, "attack_complexity"),
            "confidentiality_impact": _present(IMPACT_ORDER, "confidentiality_impact"),
            "integrity_impact": _present(IMPACT_ORDER, "integrity_impact"),
            "availability_impact": _present(IMPACT_ORDER, "availability_impact"),
            "year": years,
            "privileges": _present(PRIVILEGES_ORDER, "privileges_required"),
            "user_interaction": _present(USER_INTERACTION_ORDER, "user_interaction"),
            "os": os_values,
            "vendor": vendors,
            "cwe": cwe_options,
        }

        scores = sorted(r["cvss_score"] for r in self.records if r.get("cvss_score") is not None)
        self._sorted_cvss_scores = scores

    def cvss_percentile(self, score):
        """Share of the corpus at or below this CVSS score, as a 0-100 int."""
        scores = self._sorted_cvss_scores
        if not scores or score is None:
            return None
        idx = bisect.bisect_right(scores, score)
        return round(idx / len(scores) * 100)

    def __len__(self):
        return len(self.records)

    def get(self, cve_id):
        return self.by_id.get(cve_id)


def filter_corpus(records, severity=None, attack_vector=None, year=None,
                   privileges=None, user_interaction=None, os=None, vendor=None,
                   cwe=None, attack_complexity=None, confidentiality_impact=None,
                   integrity_impact=None, availability_impact=None,
                   kev_only=False, recency_days=None):
    out = records
    if severity:
        out = [r for r in out if r["cvss_severity"] == severity]
    if attack_vector:
        out = [r for r in out if r.get("attack_vector") == attack_vector]
    if year:
        out = [r for r in out if r["year"] == int(year)]
    if privileges:
        out = [r for r in out if r.get("privileges_required") == privileges]
    if user_interaction:
        out = [r for r in out if r.get("user_interaction") == user_interaction]
    if os:
        out = [r for r in out if os in r["os_options"]]
    if vendor:
        out = [r for r in out if r["vendor"] == vendor]
    if cwe:
        out = [r for r in out if any(c["id"] == cwe for c in r.get("cwe") or [])]
    if attack_complexity:
        out = [r for r in out if r.get("attack_complexity") == attack_complexity]
    if confidentiality_impact:
        out = [r for r in out if r.get("confidentiality_impact") == confidentiality_impact]
    if integrity_impact:
        out = [r for r in out if r.get("integrity_impact") == integrity_impact]
    if availability_impact:
        out = [r for r in out if r.get("availability_impact") == availability_impact]
    if kev_only:
        out = [r for r in out if r.get("kev_listed")]
    if recency_days:
        cutoff = datetime.now() - timedelta(days=int(recency_days))
        out = [r for r in out if datetime.fromisoformat(r["published"]) >= cutoff]
    return out
