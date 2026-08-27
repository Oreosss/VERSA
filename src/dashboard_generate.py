"""On-demand PERSONA summary generation for the dashboard's "Explain" view.

Given a corpus record, retrieves top-5 neighbours from the existing
`rag_corpus` ChromaDB collection, substitutes them into the frozen,
unmodified `v2_bullet/prompts/prompt-persona_v2.txt` template (same prompt,
model, and temperature as the thesis's frozen generation script,
src/generate_summaries.py), and parses the bullet-format output into
sections + references for rendering.

This module is intentionally independent of src/generate_summaries.py (that
script is the frozen thesis-evaluation generation path for the 24 eval CVEs
and is left untouched) even though the target/neighbour block builders below
follow the same shape.

Results are cached to disk (data/dashboard_summary_cache.json) so repeat
"Explain" clicks and app restarts do not re-call the Anthropic API.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from anthropic import Anthropic

PROMPT_PATH = "v2_bullet/prompts/prompt-persona_v2.txt"
CACHE_PATH = "data/dashboard_summary_cache.json"

MODEL = "claude-opus-4-6"
TEMPERATURE = 0
MAX_TOKENS = 2048
TOP_K = 5
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0

# The frozen prompt asks for these four headings but doesn't require markdown
# "##" formatting, and in practice the model emits both a bare heading line
# and a "## "-prefixed one across different generations (confirmed by
# inspecting v2_bullet/summaries/summaries_bullet.json). Match either form.
HEADER_RE = re.compile(
    r"^(?:#{1,6}\s*)?(what is vulnerable|how it can be exploited|"
    r"what action to take|references?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
BULLET_RE = re.compile(r"^-\s+(.*)$", re.MULTILINE)
URL_RE = re.compile(r"(https?://\S+)")

SECTION_KEYS = {
    "vulnerable": "what_is_vulnerable",
    "exploited": "how_it_can_be_exploited",
    "action": "what_action_to_take",
    "reference": "references",
}

CODE_FIX_KEYWORDS = ["update", "upgrade", "patch", "new version", "later version"]
CONFIG_KEYWORDS = [
    "config", "disable", "restrict", "firewall", "access control",
    "limit access", "network segmentation", "turn off", "block access",
]


def ordinal(n):
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def build_target_cve_block(rec):
    lines = [f"{rec['id']} | CVSS {rec['cvss_score']} {rec['cvss_severity']}"]

    conditions = []
    if rec.get("attack_vector") is not None:
        conditions.append(f"Attack vector: {rec['attack_vector']}")
    if rec.get("privileges_required") is not None:
        conditions.append(f"Privileges required: {rec['privileges_required']}")
    if rec.get("user_interaction") is not None:
        conditions.append(f"User interaction: {rec['user_interaction']}")
    if conditions:
        lines.append(" | ".join(conditions))

    impact = []
    if rec.get("confidentiality_impact") is not None:
        impact.append(f"Confidentiality {rec['confidentiality_impact']}")
    if rec.get("integrity_impact") is not None:
        impact.append(f"Integrity {rec['integrity_impact']}")
    if rec.get("availability_impact") is not None:
        impact.append(f"Availability {rec['availability_impact']}")
    if impact:
        lines.append("Impact: " + " | ".join(impact))

    kev_epss = []
    if rec.get("kev_listed") is not None:
        kev_epss.append(f"KEV listed: {'YES' if rec['kev_listed'] else 'NO'}")
    epss_score = rec.get("epss_score")
    if epss_score is not None and epss_score >= 0:
        pct_str = f"EPSS: {epss_score * 100:.2f}%"
        epss_pct = rec.get("epss_percentile")
        if epss_pct is not None and epss_pct >= 0:
            pct_str += f" ({ordinal(round(epss_pct * 100))} percentile)"
        kev_epss.append(pct_str)
    if kev_epss:
        lines.append(" | ".join(kev_epss))

    if rec.get("description"):
        lines.append(f"Description: {rec['description']}")

    seen_refs = []
    for url in rec.get("references") or []:
        if url not in seen_refs:
            seen_refs.append(url)
    for url in seen_refs:
        lines.append(f"Reference: {url}")

    return "\n".join(lines)


def build_neighbour_block(neighbours):
    lines = []
    for n in neighbours:
        lines.append(f"- {n['id']} ({n['cvss_severity']}): {n['description']}")
    return "\n".join(lines)


def parse_summary(output_text):
    matches = list(HEADER_RE.finditer(output_text))
    raw_sections = {}
    for i, m in enumerate(matches):
        heading = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(output_text)
        raw_sections[heading] = output_text[start:end].strip()

    sections = {"what_is_vulnerable": [], "how_it_can_be_exploited": [], "what_action_to_take": []}
    references = []

    for heading, body in raw_sections.items():
        key = next((v for k, v in SECTION_KEYS.items() if k in heading), None)
        if key is None:
            continue
        if key == "references":
            for line in body.splitlines():
                line = line.strip()
                if not line:
                    continue
                url_match = URL_RE.search(line)
                if not url_match:
                    continue
                url = url_match.group(1)
                label = line[:url_match.start()].strip().rstrip(":").strip()
                references.append({"label": label, "url": url})
        else:
            bullets = [b.strip() for b in BULLET_RE.findall(body)]
            if not bullets:
                bullets = [line.strip() for line in body.splitlines() if line.strip()]
            sections[key] = bullets

    return {"sections": sections, "references": references}


def derive_action_cue(action_bullets):
    text = " ".join(action_bullets).lower()
    cues = []
    if any(k in text for k in CODE_FIX_KEYWORDS):
        cues.append("Code fix")
    if any(k in text for k in CONFIG_KEYWORDS):
        cues.append("Config change")
    return cues


def retrieve_neighbours(collection, embedding_fn, record):
    """Top-K nearest CVEs from the rag_corpus ChromaDB collection, excluding
    the record itself. Shared by the live on-demand path (SummaryGenerator)
    and the offline batch pre-cache script (src/prime_dashboard_cache.py) so
    both retrieve context the same way."""
    embedding = embedding_fn([record["description"]])
    res = collection.query(query_embeddings=embedding, n_results=TOP_K + 1)
    neighbours = []
    for i in range(len(res["ids"][0])):
        nid = res["ids"][0][i]
        if nid == record["id"]:
            continue
        neighbours.append({
            "id": nid,
            "cvss_severity": res["metadatas"][0][i].get("cvss_severity"),
            "description": res["documents"][0][i],
        })
        if len(neighbours) == TOP_K:
            break
    return neighbours


def write_cache(cache, cache_path=CACHE_PATH):
    """Atomic tmp-file-then-replace write, shared by the live path and the
    batch pre-cache script."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(cache, f, indent=2)
    tmp.replace(cache_path)


