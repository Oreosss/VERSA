"""Capture screenshots of the live dashboard for the usability LLM-judge.

Drives the running Dash app (start it separately with `python app.py`,
default http://127.0.0.1:8050/) through eight representative states with
real corpus data and saves one PNG per state to `v2_bullet/screenshots/`.
These are the images `src/llm_judge_usability.py` scores against
`v2_bullet/rubric/rubric_usability.txt`.

v2 note (2026-08-13): this is the re-run after three usability fixes
(tooltips on the technical-details headers and "More filters" labels; a
"Clear all filters" button on the zero-result state). States 1-6 are
unchanged from v1 (`v2_bullet/screenshots_v1/`), byte-for-byte the same
capture logic, for a clean paired before/after comparison. States 7-8 are
new: two of the three fixes are CSS `:hover`-only tooltips, invisible to
any static screenshot that doesn't explicitly trigger a hover, so without
these two states the tooltip fixes would be entirely invisible to this
evaluation method. They're supplementary evidence, not part of the paired
1-6 comparison, since v1 has no counterpart to diff them against -- see
`src/llm_judge_usability.py` for how they're scored.

The eight states, and why each is included:

1. initial_load       -- default list view, no filters. Baseline for
                          visibility of system status / recognition rather
                          than recall.
2. filtered_search     -- severity + KEV filters applied, "More filters"
                          panel open. Exercises flexibility/efficiency.
3. explain_summary      -- detail view for a specific CVE with the
                          generated ("Explain") summary open.
4. raw_nvd_toggle       -- same detail view with the raw-NVD description
                          disclosure expanded. Evidences Objective 3's
                          verification requirement; NOTE this is a
                          sequential disclosure toggle, not a side-by-side
                          comparison view -- see the correction note in
                          DASHBOARD_USABILITY_WRITEUP.md re: Table 2.1.
5. all_expanded         -- same detail view with every disclosure section
                          open at once (tech details, references, CWE
                          details, raw NVD). Stress-tests whether
                          progressive disclosure holds up or the panel
                          becomes cluttered.
6. empty_state          -- a filter combination with zero matches, to
                          exercise error prevention / error recovery, which
                          otherwise go untested. v2: now shows the "Clear
                          all filters" button added after v1.
7. tooltip_tech_details -- (v2 only, supplementary) technical-details
                          section expanded, mouse hovered over the "Attack
                          vector" header, showing the new tooltip.
8. tooltip_filter_label -- (v2 only, supplementary) "More filters" panel
                          open, mouse hovered over the "Operating system"
                          label, showing the new tooltip.

Uses a fixed CVE (CVE-2026-46340 -- HIGH severity, Netty, resource-limits
weakness) for states 3-5, 7 so the run is reproducible. Note: the 24
evaluation-sample CVEs (e.g. CVE-2024-3400) are deliberately excluded from
the RAG corpus the dashboard reads (`data/rag_corpus_final.jsonl`), so they
do not appear in the dashboard and cannot be used here.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

APP_URL = "http://127.0.0.1:8050/"
OUT_DIR = Path("v2_bullet/screenshots")
VIEWPORT = {"width": 1440, "height": 1000}
DETAIL_CVE = "CVE-2026-46340"


def wait_settled(page, ms=800):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def shoot(page, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"saved {path}")


def hide_dev_tools(page):
    """app.py runs with debug=True (app.py:1201), which overlays a Dash
    dev-tools menu (errors/callbacks/version) bottom-right of every page.
    That's debug-only chrome a real user or examiner running the deployed
    app would never see, and it visibly covers content (e.g. the vendor
    filter) in some states, so it's hidden here rather than scored."""
    page.add_style_tag(content=".dash-debug-menu__outer { display: none !important; }")


def capture_initial_load(page):
    page.goto(APP_URL, wait_until="networkidle")
    hide_dev_tools(page)
    wait_settled(page)
    shoot(page, "1_initial_load")


def select_dropdown_option(page, dropdown_id, option_label):
    """Dash's dcc.Dropdown is a Radix-based button+listbox, not a native
    <select>, so playwright's select_option doesn't apply -- open it and
    click the matching role=option instead."""
    page.click(f"#{dropdown_id}")
    page.wait_for_timeout(300)
    page.get_by_role("option", name=option_label, exact=True).click()
    page.wait_for_timeout(300)


