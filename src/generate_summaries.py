"""Generate LLM summaries for the 24 eval CVEs under both prompt versions.

Generation only -- does not compute metrics. For each eval CVE, assembles
target_cve_block and neighbour_block, substitutes them into the frozen
baseline and persona templates, and sends both to the Anthropic API at a
fixed model and temperature=0. Writes one record per generation to
summaries.json (48 total). Resumable: a (cve_id, prompt_version) pair
already present in summaries.json is skipped, not regenerated.

Two data-quality decisions were made with the user before writing this
script, both driven by gaps in the eval data rather than by the prompt spec:
- References carry no source/vendor label anywhere in the pipeline (checked
  upstream in the raw NVD pull too), so Reference lines are emitted as a
  bare URL with no parenthetical label.
- Reference lists contain duplicate URLs in every eval record, so the list
  is deduplicated (first-seen order) before emitting Reference lines.
"""

import hashlib
import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path

import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv

EVAL_SAMPLE_PATH = "data/eval_sample.jsonl"
RETRIEVAL_VALIDATION_PATH = "data/retrieval_validation.json"
PROMPT_PATHS = {
    "baseline": "v1_prose/prompts/prompt-baseline_v1_prose.txt",
    "persona": "v1_prose/prompts/prompt-persona_v1_prose.txt",
}
OUTPUT_PATH = "summaries.json"
METHODOLOGY_LOG_PATH = "METHODOLOGY_LOG.md"

MODEL = "claude-opus-4-6"
TEMPERATURE = 0
MAX_TOKENS = 2048
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


def ordinal(n):
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def load_eval_sample(path):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    if not records:
        raise SystemExit(f"STOP: {path} is empty.")
    return records


def load_retrieval_validation(path):
    with open(path) as f:
        data = json.load(f)
    by_id = {entry["eval_id"]: entry for entry in data["eval_cves"]}
    return by_id


def load_prompts(paths):
    texts = {}
    hashes = {}
    for version, path in paths.items():
        raw = Path(path).read_bytes()
        text = raw.decode("utf-8")
        if "{target_cve_block}" not in text or "{neighbour_block}" not in text:
            raise SystemExit(
                f"STOP: {path} is missing the expected {{target_cve_block}} / "
                "{neighbour_block}} placeholders."
            )
        texts[version] = text
        hashes[version] = hashlib.sha256(raw).hexdigest()
    return texts, hashes


def load_existing_summaries(path):
    if not Path(path).exists():
        return []
    with open(path) as f:
        return json.load(f)


def write_summaries(records, path):
    tmp = Path(path).with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(records, f, indent=2)
    tmp.replace(path)


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
    if rec.get("epss_score") is not None:
        pct_str = f"EPSS: {rec['epss_score'] * 100:.2f}%"
        if rec.get("epss_percentile") is not None:
            pct_str += f" ({ordinal(round(rec['epss_percentile'] * 100))} percentile)"
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


def call_model(client, prompt_text):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.messages.create(
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
            wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"  retryable error ({last_error}), retrying in {wait:.0f}s "
                  f"({attempt}/{MAX_RETRIES})...")
            time.sleep(wait)

    raise RuntimeError(f"all {MAX_RETRIES} retries exhausted: {last_error}")


def append_methodology_log(models_used, prompt_hashes, written, skipped, failed,
                            run_timestamp):
    entry = []
    entry.append("")
    entry.append(f"## Stage 6b -- Baseline vs Persona Summary Generation ({date.today().isoformat()})")
    entry.append("")
    entry.append("**Script:** `src/generate_summaries.py`")
    entry.append("**Output:** `summaries.json`")
    entry.append("")
    entry.append(
        f"Ran both frozen prompt templates (`prompt-baseline_v1.txt`, `prompt-persona_v1.txt`) "
        f"against all 24 eval CVEs, reusing the saved neighbours from "
        f"`data/retrieval_validation.json` (no re-querying ChromaDB). Model and temperature "
        f"were fixed across all calls: model `{', '.join(sorted(models_used))}`, "
        f"temperature {TEMPERATURE}."
    )
    entry.append("")
    entry.append(f"- Prompt hash (baseline): `{prompt_hashes['baseline']}`")
    entry.append(f"- Prompt hash (persona): `{prompt_hashes['persona']}`")
    entry.append(f"- Records written this run: {written}")
    entry.append(f"- Records skipped (already present): {skipped}")
    entry.append(f"- Records failed after retries: {len(failed)}"
                  + (f" ({failed})" if failed else ""))
    entry.append(f"- Run timestamp: {run_timestamp}")
    entry.append(
        "- Generation only -- no metrics (ROUGE, BERTScore, Flesch-Kincaid, LLM-as-judge) "
        "computed in this step."
    )
    entry.append("")

    with open(METHODOLOGY_LOG_PATH, "a") as f:
        f.write("\n".join(entry))


