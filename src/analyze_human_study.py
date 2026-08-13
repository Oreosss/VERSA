"""
Parses the Qualtrics human comprehension study export, verifies the supplied
answer key against the actual survey source (not trusted blindly), scores
the three MC comprehension questions per CVE entry, and aggregates Likert
(clarity/confidence) results by condition (raw NVD vs LLM summary).

Inputs (data/human_study/):
    survey_source.txt              - Qualtrics import file (verbatim stimulus text + MC choices)
    answer_key.txt                 - supplied answer key (first-listed choice = correct)
    qualtrics_export_recorded.csv  - finalised responses (R_ ids)
    qualtrics_export_inprogress.csv - in-progress/abandoned responses (FS_ ids)

Outputs (data/human_study/):
    response_summary.csv   - one row per response: consent, demographics, block, data-quality flags
    comprehension_long.csv - one row per (response, cve, question): participant answer, correct answer, is_correct
    likert_long.csv        - one row per (response, cve): clarity + confidence ratings
    answer_key_check.csv   - one row per of the 72 items: supplied vs. derived-from-source correct answer
"""

import re
import csv
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "human_study"
SURVEY_SOURCE = DATA_DIR / "survey_source.txt"
ANSWER_KEY = DATA_DIR / "answer_key.txt"
CSV_RECORDED = DATA_DIR / "qualtrics_export_recorded.csv"
CSV_INPROGRESS = DATA_DIR / "qualtrics_export_inprogress.csv"

LIKERT_MAP = {
    "Strongly disagree": 1,
    "Disagree": 2,
    "Neither agree nor disagree": 3,
    "Agree": 4,
    "Strongly agree": 5,
}

# block -> ordered list of (slot_prefix, cve_id)
BLOCK_SLOTS = {
    "A": [("A1_2020_8010", "CVE-2020-8010"), ("A2_2021_21974", "CVE-2021-21974"),
          ("A3_2022_3062", "CVE-2022-3062"), ("A4_2023_21608", "CVE-2023-21608")],
    "B": [("B1_2020_8010", "CVE-2020-8010"), ("B2_2021_21974", "CVE-2021-21974"),
          ("B3_2022_3062", "CVE-2022-3062"), ("B4_2023_21608", "CVE-2023-21608")],
    "C": [("C1_2023_29119", "CVE-2023-29119"), ("C2_2023_43661", "CVE-2023-43661"),
          ("C3_2021_30970", "CVE-2021-30970"), ("C4_2024_21887", "CVE-2024-21887")],
    "D": [("D1_2023_29119", "CVE-2023-29119"), ("D2_2023_43661", "CVE-2023-43661"),
          ("D3_2021_30970", "CVE-2021-30970"), ("D4_2024_21887", "CVE-2024-21887")],
    "E": [("E1_2021_42013", "CVE-2021-42013"), ("E2_2023_44221", "CVE-2023-44221"),
          ("E3_2021_22204", "CVE-2021-22204"), ("E4_2022_40765", "CVE-2022-40765")],
    "F": [("F1_2021_42013", "CVE-2021-42013"), ("F2_2023_44221", "CVE-2023-44221"),
          ("F3_2021_22204", "CVE-2021-22204"), ("F4_2022_40765", "CVE-2022-40765")],
}
# A/C/E: slot1=NVD,slot2=Summary,slot3=NVD,slot4=Summary. B/D/F: flipped.
CONDITION_PATTERN = {
    "A": ["NVD", "Summary", "NVD", "Summary"],
    "C": ["NVD", "Summary", "NVD", "Summary"],
    "E": ["NVD", "Summary", "NVD", "Summary"],
    "B": ["Summary", "NVD", "Summary", "NVD"],
    "D": ["Summary", "NVD", "Summary", "NVD"],
    "F": ["Summary", "NVD", "Summary", "NVD"],
}


