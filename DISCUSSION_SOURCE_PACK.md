# DISCUSSION_SOURCE_PACK.md

Reference pack for the dissertation Discussion chapter. This file gathers evidence and previously recorded reasoning from the existing project files. It does not compute new results, run any scripts, or offer new interpretation. Sources read: `CLAUDE.md`, `STATUS.md`, `METHODOLOGY_LOG.md`, `FINDINGS_LOG.md`, `v2_bullet/judge/llm_judge_raw.json`, `v2_bullet/judge/llm_judge_raw_faithfulness_ext.json`, `v2_bullet/judge/llm_judge_mapping.json`, `v2_bullet/metrics/metrics_per_summary_bullet.csv`, `data/eval_sample.jsonl`, `v2_bullet/summaries/summaries_bullet.json`, `HUMAN_STUDY_FINDINGS.md`, `data/human_study/survey_source.txt` (both added for Section 5, 2026-08-10).

---

## Section 1 — Judge justification strings (evidence for the faithfulness scope artefact)

Stage 6e scored faithfulness against the bare NVD `description` field only. Stage 6f re-scored the same summaries' faithfulness against an expanded reference (description plus the CVSS sub-fields: attack vector, attack complexity, privileges required, user interaction, confidentiality/integrity/availability impact, CVSS score/severity). Both runs are recorded in full in `v2_bullet/judge/llm_judge_raw.json` (original) and `v2_bullet/judge/llm_judge_raw_faithfulness_ext.json` (extended). The six items below pair the same CVE and arm across both runs, chosen because the original justification flags a CVSS-derived claim (attack vector, privileges required, user interaction, or CIA impact) as unsupported, and the extended-reference run shows that same claim credited as faithful once the reference includes the CVSS sub-fields.

### 1. CVE-2022-3062, baseline arm

| Reference condition | Score | Justification (verbatim) |
|---|---|---|
| Original (description only), pass 1 | 3/5 | "Most claims are supported, including the affected plugin, version, mechanism (lack of escaping parameters), and remediation (update to 4.4.12). However, the reference does not mention attack vector as NETWORK, user interaction being required, attacker privilege requirements, or the specific impact ratings (confidentiality/integrity LOW, availability NONE), so these are unsupported." |
| Extended (description + CVSS), pass 1 | 5/5 | "All claims about the affected product, vulnerable versions, vulnerability mechanism (lack of escaping parameters in attributes), attack vector, required privileges, user interaction, impact ratings, and remediation (update to 4.4.12) are directly supported by the reference text." |

### 2. CVE-2023-43661, persona arm

| Reference condition | Score | Justification (verbatim) |
|---|---|---|
| Original (description only), pass 2 | 3/5 | "Most claims are supported, such as the affected product (Cachet), affected versions (prior to 2.4 branch), vulnerability mechanism (template functionality, bad filtration, old Twig), and remediation (patch commit, update to 2.4 branch). However, several claims are not present in the reference: the attack vector being 'NETWORK', required privileges being 'LOW', no user interaction needed, and the impact ratings (confidentiality, integrity, availability all HIGH) are not mentioned in the reference text." |
| Extended (description + CVSS), pass 1 | 5/5 | "All claims about the affected product (Cachet), affected versions (prior to 2.4 branch), vulnerability mechanism (template functionality, bad filtration, old Twig version, code execution), attack vector, privileges, user interaction, impact, remediation (commit and update), and advisory references are directly supported by the reference text." |

### 3. CVE-2021-30970, persona arm

| Reference condition | Score | Justification (verbatim) |
|---|---|---|
| Original (description only), pass 1 | 3/5 | "Most claims are supported, such as affected versions, the logic issue, bypassing Privacy preferences, and the remediation. However, the reference does not mention the attack vector being LOCAL, user interaction being required, privilege level, or the specific confidentiality/integrity/availability impact ratings; these are not supported by the reference." |
| Extended (description + CVSS), pass 2 | 5/5 | "All claims about affected versions, mechanism (logic issue with state management), exploitation (local attack, user interaction required, no privileges needed, confidentiality impact), and remediation (update to specified versions) are directly supported by the reference text." |

### 4. CVE-2023-29119, persona arm

