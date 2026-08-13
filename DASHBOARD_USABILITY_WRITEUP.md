# Dashboard usability (LLM-as-judge): drop-in content for the dissertation

Generated from a real judge run (`src/llm_judge_usability.py`, `gpt-4.1-2025-04-14`,
6 screenshots x 3 passes, 18/18 calls succeeded). Raw data: `v2_bullet/judge/llm_judge_usability_raw.json`,
`llm_judge_usability_per_screenshot.csv`, `llm_judge_usability_aggregate.json`. Figure:
`v2_bullet/figures/llm_judge_usability_bullet.png` / `.svg`. Full rubric and design rationale
already logged verbatim in `METHODOLOGY_LOG.md` under "Dashboard Usability -- LLM-as-Judge Evaluation".

Each section below is written to be pasted into the corresponding chapter with minimal editing.
Numbers are copied directly from the run's own output files -- check them against
`LLM_JUDGE_USABILITY_COMPARISON.md` before submitting if this file and that one ever drift apart.

---

## 0. Correction to fix in Table 2.1 before submission

Verified directly against `app.py:623-631` while scoping this evaluation: the "summary-vs-raw
view" cell in Table 2.1 overstates what the dashboard actually does. `build_raw_comparison()` is a
collapsible disclosure toggle ("Show original NVD description (dropdown arrow)") that reveals the raw
text in place, underneath the summary, one at a time -- not a side-by-side or split-pane comparison.
Screenshot `4_raw_nvd_toggle.png` shows this directly. The underlying claim is still true (a user can
see both the summary and the raw description for a CVE, which is what Objective 3's verification
requirement asks for), but "view" implies simultaneous display, which is not what is built.

**Suggested fix**, Table 2.1, "This study" row, second column:

- Current: *"Yes, filtering, overview and summary-vs-raw view"*
- Suggested: *"Yes, filtering, overview and a raw-NVD disclosure toggle"*

Worth doing before submission -- an examiner who runs the tool and looks for a split-screen
comparison won't find one, and the corrected wording is still a genuine differentiator against
every comparator in the table (none of them offer even a disclosure toggle back to source).

---

## 1. Methodology addition -- drop-in for a new §3.4.5

*(Follows the existing §3.4.4 Human comprehension study. Voice matched to §3.4.3.)*

### 3.4.5 Dashboard usability evaluation (LLM-as-judge)

The first three evaluation methods in this chapter all assess the generated summary text. None of
them evaluate the dashboard the summaries are surfaced through, even though Objective 3 commits to
delivering that dashboard and Table 2.1 names it as part of what distinguishes this tool from every
comparator system. A fourth method closes that gap: a heuristic evaluation of the live dashboard,
scored by an independent language model against Nielsen's ten usability heuristics (Nielsen 1994).

Heuristic evaluation is an inspector-based method: an evaluator walks an interface and checks it
against a fixed set of established usability principles, rather than recruiting end users to perform
tasks. This suited the dashboard for two reasons. First, it is the same method already applied once,
informally and without record, during development (an ad hoc "Nielsen-style walkthrough" of the
running app). This evaluation formalises and repeats that walkthrough with multiple independent
passes rather than introducing an unrelated method. Second, it does not require recruiting
additional participants beyond those already used for the human comprehension study, which matters
under the project's time constraint.

Six representative states of the live dashboard were captured with a headless browser (Playwright),
using real corpus data rather than the pre-build wireframes in `mock-ups/`: the default list view;
a filtered list view with the "more filters" panel open; a CVE detail view with the generated
summary; the same detail view with the raw-NVD disclosure toggle open; the same detail view with
every disclosure section open at once, to stress-test whether progressive disclosure holds up under
load; and a zero-result filter combination, to exercise error-handling, which the other five states
do not. Each screenshot was scored by the judge model against all ten heuristics in a single call,
given the screenshot under evaluation plus the other five as supporting context, since heuristics
such as consistency cannot be judged validly from one isolated frame. Each screenshot was scored
three times at temperature zero, the same stability check used for the text judge in §3.4.3.

The judge model was OpenAI's `gpt-4.1-2025-04-14`, the same model and provider used in §3.4.3, for
the same reason: it comes from a different provider than the Anthropic model that generates the
summaries and built the dashboard's content, so no model evaluates output associated with its own
family. Unlike §3.4.3, this evaluation is not blinded, because there is only one dashboard design
under inspection, not multiple arms to keep the judge from distinguishing; this is a single-system
inspection, not a comparison, which is consistent with how heuristic evaluation is normally applied.