def parse_survey_source(text: str):
    """Returns (stim_condition: {stim_id: 'NVD'|'Summary'}, choices: {question_id: [choice, ...]})"""
    stim_condition = {}
    for m in re.finditer(r"\[\[ID:(\w+_stim)\]\]\n(.+)\n\n", text):
        stim_id, html = m.group(1), m.group(2)
        stim_condition[stim_id] = "Summary" if "What is vulnerable" in html else "NVD"

    choices = {}
    for m in re.finditer(r"\[\[ID:(\w+_Q\d)\]\]\n(.+?)\n\[\[Choices\]\]\n((?:.+\n)+?)\n", text):
        qid, choice_block = m.group(1), m.group(3)
        choices[qid] = [c.strip() for c in choice_block.strip("\n").split("\n")]
    return stim_condition, choices


def parse_answer_key(text: str):
    key = {}
    for m in re.finditer(r"\[(\w+)\]\nQ: (.+)\nCORRECT: (.+)", text):
        key[m.group(1)] = m.group(3).strip()
    return key


def verify_condition_pattern(stim_condition: dict):
    """Cross-check the hard-coded CONDITION_PATTERN against the actual stim HTML."""
    mismatches = []
    for block, slots in BLOCK_SLOTS.items():
        expected = CONDITION_PATTERN[block]
        for (prefix, _cve), exp_cond in zip(slots, expected):
            stim_id = f"{prefix}_stim"
            actual = stim_condition.get(stim_id)
            if actual != exp_cond:
                mismatches.append((stim_id, exp_cond, actual))
    return mismatches


def verify_answer_key(supplied_key: dict, choices: dict):
    rows = []
    for qid, supplied_correct in supplied_key.items():
        if qid.endswith("_Q4") or qid.endswith("_Q5"):
            continue  # Likert items have no "correct" answer
        opts = choices.get(qid, [])
        first_choice = opts[0] if opts else None
        agrees = (supplied_correct == first_choice)
        rows.append({
            "question_id": qid,
            "supplied_correct": supplied_correct,
            "first_listed_choice": first_choice,
            "agrees": agrees,
        })
    return pd.DataFrame(rows)


def load_responses():
    dfs = []
    for path, source in [(CSV_RECORDED, "recorded"), (CSV_INPROGRESS, "inprogress")]:
        df = pd.read_csv(path, skiprows=[1, 2])
        df["source_file"] = source
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def detect_active_block(row) -> list:
    """Returns list of block letters that have ANY non-null answer (should be 0 or 1)."""
    active = []
    for block, slots in BLOCK_SLOTS.items():
        cols = [f"{prefix}_Q{n}" for prefix, _ in slots for n in range(1, 6)]
        if row[cols].notna().any():
            active.append(block)
    return active


def build_tables(responses: pd.DataFrame, answer_key: dict):
    response_rows = []
    comprehension_rows = []
    likert_rows = []

    for _, row in responses.iterrows():
        rid = row["ResponseId"]
        active_blocks = detect_active_block(row)
        version_field = row.get("Version")
        block_matches_version = (len(active_blocks) == 1 and active_blocks[0] == version_field)

        n_items_answered = 0
        if len(active_blocks) == 1:
            block = active_blocks[0]
            slots = BLOCK_SLOTS[block]
            conditions = CONDITION_PATTERN[block]
            for (prefix, cve_id), condition in zip(slots, conditions):
                q_vals = {n: row.get(f"{prefix}_Q{n}") for n in range(1, 6)}
                n_items_answered += sum(pd.notna(v) for v in q_vals.values())

                for n in (1, 2, 3):
                    ans = q_vals[n]
                    qid = f"{prefix}_Q{n}"
                    correct = answer_key.get(qid)
                    is_correct = None
                    if pd.notna(ans):
                        is_correct = (str(ans).strip() == correct)
                    comprehension_rows.append({
                        "response_id": rid, "source_file": row["source_file"],
                        "block": block, "cve_id": cve_id, "condition": condition,
                        "question_num": n, "participant_answer": ans,
                        "correct_answer": correct, "is_correct": is_correct,
                    })

                clarity_raw = q_vals[4]
                confidence_raw = q_vals[5]
                likert_rows.append({
                    "response_id": rid, "source_file": row["source_file"],
                    "block": block, "cve_id": cve_id, "condition": condition,
                    "clarity_raw": clarity_raw,
                    "clarity_score": LIKERT_MAP.get(clarity_raw) if pd.notna(clarity_raw) else None,
                    "confidence_raw": confidence_raw,
                    "confidence_score": LIKERT_MAP.get(confidence_raw) if pd.notna(confidence_raw) else None,
                })
        elif len(active_blocks) > 1:
            n_items_answered = -1  # anomaly flag

        response_rows.append({
            "response_id": rid,
            "source_file": row["source_file"],
            "consent": row.get("C1"),
            "s1_technical_background": row.get("S1"),
            "s2_security_training": row.get("S2"),
            "s3_cve_familiarity": row.get("S3"),
            "progress": row.get("Progress"),
            "finished": row.get("Finished"),
            "duration_seconds": row.get("Duration (in seconds)"),
            "version_field": version_field,
            "active_blocks": ",".join(active_blocks) if active_blocks else None,
            "block_matches_version": block_matches_version,
            "n_items_answered_of_20": n_items_answered,
            "closing_comment": row.get("CLOSING"),
        })

    return (pd.DataFrame(response_rows), pd.DataFrame(comprehension_rows), pd.DataFrame(likert_rows))