| Reference condition | Score | Justification (verbatim) |
|---|---|---|
| Original (description only), pass 2 | 3/5 | "The claims about the vulnerable product (Waybox Enel X web management application), the vulnerable endpoint (/admin/dbstore.php), and the ability to execute arbitrary requests on the internal database are supported. However, the reference does not mention the attack vector being ADJACENT_NETWORK, the lack of authentication/user interaction, the CVSS score, or the confidentiality/integrity/availability ratings. The remediation advice to restrict network access and check for updates is not present in the reference." |
| Extended (description + CVSS), pass 2 | 4/5 | "All central claims about the affected product (Waybox Enel X web management application), the vulnerable endpoint (/admin/dbstore.php), the attack vector (ADJACENT_NETWORK), lack of authentication and user interaction, and the CVSS impacts are directly supported. The only minor unsupported detail is the identification of Waybox Enel X as an 'electric vehicle charging station,' which is not stated in the reference." |

### 5. CVE-2021-42013, baseline arm

| Reference condition | Score | Justification (verbatim) |
|---|---|---|
| Original (description only), pass 1 | 3/5 | "Most claims are supported, including affected versions, mechanism (path traversal via Alias-like directives), and the risk of remote code execution if CGI is enabled. However, the reference does not mention the attack vector being 'NETWORK', lack of authentication/user interaction, or provide remediation advice to consult advisories from Fedora, Gentoo, Oracle, Cisco, and NetApp; these are not present in the reference." |
| Extended (description + CVSS), pass 1 | 4/5 | "All central claims about affected versions (2.4.49 and 2.4.50), the path traversal mechanism, the incomplete fix for CVE-2021-41773, the risk of remote code execution if CGI is enabled, and the importance of 'require all denied' are directly supported. The only unsupported detail is the mention of consulting advisories from Fedora, Gentoo, Oracle, Cisco, and NetApp, which is not present in the reference." |

This pair is a partial rather than a full flip: once the CVSS sub-fields are in the reference, the attack-vector/user-interaction claim is credited as supported, but the non-CVSS remediation claim (naming specific vendor advisories) remains unsupported, holding the score at 4 rather than 5.

### 6. CVE-2020-8260, persona arm

| Reference condition | Score | Justification (verbatim) |
|---|---|---|
| Original (description only), pass 1 | 3/5 | "Most claims are supported, including affected product (Pulse Connect Secure), affected versions (<9.1R9), admin web interface, and uncontrolled gzip extraction. However, the reference does not mention attack vector (NETWORK), required privileges (HIGH/admin), user interaction, real-world exploitation, CISA KEV listing, or the need to review admin accounts or consult CISA for remediation. These are moderately important unsupported claims." |
| Extended (description + CVSS), pass 1 | 3/5 | "Most claims are supported, including affected product (Pulse Connect Secure < 9.1R9), mechanism (uncontrolled gzip extraction), attack vector (NETWORK), privileges required (HIGH), and impacts (HIGH for confidentiality, integrity, availability). However, the claim that the vulnerability 'has been observed in real-world attacks and is listed in the CISA Known Exploited Vulnerabilities catalogue' is not present in the reference, nor is the recommendation to 'review administrator accounts' or consult the CISA catalogue for indicators of compromise." |

The numeric score does not move here (3/5 in both runs), which is useful evidence in its own right: it shows the CVSS-derived claims (attack vector, privileges required, impact ratings) are individually credited as supported once the reference is expanded, while the score stays capped by a separate, non-CVSS unsupported claim (KEV/CISA catalogue membership, which Stage 6f deliberately excluded from the expanded reference as external enrichment rather than NVD record data). This isolates the CVSS-scope effect from other sources of the faithfulness gap.

---

## Section 2 — Scope-condition data (readability gains vs source density)

All 24 eval CVEs, from `v2_bullet/metrics/metrics_per_summary_bullet.csv` (`persona` arm rows; `dc_score_nvd` and `dc_score_summary` columns). Improvement = raw NVD Dale-Chall minus persona summary Dale-Chall. Sorted by raw NVD Dale-Chall descending.