def main():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("STOP: ANTHROPIC_API_KEY not set (add it to .env).")

    print(f"Loading eval sample from {EVAL_SAMPLE_PATH}...")
    eval_records = load_eval_sample(EVAL_SAMPLE_PATH)
    print(f"Loaded {len(eval_records)} eval CVEs.")

    print(f"Loading saved neighbours from {RETRIEVAL_VALIDATION_PATH}...")
    retrieval = load_retrieval_validation(RETRIEVAL_VALIDATION_PATH)

    print("Loading and hashing prompt templates...")
    prompt_texts, prompt_hashes = load_prompts(PROMPT_PATHS)

    existing = load_existing_summaries(OUTPUT_PATH)
    completed = {(r["cve_id"], r["prompt_version"]) for r in existing}
    print(f"Found {len(existing)} existing record(s) in {OUTPUT_PATH}.")

    client = Anthropic(api_key=api_key)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    written = 0
    skipped = 0
    failed = []
    models_seen = set(r["model"] for r in existing)

    for rec in eval_records:
        cve_id = rec["id"]
        if cve_id not in retrieval:
            raise SystemExit(
                f"STOP: {cve_id} is in the eval sample but has no entry in "
                f"{RETRIEVAL_VALIDATION_PATH}."
            )
        neighbours = retrieval[cve_id]["neighbours"]
        target_block = build_target_cve_block(rec)
        neighbour_block = build_neighbour_block(neighbours)
        neighbour_ids = [n["id"] for n in neighbours]

        for version in ("baseline", "persona"):
            if (cve_id, version) in completed:
                skipped += 1
                continue

            prompt_text = (
                prompt_texts[version]
                .replace("{target_cve_block}", target_block)
                .replace("{neighbour_block}", neighbour_block)
            )

            print(f"Generating {cve_id} [{version}]...")
            try:
                response = call_model(client, prompt_text)
            except Exception as e:
                print(f"  FAILED after retries: {e}")
                failed.append(f"{cve_id}:{version}")
                continue

            if response.stop_reason == "refusal":
                print(f"  FAILED: model refused")
                failed.append(f"{cve_id}:{version}")
                continue

            output_text = "".join(
                b.text for b in response.content if b.type == "text"
            )

            record = {
                "cve_id": cve_id,
                "prompt_version": version,
                "persona": version == "persona",
                "model": response.model,
                "temperature": TEMPERATURE,
                "prompt_file_hash": prompt_hashes[version],
                "neighbours_used": neighbour_ids,
                "output_text": output_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            existing.append(record)
            write_summaries(existing, OUTPUT_PATH)
            completed.add((cve_id, version))
            models_seen.add(response.model)
            written += 1

    print()
    print("Done.")
    print(f"Written: {written}")
    print(f"Skipped (already present): {skipped}")
    print(f"Failed: {len(failed)}" + (f" -> {failed}" if failed else ""))
    print(f"Model(s) seen: {sorted(models_seen)}")
    print(f"Prompt hash (baseline): {prompt_hashes['baseline']}")
    print(f"Prompt hash (persona): {prompt_hashes['persona']}")

    if written > 0 or not Path(METHODOLOGY_LOG_PATH).exists():
        append_methodology_log(models_seen, prompt_hashes, written, skipped, failed,
                                run_timestamp)
        print(f"Appended entry to {METHODOLOGY_LOG_PATH}.")


if __name__ == "__main__":
    main()