def main():
    survey_text = SURVEY_SOURCE.read_text(encoding="utf-8")
    stim_condition, choices = parse_survey_source(survey_text)
    supplied_key = parse_answer_key(ANSWER_KEY.read_text(encoding="utf-8"))

    print(f"Parsed {len(stim_condition)} stim blocks, {len(choices)} MC questions from survey source.")
    print(f"Parsed {len(supplied_key)} answer key entries.")

    cond_mismatches = verify_condition_pattern(stim_condition)
    print(f"\n=== Condition pattern verification ({24} slots checked) ===")
    if cond_mismatches:
        for stim_id, exp, actual in cond_mismatches:
            print(f"  MISMATCH: {stim_id} expected {exp}, derived from source: {actual}")
    else:
        print("  All 24 slots match the confirmed alternating NVD/Summary pattern.")

    key_check = verify_answer_key(supplied_key, choices)
    key_check.to_csv(DATA_DIR / "answer_key_check.csv", index=False)
    n_disagree = (~key_check["agrees"]).sum()
    print(f"\n=== Answer key verification ({len(key_check)} MC items checked) ===")
    if n_disagree:
        print(f"  {n_disagree} DISAGREEMENTS between supplied key and first-listed choice in survey source:")
        print(key_check[~key_check["agrees"]].to_string(index=False))
    else:
        print("  Supplied answer key matches the first-listed choice for all items. Using it as-is.")

    responses = load_responses()
    print(f"\n=== Loaded {len(responses)} raw response rows ({(responses['source_file']=='recorded').sum()} recorded, "
          f"{(responses['source_file']=='inprogress').sum()} inprogress) ===")

    response_summary, comprehension_long, likert_long = build_tables(responses, supplied_key)

    response_summary.to_csv(DATA_DIR / "response_summary.csv", index=False)
    comprehension_long.to_csv(DATA_DIR / "comprehension_long.csv", index=False)
    likert_long.to_csv(DATA_DIR / "likert_long.csv", index=False)

    print("\n=== Response summary (all responses, unfiltered) ===")
    print(response_summary.to_string(index=False))

    # The target population (CLAUDE.md) is technical non-security personnel.
    # A respondent who answers "No" to S1 (technical background) is outside
    # that population, not merely a low scorer — excluded from the main
    # analysis below, but kept in response_summary.csv and reported
    # separately rather than silently dropped.
    non_technical_ids = set(
        response_summary.loc[response_summary["s1_technical_background"] == "No", "response_id"]
    )

    # R_5Eznt1RPReTcuu0 (block F, technical background, completed) appeared in
    # qualtrics_export_recorded.csv after every existing headline figure (n=15/17)
    # had already been computed and written up. Held out pending an explicit
    # decision to fold it in and re-run the full write-up, not a scope exclusion
    # like non_technical_ids below.
    pending_review_ids = {"R_5Eznt1RPReTcuu0"}
    excluded_ids = non_technical_ids | pending_review_ids

    if excluded_ids:
        print(f"\n=== Excluding {len(excluded_ids)} respondent(s) from main analysis: "
              f"{sorted(non_technical_ids)} (non-technical background), "
              f"{sorted(pending_review_ids)} (pending review, see comment above) ===")
        excluded_comp = comprehension_long[comprehension_long["response_id"].isin(excluded_ids)]
        excluded_scored = excluded_comp.dropna(subset=["is_correct"])
        if len(excluded_scored):
            print(f"  (their comprehension accuracy, reported separately, not in the figures below: "
                  f"{excluded_scored['is_correct'].mean():.3f} over {len(excluded_scored)} items)")
    comprehension_long = comprehension_long[~comprehension_long["response_id"].isin(excluded_ids)]
    likert_long = likert_long[~likert_long["response_id"].isin(excluded_ids)]

    block_mismatches = response_summary[
        response_summary["active_blocks"].notna() & (~response_summary["block_matches_version"])
    ]
    print(f"\n=== Block vs Version field mismatches ===")
    if len(block_mismatches):
        print(block_mismatches[["response_id", "active_blocks", "version_field"]].to_string(index=False))
    else:
        print("  None — active block matches the Version field for every response that reached a block.")

    scored = comprehension_long.dropna(subset=["is_correct"])
    print(f"\n=== Comprehension accuracy: {len(scored)} scored items ===")
    print("\nOverall by condition:")
    print(scored.groupby("condition")["is_correct"].agg(["mean", "count"]))
    print("\nBy condition x question number:")
    print(scored.groupby(["condition", "question_num"])["is_correct"].agg(["mean", "count"]))
    print("\nBy CVE x condition:")
    print(scored.groupby(["cve_id", "condition"])["is_correct"].agg(["mean", "count"]))

    likert_scored = likert_long.dropna(subset=["clarity_score", "confidence_score"], how="all")
    print(f"\n=== Likert results: {len(likert_scored)} entries with at least one rating ===")
    print("\nBy condition:")
    print(likert_scored.groupby("condition")[["clarity_score", "confidence_score"]].agg(["mean", "count"]))
    print("\nBy CVE x condition:")
    print(likert_scored.groupby(["cve_id", "condition"])[["clarity_score", "confidence_score"]].mean())

    demo = response_summary[["response_id", "s2_security_training", "s3_cve_familiarity"]]

    scored_s2 = scored.merge(demo, on="response_id")
    print("\n=== Comprehension accuracy by S2 (formal cyber security training), technical-background sample ===")
    print(scored_s2.groupby("s2_security_training")["is_correct"].agg(["mean", "count"]))
    print("\nBy S2 x condition:")
    print(scored_s2.groupby(["s2_security_training", "condition"])["is_correct"].agg(["mean", "count"]))

    scored_s3 = scored.merge(demo, on="response_id")
    print("\n=== Comprehension accuracy by S3 (CVE/CVSS familiarity), technical-background sample ===")
    print(scored_s3.groupby("s3_cve_familiarity")["is_correct"].agg(["mean", "count"]))
    print("\nBy S3 x condition:")
    print(scored_s3.groupby(["s3_cve_familiarity", "condition"])["is_correct"].agg(["mean", "count"]))

    lik_scored_demo = likert_scored.merge(demo, on="response_id")
    print("\n=== Likert by S2 ===")
    print(lik_scored_demo.groupby("s2_security_training")[["clarity_score", "confidence_score"]].mean())
    print("\n=== Likert by S3 ===")
    print(lik_scored_demo.groupby("s3_cve_familiarity")[["clarity_score", "confidence_score"]].mean())

    QUAD_MAP = {"A": "Quad1(A/B)", "B": "Quad1(A/B)", "C": "Quad2(C/D)",
                "D": "Quad2(C/D)", "E": "Quad3(E/F)", "F": "Quad3(E/F)"}

    print("\n=== Comprehension accuracy by CVE (both conditions combined) ===")
    print(scored.groupby("cve_id")["is_correct"].agg(["mean", "count"]).sort_values("mean"))

    print("\n=== Comprehension accuracy by block (A-F) -- caveat: 2-4 respondents per block, "
          "dominated by individual variance, see write-up ===")
    print(scored.groupby("block")["is_correct"].agg(["mean", "count"]).sort_values("mean"))

    scored_quad = scored.copy()
    scored_quad["quad"] = scored_quad["block"].map(QUAD_MAP)
    print("\n=== Comprehension accuracy by quad (CVE set, pools both counterbalance letters) ===")
    print(scored_quad.groupby("quad")["is_correct"].agg(["mean", "count"]))
    print("\nBy quad x condition:")
    print(scored_quad.groupby(["quad", "condition"])["is_correct"].agg(["mean", "count"]))

    print("\n=== Likert by CVE ===")
    print(likert_scored.groupby("cve_id")[["clarity_score", "confidence_score"]].agg(["mean", "count"]))

    lik_quad = likert_scored.copy()
    lik_quad["quad"] = lik_quad["block"].map(QUAD_MAP)
    print("\n=== Likert by quad ===")
    print(lik_quad.groupby("quad")[["clarity_score", "confidence_score"]].agg(["mean", "count"]))

    active = response_summary[
        (response_summary["n_items_answered_of_20"] > 0)
        & (~response_summary["response_id"].isin(excluded_ids))
    ]

    print("\n=== Technical non-security classification (S1=Yes & S2=No), technical-background sample (n=15) ===")
    print(active["s2_security_training"].value_counts())
    print(f"technical non-security (S1=Yes, S2=No): {(active['s2_security_training'] == 'No').sum()} of {len(active)}")

    demo_all = response_summary.dropna(subset=["s1_technical_background", "s2_security_training"])
    print(f"\n=== S1 x S2 crosstab, full raw pool (n={len(demo_all)} who answered both) ===")
    print(pd.crosstab(demo_all["s1_technical_background"], demo_all["s2_security_training"]))

    print("\n=== Joint S2 x S3 distribution, technical-background sample ===")
    print(pd.crosstab(active["s2_security_training"], active["s3_cve_familiarity"]))
    merged_s2s3 = scored.merge(
        active[["response_id", "s2_security_training", "s3_cve_familiarity"]], on="response_id"
    )
    print("\nAccuracy by S2 x S3 jointly (most cells are 1-3 respondents -- see write-up for caveats):")
    print(merged_s2s3.groupby(["s2_security_training", "s3_cve_familiarity"])["is_correct"].agg(["mean", "count"]))

    print("\n=== Duration (seconds) by S2 ===")
    print(active.groupby("s2_security_training")["duration_seconds"].agg(["mean", "median", "min", "max", "count"]))
    print("\n=== Duration (seconds) by S3 ===")
    print(active.groupby("s3_cve_familiarity")["duration_seconds"].agg(["mean", "median", "min", "max", "count"]))

    print("\n=== Block assignment balance: S2 x block, S3 x block (randomization sanity check) ===")
    print(pd.crosstab(active["active_blocks"], active["s2_security_training"]))
    print(pd.crosstab(active["active_blocks"], active["s3_cve_familiarity"]))

    print("\n=== Calibration: entry accuracy vs self-reported confidence, by condition ===")
    entry_acc = scored.groupby(["response_id", "cve_id", "condition"])["is_correct"].mean().rename("entry_accuracy")
    calib = entry_acc.reset_index().merge(
        likert_scored[["response_id", "cve_id", "condition", "confidence_score"]],
        on=["response_id", "cve_id", "condition"],
    )
    print(calib.groupby("condition")[["entry_accuracy", "confidence_score"]].mean())
    calib["overconfident"] = (calib["confidence_score"] >= 4) & (calib["entry_accuracy"] < 1.0)
    calib["underconfident"] = (calib["confidence_score"] <= 2) & (calib["entry_accuracy"] == 1.0)
    print("\nOverconfident entries (confidence >=4, not all correct) by condition:")
    print(calib.groupby("condition")["overconfident"].agg(["sum", "count", "mean"]))
    print("\nUnderconfident entries (confidence <=2, all correct) by condition:")
    print(calib.groupby("condition")["underconfident"].agg(["sum", "count", "mean"]))

    calib_demo = calib.merge(demo, on="response_id")
    print("\n=== Overconfidence rate by S2 (training) ===")
    print(calib_demo.groupby("s2_security_training")["overconfident"].agg(["sum", "count", "mean"]))
    print("\n=== Overconfidence rate by S3 (familiarity) ===")
    print(calib_demo.groupby("s3_cve_familiarity")["overconfident"].agg(["sum", "count", "mean"]))
    print("\nBy S3 x condition:")
    print(calib_demo.groupby(["s3_cve_familiarity", "condition"])["overconfident"].agg(["sum", "count", "mean"]))
    print("\nPer-respondent overconfidence count (out of their rated entries):")
    print(calib_demo.groupby(["response_id", "s2_security_training", "s3_cve_familiarity"])["overconfident"]
          .agg(["sum", "count"]).sort_values("sum", ascending=False))
    print("\nOverconfidence rate by CVE:")
    print(calib.groupby("cve_id")["overconfident"].agg(["sum", "count", "mean"]).sort_values("mean", ascending=False))

    print("\n=== Accuracy by slot position (1st-4th CVE seen within the block) ===")
    slot_map = {
        (block, cve): i + 1
        for block, entries in BLOCK_SLOTS.items()
        for i, (_, cve) in enumerate(entries)
    }
    scored_slot = scored.copy()
    scored_slot["slot"] = list(zip(scored_slot["block"], scored_slot["cve_id"]))
    scored_slot["slot"] = scored_slot["slot"].map(slot_map)
    print(scored_slot.groupby("slot")["is_correct"].agg(["mean", "count"]))
    print("\nBy slot x condition:")
    print(scored_slot.groupby(["slot", "condition"])["is_correct"].agg(["mean", "count"]))
    likert_slot = likert_scored.copy()
    likert_slot["slot"] = list(zip(likert_slot["block"], likert_slot["cve_id"]))
    likert_slot["slot"] = likert_slot["slot"].map(slot_map)
    print("\nLikert by slot position:")
    print(likert_slot.groupby("slot")[["clarity_score", "confidence_score"]].mean())

    print("\n=== Within-person consistency: per-respondent accuracy, NVD entries vs Summary entries ===")
    per_person_cond = scored.groupby(["response_id", "condition"])["is_correct"].mean().unstack()
    print(per_person_cond)
    print(f"\nPearson correlation (NVD acc vs Summary acc): {per_person_cond['NVD'].corr(per_person_cond['Summary']):.3f}")
    print(f"Spearman correlation: {per_person_cond['NVD'].corr(per_person_cond['Summary'], method='spearman'):.3f}")
    print(f"Better on NVD: {(per_person_cond['NVD'] > per_person_cond['Summary']).sum()}, "
          f"Better on Summary: {(per_person_cond['Summary'] > per_person_cond['NVD']).sum()}, "
          f"Tied: {(per_person_cond['NVD'] == per_person_cond['Summary']).sum()}")

    print("\n=== Distractor clustering: does everyone who gets an item wrong pick the SAME wrong answer? ===")
    wrong = scored[scored["is_correct"] == False]
    for (cve, q, cond), g in wrong.groupby(["cve_id", "question_num", "condition"]):
        if len(g) < 2:
            continue
        print(f"\n{cve} Q{q} ({cond}) -- {len(g)} wrong answers:")
        for ans, n in g["participant_answer"].value_counts().items():
            print(f"   x{n}: {ans}")

    print("\n=== Closing comments (verbatim) ===")
    for _, r in response_summary.iterrows():
        if pd.notna(r["closing_comment"]):
            print(f"\n[{r['response_id']}]:\n{r['closing_comment']}")


if __name__ == "__main__":
    main()