def capture_filtered_search(page):
    # HIGH + KEV-only is broad enough to return real rows (verified: 10
    # matches). Critical + Network + KEV, tried first, returned zero and
    # would have accidentally turned this into a second empty-state shot.
    select_dropdown_option(page, "severity-dropdown", "High")
    page.click("#kev-only-checklist input[type='checkbox']")
    page.click("#more-filters-btn")
    page.wait_for_timeout(300)
    wait_settled(page)
    shoot(page, "2_filtered_search")

    # reset filters before moving on
    page.reload(wait_until="networkidle")
    hide_dev_tools(page)
    wait_settled(page)


def open_detail(page, cve_id):
    page.fill("#search-input", cve_id)
    page.press("#search-input", "Enter")
    page.wait_for_timeout(800)
    explain_btn = page.query_selector(f"button[id*='{cve_id}']")
    if explain_btn is None:
        raise RuntimeError(f"Could not find Explain button for {cve_id}")
    explain_btn.click()
    page.wait_for_selector("#detail-view", state="visible", timeout=20000)
    wait_settled(page, ms=1500)


def capture_explain_summary(page):
    open_detail(page, DETAIL_CVE)
    shoot(page, "3_explain_summary")


def capture_raw_nvd_toggle(page):
    page.click("#show-raw-btn")
    page.wait_for_timeout(400)
    shoot(page, "4_raw_nvd_toggle")


def capture_all_expanded(page):
    for btn_id in ("#show-tech-details-btn", "#show-references-btn", "#show-cwe-details-btn"):
        btn = page.query_selector(btn_id)
        if btn:
            btn.click()
            page.wait_for_timeout(300)
    shoot(page, "5_all_expanded")


def capture_empty_state(page):
    page.click("#back-to-list-btn")
    page.wait_for_timeout(500)
    page.fill("#search-input", "")
    page.press("#search-input", "Enter")
    page.wait_for_timeout(400)
    select_dropdown_option(page, "severity-dropdown", "Low")
    page.click("#kev-only-checklist input[type='checkbox']")
    wait_settled(page)
    shoot(page, "6_empty_state")


def capture_tooltip_tech_details(page):
    """Supplementary (v2 only): the technical-details tooltip fix is
    CSS :hover-only, so this explicitly hovers a header to make it visible
    to a static screenshot at all."""
    page.reload(wait_until="networkidle")
    hide_dev_tools(page)
    wait_settled(page)
    open_detail(page, DETAIL_CVE)
    page.click("#show-tech-details-btn")
    page.wait_for_timeout(400)
    # build_row's hover-preview also renders a (hidden) technical-details
    # table, so .tech-table th[data-tooltip] matches both it and the real,
    # visible one in the detail panel -- filter to the visible match.
    # Also: the tooltip is centered on its header (assets/style.css:304-305,
    # 260px max-width), so the leftmost column ("Attack vector") clips off
    # the left edge of the viewport -- hover a middle column instead.
    headers = page.query_selector_all(".tech-table th[data-tooltip]")
    header = next(
        (h for h in headers if h.is_visible() and h.inner_text().strip().lower() == "confidentiality impact"),
        None,
    )
    if header is None:
        raise RuntimeError("Could not find a visible 'Confidentiality impact' tech-details header")
    header.hover()
    page.wait_for_timeout(300)
    shoot(page, "7_tooltip_tech_details")


def capture_tooltip_filter_label(page):
    """Supplementary (v2 only): same reasoning as above, for the "More
    filters" panel label tooltips."""
    page.reload(wait_until="networkidle")
    hide_dev_tools(page)
    wait_settled(page)
    page.click("#more-filters-btn")
    page.wait_for_timeout(300)
    label = page.query_selector(".filter-label[data-tooltip]")
    if label is None:
        raise RuntimeError("Could not find a tooltip-bearing filter label")
    label.hover()
    page.wait_for_timeout(300)
    shoot(page, "8_tooltip_filter_label")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        capture_initial_load(page)
        capture_filtered_search(page)
        capture_explain_summary(page)
        capture_raw_nvd_toggle(page)
        capture_all_expanded(page)
        capture_empty_state(page)
        capture_tooltip_tech_details(page)
        capture_tooltip_filter_label(page)
        browser.close()


if __name__ == "__main__":
    main()