This evaluation is a computational method involving no human participants and required no amendment
to the study's ethics approval (§3.6); it is reported here as a fourth, independent evaluation
method alongside, not part of, the human comprehension study.

---

## 2. Findings addition -- drop-in for a new §4.6

*(Insert before the current §4.5 "Summary of Findings", which becomes §4.7. Voice matched to §4.3.)*

### 4.6 Dashboard Usability (LLM-as-Judge)

The dashboard was scored by an independent judge against Nielsen's ten usability heuristics, using
the method set out in §3.4.5. Six screenshots were each scored three times; Table 4.4 gives the mean
score (1-5) for each heuristic across all eighteen scoring passes, ordered lowest to highest.
Figure 4.7 shows the same result.

**Table 4.4: Mean judge score by heuristic, across 6 screenshots x 3 passes (n = 18 scoring
instances per heuristic).**

| Heuristic | Mean | SD (across screenshots) |
|---|---|---|
| Help users recognize, diagnose, and recover from errors | 3.17 | 0.41 |
| Help and documentation | 3.17 | 0.41 |
| Error prevention | 3.50 | 0.55 |
| Flexibility and efficiency of use | 4.00 | 1.10 |
| Recognition rather than recall | 4.06 | 0.65 |
| Match between system and the real world | 4.17 | 0.41 |
| User control and freedom | 4.67 | 0.52 |
| Visibility of system status | 4.83 | 0.41 |
| Aesthetic and minimalist design | 4.83 | 0.41 |
| Consistency and standards | 5.00 | 0.00 |

**Figure 4.7: Dashboard usability, mean judge score by Nielsen heuristic
(`v2_bullet/figures/llm_judge_usability_bullet.png`).**

Scores were highly stable within each screenshot: of the 60 (screenshot, heuristic) cells, the
within-screenshot standard deviation across the three passes was 0.00 for all but two cells, both on
the raw-NVD-toggle and recognition-rather-than-recall combination (SD = 0.58) -- the same stability
pattern already observed for the text judge in §4.3.3.

Consistency and standards scored the maximum on every screenshot (5.00, SD 0.00): the judge reported
that interactive elements -- buttons, toggles, badges, dropdowns -- looked and behaved the same way
across every state shown. Visibility of system status and aesthetic and minimalist design were the
next highest (4.83 each). Aesthetic and minimalist design is worth breaking out by screen: it scored
the maximum (5.00) on every screenshot except one, the fully-expanded detail view, where it dropped
to 4.00. That screen was built specifically to stress-test whether progressive disclosure -- keeping
technical details, references, CWE details, and the raw description behind toggles rather than shown
by default -- actually keeps the interface uncluttered when a user chooses to open everything at
once. The one-point drop on exactly that screen, and nowhere else, is evidence the design choice is
doing what it was intended to do, without erasing the cost of opening everything simultaneously.

Flexibility and efficiency of use had the widest spread of any heuristic (SD = 1.10): it scored the
maximum (5.00) on the two list-view screens and the empty-state screen, but only 3.00 on all three
detail-view screens. The judge's justification was consistent across passes: the list view's
filtering, search, and sorting controls let a user narrow results quickly, but the detail view
offers little beyond navigating back, which is a reasonable reading of what a single-record view is
for, though it means the flexibility the list view offers does not carry into the detail view.

The two lowest-scoring heuristics were help and documentation and error recovery, both at 3.17. For
help and documentation, the judge's justification was consistent across five of the six screenshots:
there are no visible tooltips or inline explanations for badges, scores, or acronyms such as EPSS or
CISA KEV, so a reader without security background who does not already know these terms has no
in-context way to look them up. The one exception was the summary screen itself (score 4), where the
judge noted "most terms are explained in context" by the generated summary text, but that the badge
row above it (EPSS, CISA KEV) is not. For error recovery, five of the six screenshots do not contain
an error or empty state at all, so the judge correctly scored these 3 (the rubric's defined
not-applicable case) rather than guessing; the one screenshot that does show an empty state (the
zero-result filter combination) scored 4, with the judge noting the empty-state message is clear but
offers no explicit shortcut to reset the filters that caused it.

Full per-screenshot detail for all ten heuristics is in `v2_bullet/judge/LLM_JUDGE_USABILITY_COMPARISON.md`.

---

## 3. Addition for §3.5 Reliability and Validity