| CVE | Raw NVD Dale-Chall | Persona summary Dale-Chall | Improvement |
|---|---|---|---|
| CVE-2023-44221 | 16.469 | 12.047 | 4.422 |
| CVE-2023-50919 | 16.296 | 12.319 | 3.976 |
| CVE-2023-29119 | 16.273 | 11.892 | 4.381 |
| CVE-2021-23894 | 15.437 | 12.535 | 2.901 |
| CVE-2021-37976 | 15.418 | 11.989 | 3.429 |
| CVE-2020-8958 | 14.640 | 12.013 | 2.628 |
| CVE-2024-21887 | 14.591 | 11.725 | 2.867 |
| CVE-2024-3400 | 14.469 | 12.548 | 1.921 |
| CVE-2021-22204 | 14.362 | 12.091 | 2.271 |
| CVE-2020-8260 | 13.998 | 12.245 | 1.753 |
| CVE-2020-8655 | 13.979 | 11.708 | 2.270 |
| CVE-2022-28810 | 13.817 | 12.074 | 1.742 |
| CVE-2021-22717 | 13.805 | 11.975 | 1.830 |
| CVE-2020-8010 | 13.732 | 12.070 | 1.662 |
| CVE-2021-30970 | 13.189 | 12.027 | 1.162 |
| CVE-2021-26084 | 12.877 | 11.543 | 1.334 |
| CVE-2021-21974 | 12.811 | 11.814 | 0.998 |
| CVE-2023-0157 | 12.641 | 11.803 | 0.838 |
| CVE-2022-40765 | 12.625 | 11.510 | 1.115 |
| CVE-2023-21608 | 11.744 | 11.265 | 0.479 |
| CVE-2023-43661 | 11.534 | 11.128 | 0.406 |
| CVE-2021-42013 | 11.514 | 11.753 | −0.240 |
| CVE-2022-3062 | 11.072 | 11.498 | −0.426 |
| CVE-2024-1781 | 10.304 | 12.072 | −1.768 |

Pearson correlation between raw NVD Dale-Chall and improvement (n = 24): **r = 0.982**.

---

## Section 3 — Two worked examples

### Example A — dense source, large improvement: CVE-2023-44221

Raw NVD Dale-Chall 16.469 (highest in the sample), improvement 4.422 (highest in the sample). From `data/eval_sample.jsonl`.

**Raw NVD description (verbatim):**

> Improper neutralization of special elements in the SMA100 SSL-VPN management interface allows a remote authenticated attacker with administrative privilege to inject arbitrary commands as a 'nobody' user, potentially leading to OS Command Injection Vulnerability.

**Generated persona summary (verbatim, from `v2_bullet/summaries/summaries_bullet.json`):**

> ## What is vulnerable
>
> - This affects the SonicWall SMA100 series, a secure remote access appliance, specifically its SSL-VPN management interface.
> - The flaw is an OS command injection vulnerability, which means the management interface does not properly clean special characters out of input before passing it to the operating system.
> - Because of this, an attacker can slip operating system commands into the input, and the system will run them under the "nobody" user account.
> - The "nobody" account is a low-privilege system account, but commands running under it can still affect confidentiality, integrity and availability of the appliance.
>
> ## How it can be exploited
>
> - The attack vector is NETWORK, so an attacker can reach the management interface remotely without needing physical access.
> - Privileges required are HIGH, meaning the attacker must already hold a valid administrative login on the SMA100 management interface before they can attempt this.
> - No user interaction is needed, so once an attacker has admin credentials they can exploit this without anyone else clicking or approving anything.
> - Confidentiality, integrity and availability are all rated HIGH, so a successful attack could let the attacker read sensitive data, modify the system, or disrupt its operation.
>
> ## What action to take
>
> - Check whether any SMA100 appliances in your environment expose their SSL-VPN management interface to the network, and confirm the firmware version running on each.
> - Review the SonicWall advisory linked below for the specific firmware update that addresses this issue and apply it.
> - Because this vulnerability is listed in CISA's Known Exploited Vulnerabilities catalogue, it has been observed in real-world attacks, so treat remediation as a priority.
> - Restrict access to the management interface to trusted networks or IP ranges as an additional safeguard while patching is underway.
>
> ## Reference
>
> SonicWall advisory from the affected vendor:
> https://psirt.global.sonicwall.com/vuln-detail/SNWLID-2023-0018
>
> CISA Known Exploited Vulnerabilities catalogue entry:
> https://www.cisa.gov/known-exploited-vulnerabilities-catalog?field_cve=CVE-2023-44221

### Example B — already-readable source, regression: CVE-2024-1781

Raw NVD Dale-Chall 10.304 (lowest, i.e. most readable, source description in the sample), improvement −1.768 (largest regression in the sample; the summary scored harder to read than the source it was generated from). From `data/eval_sample.jsonl`.

**Raw NVD description (verbatim):**