def load_cache(cache_path=CACHE_PATH):
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return {}
    with open(cache_path) as f:
        return json.load(f)


class SummaryGenerator:
    """Generates (or fetches cached) PERSONA summaries for arbitrary corpus CVEs."""

    def __init__(self, collection, embedding_fn, api_key, cache_path=CACHE_PATH,
                 prompt_path=PROMPT_PATH):
        self.collection = collection
        self.embedding_fn = embedding_fn
        self.client = Anthropic(api_key=api_key)
        self.cache_path = Path(cache_path)
        self.prompt_template = Path(prompt_path).read_text()
        self.cache = self._load_cache()

    def _load_cache(self):
        return load_cache(self.cache_path)

    def _write_cache(self):
        write_cache(self.cache, self.cache_path)

    def _retrieve_neighbours(self, record):
        return retrieve_neighbours(self.collection, self.embedding_fn, record)
        return neighbours

    def _call_model(self, prompt_text):
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self.client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt_text}],
                )
            except anthropic.RateLimitError as e:
                last_error = e
            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    last_error = e
                else:
                    raise
            except anthropic.APIConnectionError as e:
                last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))
        raise RuntimeError(f"all {MAX_RETRIES} retries exhausted: {last_error}")

    def get_or_generate(self, record):
        cve_id = record["id"]
        if cve_id in self.cache:
            return self.cache[cve_id]

        neighbours = self._retrieve_neighbours(record)
        target_block = build_target_cve_block(record)
        neighbour_block = build_neighbour_block(neighbours)
        prompt_text = (
            self.prompt_template
            .replace("{target_cve_block}", target_block)
            .replace("{neighbour_block}", neighbour_block)
        )

        response = self._call_model(prompt_text)
        if response.stop_reason == "refusal":
            raise RuntimeError(f"model refused to generate a summary for {cve_id}")
        output_text = "".join(b.text for b in response.content if b.type == "text")

        parsed = parse_summary(output_text)
        result = {
            "cve_id": cve_id,
            "model": response.model,
            "temperature": TEMPERATURE,
            "neighbours_used": [n["id"] for n in neighbours],
            "output_text": output_text,
            "sections": parsed["sections"],
            "references": parsed["references"],
            "action_cue": derive_action_cue(parsed["sections"]["what_action_to_take"]),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.cache[cve_id] = result
        self._write_cache()
        return result