*(Insert as a new paragraph, after the existing paragraph on the independent judge's reliability.)*

The dashboard usability judge (§3.4.5) was checked for stability the same way: three passes per
screenshot at temperature zero, with the observed spread reported rather than assumed away (§4.6).
Its validity is more limited than the text judge's, in one specific respect worth stating plainly.
Nielsen's heuristic evaluation method assumes multiple independent evaluators, since different
evaluators tend to catch different subsets of usability problems; repeated passes from the same
model, however stable, are not equivalent to that diversity, and may share the same blind spots
however many times the evaluation is repeated. Nor does this method involve a real user completing a
real task on the live dashboard -- the closest the project comes to that is the human comprehension
study (§3.4.4), which used static rendered stimuli, not the dashboard itself. The usability judge is
therefore reported as a structured, repeatable proxy for a expert inspection, not as a substitute for
either a multi-evaluator heuristic review or a live-dashboard user study; both remain open validity
gaps, noted here rather than left implicit.

---

## 4. Discussion draft -- for Chapter 5

*(Chapter 5 is currently empty. This is a self-contained subsection that can be dropped in as-is,
or split across wherever the finished chapter organises its material on the tool's design and its
limitations.)*

### The dashboard's contribution, now evidenced rather than asserted

Table 2.1 named a "visual triage dashboard" as what separates this tool from every comparator
system reviewed in Chapter 2: ChatNVD's chatbot has no visual overview, SAFE is scoped to
in-IDE code explanation, VulnScore and CAVP are built for security teams rather than non-security
readers. Until the evaluation in §4.6, that claim rested on the dashboard existing, not on any
assessment of whether it works well for the audience it targets. The heuristic scores go some way to
closing that gap: the dashboard scored strongly on consistency, status visibility, and (with one
deliberate exception) minimal clutter, which supports treating the visualisation layer as a genuine
asset rather than a decorative addition to the summarisation pipeline. That said, the two weakest
heuristics -- help and documentation, and error recovery -- are not minor. A reader with no security
background is exactly the population this thesis is written for, and exactly the population least
able to independently look up what "EPSS" or "CISA KEV" mean when the interface itself doesn't say.
The plain-language summary text solves this for the *body* of a CVE record; the surrounding
dashboard chrome -- badges, filters, stat cards -- has not yet had the same treatment, and this
evaluation is what surfaces that as a specific, addressable gap rather than a vague impression.

### Visualization's Level 1 strength, and where this tool sits against it

Section 2.2 discussed Jiang et al.'s (2022) finding that security visualisation tools support
perception (Level 1 of Endsley's framework) far more effectively than comprehension (Level 2): 92.6%
against 53.7% in their sample. This thesis's design deliberately does not ask the dashboard to close
that Level 2 gap by itself -- that is the job of the LLM-generated summary, evaluated separately in
§4.3 and §4.4. The usability evaluation in §4.6 is best read as a check on whether the dashboard is
at least doing its own job well: surfacing, filtering, and triaging vulnerability records (Level 1),
without getting in the way of the plain-language explanation once a user drills into one (the
hand-off from Level 1 to Level 2). The consistency and visibility scores suggest the Level 1 side is
solid; the flexibility-of-use drop between the list and detail views suggests the hand-off itself
could be smoother, since the triage tools available while scanning don't carry into the record a
user has actually opened.

### Verification and automation bias

Section 2.3.4 raised automation bias -- the risk that users trust LLM-generated output without
independent verification -- as a risk this thesis's design tries to mitigate by keeping the raw NVD
description one click away rather than removing it. The usability evaluation gives some support for
that design choice actually functioning as intended: user control and freedom scored 4.67, and the
raw-NVD screenshot specifically was judged to make the underlying source easy to reach and easy to
close again. What the evaluation cannot show is whether users actually use that affordance in
practice, rather than reading the summary and moving on; that is a question for a live-dashboard user
study, not for a heuristic inspection, and is noted as exactly that kind of open question in §3.5.

### Honest limitation

None of the above should be read as a substitute for testing the dashboard with real users. It is a
structured, repeatable, and -- per §4.6 -- internally stable proxy for one, run under this project's
time constraint rather than in place of a study that was never in scope to begin with. The two
consistent weak points it surfaced (in-context help for domain terms; a clearer recovery path from a
zero-result filter state) are concrete enough to be worth fixing regardless of whether a future study
confirms them with real users, which is arguably the most useful thing a heuristic evaluation can
offer a project at this stage.