> A vulnerability was found in Totolink X6000R AX3000 9.4.0cu.852_20230719. It has been rated as critical. This issue affects the function setWizardCfg of the file /cgi-bin/cstecgi.cgi of the component shttpd. The manipulation leads to command injection. The exploit has been disclosed to the public and may be used. The identifier VDB-254573 was assigned to this vulnerability. NOTE: The vendor was contacted early about this disclosure but did not respond in any way.

**Generated persona summary (verbatim, from `v2_bullet/summaries/summaries_bullet.json`):**

> ## What is vulnerable
>
> - This affects the Totolink X6000R AX3000 wireless router running firmware version 9.4.0cu.852_20230719.
> - The flaw is in a function called setWizardCfg, which is part of the file /cgi-bin/cstecgi.cgi served by the router's built-in web server component called shttpd.
> - It is a command injection vulnerability, meaning an attacker can insert operating system commands into input that the router then executes as though they were legitimate instructions.
> - The vendor was contacted about this issue but did not respond, so there is no indication of a fix from Totolink.
>
> ## How it can be exploited
>
> - The attack vector is ADJACENT_NETWORK, which means the attacker needs to be on the same local network segment as the router, for example connected to the same Wi-Fi or LAN.
> - No login credentials and no user interaction are needed, so anyone with adjacent network access can attempt the attack without authentication.
> - Confidentiality, integrity and availability are all rated LOW, meaning the attacker gains limited ability to read data, make changes and disrupt the device rather than full control.
> - A public exploit already exists, which lowers the effort required for someone to attempt this.
>
> ## What action to take
>
> - Check whether any Totolink X6000R AX3000 routers on your network are running firmware version 9.4.0cu.852_20230719.
> - No vendor fix is available at this time because Totolink did not respond to the disclosure.
> - Restrict access to the router's management interface so that only trusted devices on the local network can reach it, and consider whether network segmentation can limit exposure.
> - Monitor the vendor's support pages and the references below for any future firmware update that addresses this issue.
>
> ## Reference
>
> Third-party writeup documenting the vulnerability:
> https://github.com/Icycu123/X6000R-AX3000-Wifi-6-Giga/blob/main/2/X6000R%20AX3000%20WiFi%206%20Giga%E7%84%A1%E7%B7%9A%E8%B7%AF%E7%94%B1%E5%99%A8%E6%9C%AA%E6%8E%88%E6%9D%83rce.md
>
> VulDB entry (CTI details):
> https://vuldb.com/?ctiid.254573
>
> VulDB entry (general):
> https://vuldb.com/?id.254573

---

## Section 4 — Recorded rationale from the methodology log

### 4.1 Stage 6e — known LLM-as-judge biases and mitigations applied

From `METHODOLOGY_LOG.md`, Stage 6e, "Pros and limitations of LLM-as-judge" (verbatim):

> **Limitations, and how this design mitigates them where possible:**
>
> - *Self-evaluation / self-preference bias.* An LLM judge tends to rate text in its own stylistic register more favourably. Mitigated by using a judge from a different provider (OpenAI) than the generator (Anthropic).
> - *Position bias.* LLM judges asked to directly compare two options in the same call are known to favour whichever option is presented first (or second). This design avoids pairwise comparison entirely: every call scores exactly one text in isolation against a fixed rubric, so there is no position for the judge to be biased by. The residual processing-order randomisation (above) is a conservative extra measure, not a correction for a comparison the design does not otherwise perform.
> - *Verbosity bias.* LLM judges are known to rate longer, more elaborated text more favourably independent of actual quality, which matters here since the persona and baseline prompt arms produce summaries of different typical length (see word-count results, Stage 6d). The rubric anchors are written around concrete, checkable content criteria (whether what/how/remediation-scope is present and clear, or whether specific claims are supported) rather than an open-ended holistic quality judgement, and explicitly instructs the judge not to score brevity or style. This reduces but cannot fully eliminate the risk that a more elaborate summary scores higher for its length rather than its content; it is noted here as a residual limitation rather than a solved problem.
> - *Leniency/severity clustering and imperfect determinism.* LLM judges can cluster scores toward one end of a scale, and are not guaranteed to be perfectly deterministic even at temperature 0 depending on backend. Mitigated empirically, not assumed away, by running 3 passes per text per dimension and reporting the observed mean and standard deviation rather than a single score; see `v2_bullet/judge/llm_judge_per_text.csv` for the per-text spread actually observed.
> - *No ground truth for comprehension.* Unlike faithfulness, which has the raw NVD description as a reference, there is no independent ground truth for what a real technically capable non-security reader would understand. The comprehension score is this judge model's estimate of that, not a measurement of an actual reader; the questionnaire-based human evaluation (Stage 8, see below) is the check on this dimension that LLM-as-judge alone cannot provide.

