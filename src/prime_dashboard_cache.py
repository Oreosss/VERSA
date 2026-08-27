"""Batch pre-cache PERSONA summaries for a curated demo subset of the corpus.

Runs the same retrieval + prompt-building logic as the live on-demand path
(src/dashboard_generate.py) but submits all requests as a single Anthropic
Batch API job (~50% cheaper than live calls, no per-CVE live-latency
pressure), then parses and merges results into the same
data/dashboard_summary_cache.json the dashboard already reads -- no
dashboard code changes are needed for the results to take effect.

Selection: all not-yet-cached KEV-listed CVEs (up to KEV_CAP), then a
stratified pull across severity x EPSS band to fill the remaining slots up
to TARGET_COUNT, so the pre-cached set exercises the full badge/chart visual
range rather than an arbitrary slice. random.seed(RANDOM_SEED) for
reproducibility, matching this project's existing sampling convention.

Run: python src/prime_dashboard_cache.py
Requires ANTHROPIC_API_KEY in .env.
"""

import os
import random
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.insert(0, "src")

from anthropic import Anthropic

from dashboard_data import CorpusStore
from dashboard_generate import (
    CACHE_PATH, MAX_TOKENS, MODEL, PROMPT_PATH, TEMPERATURE,
    build_neighbour_block, build_target_cve_block, derive_action_cue,
    load_cache, parse_summary, retrieve_neighbours, write_cache,
)
from dashboard_search import SearchEngine

TARGET_COUNT = 100
KEV_CAP = 40  # generous headroom under the ~53 KEV-listed CVEs in-corpus
RANDOM_SEED = 42
POLL_INTERVAL_SECONDS = 30


def epss_band(record):
    score = record.get("epss_score")
    if score is None or score < 0:
        return "LOW"
    if score >= 0.5:
        return "HIGH"
    if score >= 0.01:
        return "MEDIUM"
    return "LOW"


def select_cves(store, already_cached):
    random.seed(RANDOM_SEED)
    candidates = [r for r in store.records if r["id"] not in already_cached]

    kev = [r for r in candidates if r.get("kev_listed")]
    random.shuffle(kev)
    selected = kev[:KEV_CAP]
    selected_ids = {r["id"] for r in selected}

    remaining_slots = TARGET_COUNT - len(selected)
    pool = [r for r in candidates if r["id"] not in selected_ids]

    buckets = {}
    for r in pool:
        key = (r["cvss_severity"], epss_band(r))
        buckets.setdefault(key, []).append(r)
    for recs in buckets.values():
        random.shuffle(recs)

    keys = sorted(buckets.keys())
    i = 0
    while remaining_slots > 0 and any(buckets[k] for k in keys):
        key = keys[i % len(keys)]
        if buckets[key]:
            selected.append(buckets[key].pop())
            remaining_slots -= 1
        i += 1

    return selected[:TARGET_COUNT]


def build_prompt(record, search_engine, prompt_template):
    neighbours = retrieve_neighbours(search_engine.collection, search_engine.embedding_fn, record)
    target_block = build_target_cve_block(record)
    neighbour_block = build_neighbour_block(neighbours)
    prompt_text = (
        prompt_template
        .replace("{target_cve_block}", target_block)
        .replace("{neighbour_block}", neighbour_block)
    )
    return prompt_text, neighbours


def main():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY not set in .env")

    print("Loading corpus + search engine...")
    store = CorpusStore()
    search_engine = SearchEngine(store)
    prompt_template = open(PROMPT_PATH).read()

    cache = load_cache(CACHE_PATH)
    selected = select_cves(store, set(cache.keys()))
    kev_count = sum(1 for r in selected if r.get("kev_listed"))
    print(f"Selected {len(selected)} CVEs to pre-cache ({kev_count} KEV-listed).")
    if not selected:
        print("Nothing to do -- selection is empty (already cached or corpus exhausted).")
        return

    print("Building prompts (local retrieval, no API calls yet)...")
    requests = []
    neighbours_by_id = {}
    for record in selected:
        prompt_text, neighbours = build_prompt(record, search_engine, prompt_template)
        neighbours_by_id[record["id"]] = [n["id"] for n in neighbours]
        requests.append({
            "custom_id": record["id"],
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "messages": [{"role": "user", "content": prompt_text}],
            },
        })

    client = Anthropic(api_key=api_key)
    print(f"Submitting batch of {len(requests)} requests...")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        counts = batch.request_counts
        print(f"  status: {batch.processing_status} "
              f"(succeeded={counts.succeeded}, errored={counts.errored}, "
              f"processing={counts.processing})")
        if batch.processing_status == "ended":
            break
        time.sleep(POLL_INTERVAL_SECONDS)

    print("Fetching results...")
    succeeded = 0
    failed = []
    for entry in client.messages.batches.results(batch.id):
        cve_id = entry.custom_id
        if entry.result.type != "succeeded":
            failed.append((cve_id, entry.result.type))
            continue

        response = entry.result.message
        if response.stop_reason == "refusal":
            failed.append((cve_id, "refusal"))
            continue

        output_text = "".join(b.text for b in response.content if b.type == "text")
        parsed = parse_summary(output_text)
        cache[cve_id] = {
            "cve_id": cve_id,
            "model": response.model,
            "temperature": TEMPERATURE,
            "neighbours_used": neighbours_by_id[cve_id],
            "output_text": output_text,
            "sections": parsed["sections"],
            "references": parsed["references"],
            "action_cue": derive_action_cue(parsed["sections"]["what_action_to_take"]),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        succeeded += 1

    write_cache(cache, CACHE_PATH)
    print(f"Done. {succeeded} succeeded, {len(failed)} failed. Cache now has {len(cache)} entries.")
    if failed:
        print("Failed CVEs:")
        for cve_id, reason in failed:
            print(f"  {cve_id}: {reason}")


if __name__ == "__main__":
    main()