*(Quoted text updated 2026-08-10 to match `METHODOLOGY_LOG.md`'s current wording after Stage 8 was run — see Section 5 below for what that check found.)*

This directly supports reading the flat 5.0/5.0 comprehension ceiling (persona and baseline, SD 0.000 across all 24 CVEs, against raw NVD's 4.01/SD 0.75/range 3–5, per `FINDINGS_LOG.md` Section 2.3) as bounded by a measurement limitation of the judge itself (no ground truth for comprehension, plus the residual verbosity-bias risk given persona and baseline differ in typical length) rather than as an unqualified result.

### 4.2 Xiao et al. persona reasoning (advisory risk-communication trade-off)

Searched `METHODOLOGY_LOG.md`, `STATUS.md`, `FINDINGS_LOG.md`, `CLAUDE.md`, and the prompt files (`v2_bullet/prompts/`) for "Xiao", "security-champion", "risk-communication", "expertise-versus-clarity", and "trade-off" in connection with the persona design. **No such reasoning exists in the recorded files.** The persona prompt (`v2_bullet/prompts/prompt-persona_v2.txt`) opens with "You are a security champion communicating a software vulnerability to a..." but there is no accompanying citation to Xiao et al., and no recorded discussion anywhere in the repository framing the security-champion persona as sitting on a favourable side of an expertise-versus-clarity trade-off. This item cannot be included as requested; it would need to be written from scratch for the Discussion chapter, or sourced from reading notes kept outside this repository, rather than quoted from a prior record.

### 4.3 Stage 7 decisions (four-CVEs-per-participant limit, automated-only comparison)

Searched `METHODOLOGY_LOG.md` for a "Stage 7" covering the human evaluation design. The only Stage 7 in that file is "Stage 7. ChromaDB Ingestion" (embedding model and vector store choice), which is unrelated to participant-facing evaluation design. Searched the whole repository for "PIL", "10 to 15 minute", "four-CVEs-per-participant", and "automated-only" — no matches anywhere. `FINDINGS_LOG.md` Section 3 and `STATUS.md`'s dated notes both independently confirm the human comprehension study (there labelled Stage 8) has not started: no participant, questionnaire, survey, or response files exist in the repository, and the "Design user questionnaire" / "Recruit participants" / "Run evaluation sessions" / "Analyse results" checklist items in `STATUS.md` are all unchecked. **No recorded rationale exists for a four-CVE participant limit, a 10–15 minute PIL time commitment, or a decision to keep the persona-versus-baseline comparison automated-only.** These constraints, if they reflect real planning intent, have not yet been written down anywhere in this repository and would need to be recorded (ideally before the questionnaire is designed) rather than retrieved from an existing source for the Discussion chapter's limitations section.

**Update (2026-08-10, appended — not a correction of the search above, which was accurate as of when it was run):** Stage 8 has since run; see `METHODOLOGY_LOG.md` Stage 8 and `HUMAN_STUDY_FINDINGS.md`. This resolves the four-CVE and time-commitment questions specifically: `data/human_study/survey_source.txt` (which did not exist at the time of the search above) contains the actual participant-facing instructions text, verbatim: *"You will be shown four software vulnerability entries, one at a time... The survey takes approximately 10 to 15 minutes."* This confirms **what** was done (four CVEs, ~10–15 minutes), sourced directly rather than inferred. It does **not** supply the missing piece the original paragraph above was actually asking for: **why** four CVEs specifically, or why the persona-vs-baseline comparison was kept automated-only rather than also run past participants. That strategic rationale is still not recorded anywhere in this repository. If it reflects real planning intent, it still needs to be written down rather than reconstructed after the fact for the Discussion chapter.

---

## Section 5 — Human comprehension study (Stage 8), added 2026-08-10

Sources read for this section: `HUMAN_STUDY_FINDINGS.md` (all sections), `data/human_study/survey_source.txt`. As with the rest of this file, this section gathers evidence and quotes already-recorded reasoning; it does not compute new results.

### 5.1 A participant critique of the project's core premise

`HUMAN_STUDY_FINDINGS.md` §6 records the closing free-text response of `R_50xbc0ffVBVZgV7` (block C, 100% comprehension accuracy in the study — not the view of someone who struggled with either presentation format):

> CVEs are a dumb political system that leads to security and engineering teams getting misleading impressions on the severity of defects. In addition, some vulnerabilities don't get the CVEs they deserve.
>
> Thinking more about the problem: It is generally best practice to look at example exploit code, read advisories published by subject matter experts, and look at source code. Having an LLM summarize a CVE is just deferring responsibility, and hiding the issue that CVEs should just be better structured.

`HUMAN_STUDY_FINDINGS.md` separates this into two claims worth treating independently in the Discussion chapter: (1) a critique of CVE severity scoring as politically/organisationally distorted, aimed at the underlying data source rather than this project's summarisation approach; and (2) a claim that LLM summarisation specifically defers responsibility and obscures a structural problem, rather than fixing it — i.e. that improving comprehension of a flawed record is the wrong intervention next to improving the record itself, or reading primary sources (exploit code, vendor advisories) directly. This is a substantive, expert-adjacent objection to the thesis's framing from a high-scoring participant, and the source doc explicitly recommends representing it as a limitation/counterargument rather than omitting it for being inconvenient to the project's premise.

### 5.2 The human study's NVD condition is not the same artefact as the LLM-judge's faithfulness reference

Section 1 above establishes that Stage 6e's faithfulness evaluation scored LLM summaries against the bare NVD `description` field only, excluding CVSS sub-fields (attack vector, privileges required, user interaction, CIA impact) and KEV/EPSS from the reference — and that most of the resulting "unsupported claim" flags were the judge correctly following its rubric while marking real, sourced CVSS-derived restatements as unsupported, simply because they were absent from that narrow reference text.

The human study's "NVD condition" is a different, broader artefact. Confirmed directly from `data/human_study/survey_source.txt`: a technical-context table (CVE ID, severity, attack vector, privileges required, user interaction, C/I/A impact, KEV status, EPSS score) is displayed above the stimulus text in **both** the NVD and Summary conditions — identically. The only thing that varies between conditions in the human study is the prose narrative (raw description paragraph vs. three-part LLM summary), not the structured CVSS/KEV/EPSS data, which both conditions have equal access to.

This means the human study and the LLM-judge faithfulness evaluation are not comparable presentations of "raw NVD" — one gives readers/the judge only the free-text description, the other gives human readers the description plus the full structured record. **If the Discussion chapter compares human-study results against the LLM-judge's faithfulness findings (or against its "raw NVD" framing generally), this scope difference needs to be stated explicitly** — a reader could otherwise assume both evaluations tested comprehension/faithfulness of the same "raw NVD" object, and they did not.

### 5.3 Comprehension benefit concentrated in the subgroup closest to the target population

`HUMAN_STUDY_FINDINGS.md` §8.2 splits the study's technical-background sample (n=15) by self-reported CVE/CVSS familiarity (`S3`) and finds a clean, monotonic relationship between familiarity and comprehension accuracy (82.1% → 86.7% → 96.7% as familiarity rises) — already a reasonably orderly result on its own. Split further by presentation condition:

| S3 (familiarity) | NVD | Summary | Gap |
|---|---|---|---|
| Never worked with them (n=7) | 78.6% | 85.7% | +7.1pp |
| Seen occasionally (n=5) | 86.7% | 86.7% | 0pp |
| Work with them from time to time (n=3) | 93.3% | 100% | +6.7pp |

The largest NVD-vs-Summary comprehension benefit falls in the least-familiar subgroup — the respondents closest to the thesis's stated target population (`CLAUDE.md`: "technical non-security personnel"). This is a genuinely favourable shape for the thesis's central argument: the intervention appears to help most where it is intended to help. The source document is explicit that this should be reported as a **suggestive, small-n pattern** (the driving cell is 7 respondents / 42 items) rather than a confirmed result, and notes a divergence worth stating alongside it rather than smoothing over: self-reported clarity/confidence does not follow the same shape (it peaks in the *middle* familiarity subgroup and is lowest in the *most*-familiar one, which nonetheless scored best on measured accuracy) — a reminder that self-reported ease and demonstrated comprehension are not interchangeable measures here.
