"""CVE Intelligence Dashboard.

Local Plotly Dash UI over the existing RAG + LLM pipeline: browse the
11,976-CVE rag_corpus, filter/search it, and generate an on-demand
plain-language three-part PERSONA summary ("Explain") for any CVE. Rendering
layer only -- prompts, embeddings, and the ChromaDB collection are not
modified. See src/dashboard_data.py, src/dashboard_search.py, and
src/dashboard_generate.py for the underlying logic.

Run: python app.py, then open http://127.0.0.1:8050
Requires ANTHROPIC_API_KEY in .env (used only when "Explain" is clicked on a
CVE with no cached summary yet).
"""

import csv
import io
import json
import math
import os
import sys
import urllib.parse

from dotenv import load_dotenv

sys.path.insert(0, "src")

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, ctx, dcc, html

from dashboard_data import ATTACK_VECTOR_ORDER, CorpusStore, filter_corpus
from dashboard_generate import SummaryGenerator, ordinal
from dashboard_search import SearchEngine

load_dotenv()

PAGE_SIZE = 10

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# Same hexes as the severity-pill CSS classes in assets/style.css, so the
# overview chart and the list's severity pills read as one system.
SEVERITY_COLORS = {
    "CRITICAL": "#b3261e",
    "HIGH": "#92620a",
    "MEDIUM": "#3d5a80",
    "LOW": "#5b6472",
}

# Colors for the non-severity chart dimensions, picked via the dataviz
# skill's validator (categorical/ordinal checks against a white surface) --
# deliberately not reusing any SEVERITY_COLORS hue so a reader never reads
# "attack vector" or "year" bars as implying a severity meaning.
ATTACK_VECTOR_COLOR = "#008300"
# 5-step validated blue ordinal ramp (light -> dark); bucket-mapped across
# however many distinct years are present, since the documented ramp's named
# steps don't have enough adjacent lightness separation to support one
# distinct step per year cleanly.
YEAR_RAMP = ["#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
EPSS_BAND_ORDER = ["LOW", "MEDIUM", "HIGH"]
EPSS_BAND_COLORS = {"LOW": "#86b6ef", "MEDIUM": "#256abf", "HIGH": "#0d366b"}
EPSS_BAND_LABELS = {
    "LOW": "Low (< 1%)",
    "MEDIUM": "Medium (1–50%)",
    "HIGH": "High (≥ 50%)",
}

CHART_DIMENSION_OPTIONS = [
    {"label": "Severity", "value": "severity"},
    {"label": "Attack vector", "value": "attack_vector"},
    {"label": "Published year", "value": "year"},
    {"label": "Exploitation likelihood (EPSS)", "value": "epss_band"},
]
CHART_DIMENSION_LABELS = {opt["value"]: opt["label"] for opt in CHART_DIMENSION_OPTIONS}

SORT_OPTIONS = [
    {"label": "Newest first", "value": "newest"},
    {"label": "Oldest first", "value": "oldest"},
    {"label": "Severity: Critical → Low", "value": "severity"},
    {"label": "CVSS score: High → Low", "value": "cvss"},
]

print("Loading RAG corpus...")
STORE = CorpusStore()
print(f"Loaded {len(STORE)} CVEs.")

print("Connecting search engine (ChromaDB + embedding model)...")
SEARCH_ENGINE = SearchEngine(STORE)

API_KEY = (os.getenv("ANTHROPIC_API_KEY") or "").strip() or None
SUMMARY_GENERATOR = SummaryGenerator(
    collection=SEARCH_ENGINE.collection,
    embedding_fn=SEARCH_ENGINE.embedding_fn,
    api_key=API_KEY,
) if API_KEY else None

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                 suppress_callback_exceptions=True)
app.title = "CVETranslate"

# The "shield + swap arrows" mark: a single SVG reused as-is for both the
# header logo (build_logo(), rendered via html.Img since this Dash version
# has no native Svg/Rect/Path components) and the browser-tab favicon --
# one source of truth so the two can't drift apart. Gradient runs from a
# teal accent to the app's existing --accent navy so the mark reads as part
# of the same palette used everywhere else, not an unrelated brand color.
_LOGO_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
    "<defs><linearGradient id='cvetGrad' x1='0' y1='0' x2='64' y2='64' "
    "gradientUnits='userSpaceOnUse'>"
    "<stop offset='0' stop-color='#2f9e8f'/>"
    "<stop offset='1' stop-color='#35507d'/>"
    "</linearGradient></defs>"
    "<rect width='64' height='64' rx='14' fill='url(#cvetGrad)'/>"
    "<path d='M32,14 L45,18.5 V31 C45,41 39,47.5 32,51 "
    "C25,47.5 19,41 19,31 V18.5 Z' fill='#ffffff'/>"
    "<line x1='22' y1='26' x2='37' y2='26' stroke='#35507d' "
    "stroke-width='3.2' stroke-linecap='round'/>"
    "<polygon points='35,21.5 42,26 35,30.5' fill='#35507d'/>"
    "<line x1='42' y1='37' x2='27' y2='37' stroke='#2f9e8f' "
    "stroke-width='3.2' stroke-linecap='round'/>"
    "<polygon points='29,32.5 22,37 29,41.5' fill='#2f9e8f'/>"
    "</svg>"
)
LOGO_DATA_URI = "data:image/svg+xml," + urllib.parse.quote(_LOGO_SVG)

app.index_string = f"""<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        <link rel="icon" type="image/svg+xml" href="{LOGO_DATA_URI}">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap" rel="stylesheet">
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>"""


# ---------------------------------------------------------------------------
# Small display helpers
# ---------------------------------------------------------------------------

def humanize(token):
    if not token:
        return "—"
    return token.replace("_", " ").title()


def severity_class(severity):
    return (severity or "").lower()


def options_from(values, label_fn=humanize):
    return [{"label": label_fn(v), "value": v} for v in values]


def severity_pill(severity):
    return html.Span([
        html.Span(className="dot"),
        html.Span(humanize(severity)),
    ], className=f"severity-pill {severity_class(severity)}")


def cvss_badge(record):
    score = record.get("cvss_score")
    severity = record.get("cvss_severity")
    label = f"{score:.1f} {humanize(severity)}" if score is not None else humanize(severity)
    attrs = {}
    if score is not None:
        percentile = STORE.cvss_percentile(score)
        if percentile is not None:
            attrs["data-tooltip"] = f"More severe than {percentile}% of tracked CVEs."
    return html.Span([
        html.Span(className="dot"),
        html.Span(label),
    ], className=f"severity-pill {severity_class(severity)}", **attrs)


KEV_TOOLTIP = ("KEV — CISA Known Exploited Vulnerabilities catalogue: lists "
               "vulnerabilities confirmed to have been exploited in the wild.")
EPSS_TOOLTIP = ("EPSS — Exploit Prediction Scoring System: estimated probability "
                "this vulnerability will be exploited in the next 30 days.")

TECH_FIELD_TOOLTIPS = {
    "Attack vector": "How close an attacker needs to be: Network (remote), "
                      "Adjacent Network (same LAN), Local (on the machine), "
                      "or Physical (in person).",
    "Privileges required": "The access level an attacker needs before they "
                            "can exploit this: None, Low, or High.",
    "User interaction": "Whether a victim needs to do something (e.g. open a "
                         "file, click a link) for the exploit to work.",
    "Attack complexity": "How much extra effort or specific conditions the "
                          "attack needs beyond access alone: Low "
                          "(straightforward) or High.",
    "Confidentiality impact": "Whether exploitation can expose data the "
                               "attacker shouldn't see: None, Low, or High.",
    "Integrity impact": "Whether exploitation can let an attacker modify "
                         "data or code: None, Low, or High.",
    "Availability impact": "Whether exploitation can disrupt or take down "
                            "the system: None, Low, or High.",
    "CWE": "Common Weakness Enumeration — the general category of coding "
           "flaw behind this vulnerability.",
}

FILTER_LABEL_TOOLTIPS = {
    "Privileges": "Filter by the access level an attacker needs before "
                  "they can exploit the vulnerability.",
    "User interaction": "Filter by whether a victim needs to take an "
                         "action (e.g. click a link) for exploitation to "
                         "work.",
    "Operating system": "Filter by the specific operating system or "
                         "firmware platform affected. This list is derived "
                         "from CPE data and includes device firmware, so "
                         "it's long — typing narrows it quickly.",
    "Vendor": "Filter by the vendor of the affected product.",
    "Attack complexity": "Filter by how much extra effort or specific "
                          "conditions the attack needs beyond access alone.",
    "Confidentiality impact": "Filter by whether exploitation can expose "
                               "data the attacker shouldn't see.",
    "Integrity impact": "Filter by whether exploitation can let an "
                         "attacker modify data or code.",
    "Availability impact": "Filter by whether exploitation can disrupt or "
                            "take down the system.",
    "Published within": "Filter to only vulnerabilities published in the "
                         "last 30 or 90 days.",
}


def kev_badge(record):
    is_listed = bool(record.get("kev_listed"))
    label = f"CISA KEV: {'Yes' if is_listed else 'No'}"
    css_class = "kev" if is_listed else "neutral"
    return html.Span([
        html.Span(className="dot"),
        html.Span(label),
    ], className=f"severity-pill {css_class}", **{"data-tooltip": KEV_TOOLTIP})


def epss_badge(record):
    epss_score = record.get("epss_score")
    if epss_score is None or epss_score < 0:
        return None
    label = f"EPSS {epss_score * 100:.2f}%"
    epss_pct = record.get("epss_percentile")
    if epss_pct is not None and epss_pct >= 0:
        label += f" ({ordinal(round(epss_pct * 100))} percentile)"
    band = epss_band(record)
    css_class = f"epss-{band.lower()}" if band else "epss-low"
    return html.Span([
        html.Span(className="dot"),
        html.Span(label),
    ], className=f"severity-pill {css_class}", **{"data-tooltip": EPSS_TOOLTIP})


def build_risk_badges(record):
    badges = [cvss_badge(record), kev_badge(record)]
    epss = epss_badge(record)
    if epss is not None:
        badges.append(epss)
    return html.Div(badges, className="risk-badge-row")


def build_cwe_tags(record):
    """Always-visible CWE summary for the detail view -- the technical-
    details table also has a CWE column, but that's collapsed by default;
    this is the uncramped, primary place to see it without expanding
    anything, showing the full id + name rather than just the name (as the
    space-constrained list-row tags do)."""
    cwe_list = record.get("cwe") or []
    if not cwe_list:
        return html.Div()
    chips = [
        html.Span(f"{c['id']} — {c['name']}", className="tag-chip tag-chip-cwe",
                  **{"data-tooltip": c.get("full_name") or c["name"]})
        for c in cwe_list
    ]
    return html.Div([
        html.Span("CWE:", className="cwe-tags-label"),
        html.Div(chips, className="tag-row"),
    ], className="cwe-tags-row")


# ---------------------------------------------------------------------------
# Layout builders
# ---------------------------------------------------------------------------

def epss_band(record):
    score = record.get("epss_score")
    if score is None or score < 0:
        return None
    if score >= 0.5:
        return "HIGH"
    if score >= 0.01:
        return "MEDIUM"
    return "LOW"


def _year_ramp_colors(years):
    n = len(years)
    if n <= 1:
        return [YEAR_RAMP[-1]] * n
    last = len(YEAR_RAMP) - 1
    return [YEAR_RAMP[round(i * last / (n - 1))] for i in range(n)]


def _chart_series(records, dimension):
    if dimension == "attack_vector":
        counts = {v: 0 for v in ATTACK_VECTOR_ORDER}
        for r in records:
            if r.get("attack_vector") in counts:
                counts[r["attack_vector"]] += 1
        labels = [humanize(v) for v in ATTACK_VECTOR_ORDER]
        values = [counts[v] for v in ATTACK_VECTOR_ORDER]
        colors = [ATTACK_VECTOR_COLOR] * len(ATTACK_VECTOR_ORDER)
    elif dimension == "year":
        years = sorted(STORE.filter_options["year"])
        counts = {y: 0 for y in years}
        for r in records:
            if r.get("year") in counts:
                counts[r["year"]] += 1
        labels = [str(y) for y in years]
        values = [counts[y] for y in years]
        colors = _year_ramp_colors(years)
    elif dimension == "epss_band":
        counts = {b: 0 for b in EPSS_BAND_ORDER}
        for r in records:
            b = epss_band(r)
            if b in counts:
                counts[b] += 1
        labels = [EPSS_BAND_LABELS[b] for b in EPSS_BAND_ORDER]
        values = [counts[b] for b in EPSS_BAND_ORDER]
        colors = [EPSS_BAND_COLORS[b] for b in EPSS_BAND_ORDER]
    else:
        counts = {sev: 0 for sev in SEVERITY_ORDER}
        for r in records:
            if r["cvss_severity"] in counts:
                counts[r["cvss_severity"]] += 1
        labels = [humanize(v) for v in SEVERITY_ORDER]
        values = [counts[v] for v in SEVERITY_ORDER]
        colors = [SEVERITY_COLORS[v] for v in SEVERITY_ORDER]
    return labels, values, colors


def build_overview_chart(records, dimension="severity"):
    labels, values, colors = _chart_series(records, dimension)

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[f"{v:,}" for v in values],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: %{y:,} CVEs<extra></extra>",
        width=0.5,
    ))
    fig.update_layout(
        margin=dict(l=8, r=8, t=8, b=8),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
                  color="#1f2430", size=13),
        showlegend=False,
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor="#e2e5ea")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f1f3", zeroline=False,
                      rangemode="tozero", range=[0, (max(values) * 1.18) or 1])
    return fig


def build_logo():
    """The shield + swap-arrows mark used in the page header, rendered via
    html.Img from the shared LOGO_DATA_URI (this Dash version's html module
    has no native Svg/Rect/Path tags) -- the exact same asset used for the
    browser-tab favicon (see LOGO_DATA_URI, near app.index_string)."""
    return html.Img(src=LOGO_DATA_URI, className="app-logo-badge", alt="CVETranslate logo")


def build_header():
    return html.Div([
        html.Div([
            build_logo(),
            html.Div("CVETranslate", className="app-title"),
        ], className="app-title-row"),
        html.Div(
            "Plain-language CVE summaries for developers — what's vulnerable, "
            "how it's exploited, and what to do, without wading through raw "
            "NVD text.",
            className="app-tagline",
        ),
    ], className="app-header")


def build_filter_bar():
    year_options = options_from(STORE.filter_options["year"], label_fn=str)
    return html.Div([
        html.Div([
            html.Div(
                dcc.Input(
                    id="search-input",
                    type="text",
                    placeholder="Search by keyword or CVE ID…",
                    debounce=True,
                    className="form-control",
                ),
                className="search-input-wrap",
            ),
            html.Div([
                html.Div("Sort by", className="filter-label"),
                dcc.Dropdown(
                    id="sort-dropdown",
                    options=SORT_OPTIONS,
                    value="newest",
                    clearable=False,
                ),
            ], className="sort-control"),
            html.Button("Clear filters", id="clear-filters-btn",
                        className="detail-toggle-btn"),
        ], className="search-row"),

        dbc.Row([
            dbc.Col([
                html.Div("Severity", className="filter-label"),
                dcc.Dropdown(id="severity-dropdown",
                             options=options_from(STORE.filter_options["severity"]),
                             placeholder="Any", clearable=True),
            ], width=3),
            dbc.Col([
                html.Div("Attack vector", className="filter-label"),
                dcc.Dropdown(id="attack-vector-dropdown",
                             options=options_from(STORE.filter_options["attack_vector"]),
                             placeholder="Any", clearable=True),
            ], width=3),
            dbc.Col([
                html.Div("Published", className="filter-label"),
                dcc.Dropdown(id="year-dropdown", options=year_options,
                             placeholder="Any year", clearable=True),
            ], width=3),
            dbc.Col([
                html.Div("CWE", className="filter-label"),
                dcc.Dropdown(
                    id="cwe-dropdown",
                    options=[{"label": f"{c['id']} — {c['name']}", "value": c["id"]}
                             for c in STORE.filter_options["cwe"]],
                    placeholder="Any", clearable=True,
                ),
            ], width=3),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col([
                dcc.Checklist(
                    id="kev-only-checklist",
                    options=[{"label": " Only show CISA KEV-listed", "value": "kev_only"}],
                    value=[], className="kev-only-checklist",
                ),
            ], width=6, className="d-flex align-items-center"),
            dbc.Col([
                html.Button("More filters ▾", id="more-filters-btn",
                             className="more-filters-toggle"),
            ], width=6, className="d-flex align-items-center justify-content-end"),
        ], className="g-3"),

        dbc.Collapse([
            html.Div(className="filter-divider"),
            dbc.Row([
                dbc.Col([
                    html.Div("Privileges", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Privileges"]}),
                    dcc.Dropdown(id="privileges-dropdown",
                                 options=options_from(STORE.filter_options["privileges"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
                dbc.Col([
                    html.Div("User interaction", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["User interaction"]}),
                    dcc.Dropdown(id="user-interaction-dropdown",
                                 options=options_from(STORE.filter_options["user_interaction"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
                dbc.Col([
                    html.Div("Operating system", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Operating system"]}),
                    dcc.Dropdown(id="os-dropdown",
                                 options=options_from(STORE.filter_options["os"], label_fn=lambda v: v),
                                 placeholder="Any", clearable=True),
                ], width=3),
                dbc.Col([
                    html.Div("Vendor", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Vendor"]}),
                    dcc.Dropdown(id="vendor-dropdown",
                                 options=options_from(STORE.filter_options["vendor"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
            ], className="g-3 mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div("Attack complexity", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Attack complexity"]}),
                    dcc.Dropdown(id="attack-complexity-dropdown",
                                 options=options_from(STORE.filter_options["attack_complexity"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
                dbc.Col([
                    html.Div("Confidentiality impact", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Confidentiality impact"]}),
                    dcc.Dropdown(id="confidentiality-impact-dropdown",
                                 options=options_from(STORE.filter_options["confidentiality_impact"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
                dbc.Col([
                    html.Div("Integrity impact", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Integrity impact"]}),
                    dcc.Dropdown(id="integrity-impact-dropdown",
                                 options=options_from(STORE.filter_options["integrity_impact"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
                dbc.Col([
                    html.Div("Availability impact", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Availability impact"]}),
                    dcc.Dropdown(id="availability-impact-dropdown",
                                 options=options_from(STORE.filter_options["availability_impact"]),
                                 placeholder="Any", clearable=True),
                ], width=3),
            ], className="g-3 mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div("Published within", className="filter-label",
                              **{"data-tooltip": FILTER_LABEL_TOOLTIPS["Published within"]}),
                    dcc.Dropdown(
                        id="recency-dropdown",
                        options=[{"label": "Last 30 days", "value": "30"},
                                 {"label": "Last 90 days", "value": "90"}],
                        placeholder="Any time", clearable=True,
                    ),
                ], width=3),
            ], className="g-3"),
        ], id="more-filters-collapse", is_open=False),
    ], className="filter-zone")


def build_stat_cards(matching, critical, kev, active):
    if not active:
        return []
    return [dbc.Row([
        dbc.Col(html.Div([
            html.Div(f"{matching:,}", className="stat-value"),
            html.Div("Matching", className="stat-label"),
        ], className="stat-card"), width=4),
        dbc.Col(html.Div([
            html.Div(f"{critical:,}", className="stat-value"),
            html.Div("Rated critical", className="stat-label"),
        ], className="stat-card critical"), width=4),
        dbc.Col(html.Div([
            html.Div(f"{kev:,}", className="stat-value"),
            html.Div("In CISA KEV", className="stat-label"),
        ], className="stat-card"), width=4),
    ], className="g-3 stat-cards-row")]


def build_tags(record):
    tags = []
    vendor, product = record.get("vendor"), record.get("product")
    if vendor:
        tags.append(html.Span(humanize(vendor), className="tag-chip tag-chip-neutral"))
    # Skip the product chip when it's the same token as vendor (e.g. Netty,
    # Zephyr) -- showing "Netty" "Netty" side by side is redundant, not
    # informative.
    if product and product != vendor:
        tags.append(html.Span(humanize(product), className="tag-chip tag-chip-neutral"))
    cwe_list = record.get("cwe") or []
    for c in cwe_list[:2]:
        tags.append(html.Span(c["name"], className="tag-chip tag-chip-cwe",
                               **{"data-tooltip": c.get("full_name") or c["name"]}))
    if len(cwe_list) > 2:
        tags.append(html.Span(f"+{len(cwe_list) - 2}", className="tag-chip tag-chip-cwe"))
    if not tags:
        return html.Span("—", className="text-muted")
    return html.Div(tags, className="tag-row")


def build_row(record, selected_id):
    row_class = "vuln-table-row selected" if record["id"] == selected_id else "vuln-table-row"
    hover_preview = html.Div([
        build_risk_badges(record),
        build_technical_context_table(record),
    ], className="row-hover-preview")
    return html.Tr([
        html.Td(html.Span([
            html.Span(record["id"], className="cve-id"),
            hover_preview,
        ], className="cve-id-hover"), className="col-cve-id"),
        html.Td(severity_pill(record["cvss_severity"]), className="col-severity"),
        html.Td(build_tags(record), className="col-tags"),
        html.Td(html.Button("Explain", id={"type": "explain-btn", "index": record["id"]},
                             className="explain-btn"), className="col-action"),
    ], className=row_class)


def build_list(page_records, selected_id):
    if not page_records:
        return html.Div([
            html.Div("No CVEs match the current filters."),
        ], className="empty-state")
    header = html.Thead(html.Tr([
        html.Th("CVE ID"), html.Th("Severity"), html.Th("Tags"), html.Th(""),
    ]))
    body = html.Tbody([build_row(r, selected_id) for r in page_records])
    return html.Table([header, body], className="vuln-table")


def build_technical_context_table(record):
    cwe_list = record.get("cwe") or []
    cwe_value = ", ".join(c["id"] for c in cwe_list) if cwe_list else "Not classified"
    fields = [
        ("Attack vector", record.get("attack_vector")),
        ("Privileges required", record.get("privileges_required")),
        ("User interaction", record.get("user_interaction")),
        ("Attack complexity", record.get("attack_complexity")),
        ("Confidentiality impact", record.get("confidentiality_impact")),
        ("Integrity impact", record.get("integrity_impact")),
        ("Availability impact", record.get("availability_impact")),
    ]
    header_cells = [
        html.Th(label, **{"data-tooltip": TECH_FIELD_TOOLTIPS[label]}) for label, _ in fields
    ] + [html.Th("CWE", **{"data-tooltip": TECH_FIELD_TOOLTIPS["CWE"]})]
    value_cells = [html.Td(humanize(value)) for _, value in fields] + [html.Td(cwe_value)]
    return html.Div([
        html.Table([
            html.Thead(html.Tr(header_cells)),
            html.Tbody(html.Tr(value_cells)),
        ], className="tech-table"),
    ], className="tech-table-wrap")


def build_technical_context(record):
    return html.Div([
        html.Button("Show technical details ▾", id="show-tech-details-btn",
                    className="detail-toggle-btn"),
        dbc.Collapse(build_technical_context_table(record), id="tech-details-collapse",
                     is_open=False),
    ], className="disclosure-row")


def build_references(references):
    if not references:
        return html.Div()
    items = [
        html.Li(html.A(ref["label"] or ref["url"], href=ref["url"], target="_blank",
                        rel="noopener noreferrer"))
        for ref in references
    ]
    content = html.Div([
        html.Div("References", className="section-heading"),
        html.Ul(items, className="reference-list"),
        html.Div(
            "Links are as captured in the CVE record; they have not been "
            "re-verified since ingestion.",
            className="reference-caption",
        ),
    ], className="reference-section")
    return html.Div([
        html.Button("Show references ▾", id="show-references-btn",
                    className="detail-toggle-btn"),
        dbc.Collapse(content, id="references-collapse", is_open=False),
    ], className="disclosure-row")


def build_raw_comparison(record):
    nvd_url = f"https://nvd.nist.gov/vuln/detail/{record['id']}"
    content = html.Div([
        html.Div("Original NVD description", className="section-heading"),
        html.P(record["description"], className="raw-description-text"),
        html.A("View this CVE on nvd.nist.gov ↗", href=nvd_url, target="_blank",
               rel="noopener noreferrer", className="nvd-source-link"),
    ], className="raw-description-wrap")
    return html.Div([
        html.Button("Show original NVD description ▾", id="show-raw-btn",
                    className="detail-toggle-btn"),
        dbc.Collapse(content, id="raw-description-collapse", is_open=False),
    ], className="disclosure-row")


def build_cwe_details(record):
    """What each attached CWE actually means -- the always-visible CWE tags
    (build_cwe_tags) give id + name, the hover tooltip gives the full name,
    but neither explains the weakness category itself. MITRE's own
    Description field (fetched once via src/add_cwe_descriptions.py, no LLM
    cost) does. Collapsed by default, same pattern as the other
    secondary-detail toggles; omitted entirely (not just empty) for the
    ~8.8% of CVEs with no CWE, matching build_references()'s precedent."""
    cwe_list = record.get("cwe") or []
    if not cwe_list:
        return html.Div()
    blocks = [
        html.Div([
            html.Div(f"{c['id']} — {c.get('full_name') or c['name']}",
                      className="cwe-detail-heading"),
            html.P(c.get("description") or "No description available for this CWE.",
                   className="cwe-detail-text"),
        ], className="cwe-detail-block")
        for c in cwe_list
    ]
    content = html.Div(blocks, className="cwe-detail-wrap")
    return html.Div([
        html.Button("Show CWE details ▾", id="show-cwe-details-btn",
                    className="detail-toggle-btn"),
        dbc.Collapse(content, id="cwe-details-collapse", is_open=False),
    ], className="disclosure-row")


def build_section(heading, bullets, cue_tags=None):
    heading_children = [heading]
    if cue_tags:
        for tag in cue_tags:
            heading_children.append(html.Span(tag, className="action-cue"))
    return html.Div([
        html.Div(heading_children, className="section-heading"),
        html.Div(
            html.Ul([html.Li(b) for b in bullets], className="bullet-list")
            if bullets else html.Div("Not stated in the source.", className="text-muted"),
            className="section-body",
        ),
    ])


def build_similar_cves(summary, current_id):
    """Proactively surfaces the same nearest-neighbour CVEs already retrieved
    and cached for this summary's generation prompt (summary["neighbours_used"])
    -- no new retrieval call. Unprompted, always-visible delivery (not behind
    a search or a toggle) is what makes this "content context-awareness"
    rather than just another search feature."""
    neighbour_ids = summary.get("neighbours_used") or []
    cards = []
    for nid in neighbour_ids:
        if nid == current_id:
            continue
        neighbour = STORE.get(nid)
        if neighbour is None:
            continue
        cards.append(html.Button([
            html.Span(nid, className="similar-cve-id"),
            severity_pill(neighbour["cvss_severity"]),
            html.Span(neighbour["product_subtitle"], className="similar-cve-subtitle"),
        ], id={"type": "similar-cve-link", "index": nid}, className="similar-cve-card"))
    if not cards:
        return html.Div()
    return html.Div([
        html.Div("Similar vulnerabilities", className="section-heading"),
        html.Div(cards, className="similar-cves-row"),
    ], className="similar-cves-section")


def build_detail_content(record, summary):
    sections = summary["sections"]
    return [
        html.Div([
            html.Div(record["id"], className="cve-id"),
            html.Div(record["product_subtitle"], className="cve-subtitle"),
        ], className="detail-header"),
        build_risk_badges(record),
        build_cwe_tags(record),
        html.Div(className="detail-divider"),
        build_section("What is vulnerable", sections["what_is_vulnerable"]),
        build_section("How it can be exploited", sections["how_it_can_be_exploited"]),
        build_section("What action to take", sections["what_action_to_take"],
                      cue_tags=summary.get("action_cue")),
        build_similar_cves(summary, record["id"]),
        build_raw_comparison(record),
        build_cwe_details(record),
        build_technical_context(record),
        build_references(summary["references"]),
    ]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

app.layout = html.Div([
    html.Div([
        build_header(),

        html.Div([
            html.Div([
                html.Div([
                    html.H4("Distribution", className="card-title"),
                    html.Div(f"{len(STORE):,} CVEs across the full corpus",
                             id="overview-chart-subtitle",
                             className="card-subtitle"),
                    html.Div([
                        dcc.Tabs(
                            id="chart-dimension-dropdown",
                            value="severity",
                            className="chart-tabs",
                            parent_className="chart-tabs-parent",
                            children=[
                                dcc.Tab(label=opt["label"], value=opt["value"],
                                        className="chart-tab",
                                        selected_className="chart-tab--selected")
                                for opt in CHART_DIMENSION_OPTIONS
                            ],
                        ),
                    ], className="chart-tabs-row"),
                ], className="cve-card-header"),
                dcc.Graph(id="overview-chart",
                          figure=build_overview_chart(STORE.records, "severity"),
                          config={"displayModeBar": False},
                          style={"padding": "0 16px 16px"}),
            ], className="cve-card"),

            html.Div([
                html.Div([
                    html.H4("Vulnerabilities", className="card-title"),
                    html.Span(f"· {len(STORE):,} tracked", className="tracked-count"),
                ], className="cve-card-header"),

                build_filter_bar(),

                html.Div(id="stat-cards-container"),
                html.Div(id="list-container"),
                html.Div([
                    html.Button("‹ Previous", id="prev-page-btn",
                                className="page-nav-btn", disabled=True),
                    html.Div("Page 1 of 1", id="page-indicator", className="page-indicator"),
                    html.Button("Next ›", id="next-page-btn",
                                className="page-nav-btn", disabled=True),
                ], className="pagination-row"),
                html.Div([
                    html.Button("⬇ Export CSV", id="csv-export-btn",
                                className="page-nav-btn"),
                    html.Button("⬇ Export JSON", id="json-export-btn",
                                className="page-nav-btn"),
                ], className="export-row"),
            ], className="cve-card"),
        ], id="list-view"),

        html.Div([
            html.Button("← Back to list", id="back-to-list-btn",
                        className="back-to-list-btn"),
            html.Div(
                dcc.Loading(html.Div(id="detail-card-body"), type="circle"),
                className="cve-card",
            ),
        ], id="detail-view", style={"display": "none"}),

        dcc.Store(id="selected-cve-store"),
        dcc.Store(id="page-store", data=0),
        dcc.Store(id="scroll-reset-store"),
        dcc.Download(id="csv-download"),
        dcc.Download(id="json-download"),
    ], className="page-container"),
])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("more-filters-collapse", "is_open"),
    Output("more-filters-btn", "children"),
    Input("more-filters-btn", "n_clicks"),
    State("more-filters-collapse", "is_open"),
)
def toggle_more_filters(n_clicks, is_open):
    if not n_clicks:
        return False, "More filters ▾"
    new_state = not is_open
    label = "Fewer filters ▴" if new_state else "More filters ▾"
    return new_state, label


@app.callback(
    Output("raw-description-collapse", "is_open"),
    Output("show-raw-btn", "children"),
    Input("show-raw-btn", "n_clicks"),
    State("raw-description-collapse", "is_open"),
)
def toggle_raw_description(n_clicks, is_open):
    # detail-card-body is rebuilt from scratch on every CVE selection, so
    # this button remounts with n_clicks=None on every fresh Explain click.
    # Without this guard that remount reads as a real click and the section
    # would silently auto-expand on every new CVE -- the same bug class
    # already fixed for select_cve on 2026-08-04.
    if not n_clicks:
        return False, "Show original NVD description ▾"
    new_state = not is_open
    label = "Hide original NVD description ▴" if new_state else "Show original NVD description ▾"
    return new_state, label


@app.callback(
    Output("cwe-details-collapse", "is_open"),
    Output("show-cwe-details-btn", "children"),
    Input("show-cwe-details-btn", "n_clicks"),
    State("cwe-details-collapse", "is_open"),
)
def toggle_cwe_details(n_clicks, is_open):
    if not n_clicks:
        return False, "Show CWE details ▾"
    new_state = not is_open
    label = "Hide CWE details ▴" if new_state else "Show CWE details ▾"
    return new_state, label


@app.callback(
    Output("tech-details-collapse", "is_open"),
    Output("show-tech-details-btn", "children"),
    Input("show-tech-details-btn", "n_clicks"),
    State("tech-details-collapse", "is_open"),
)
def toggle_tech_details(n_clicks, is_open):
    if not n_clicks:
        return False, "Show technical details ▾"
    new_state = not is_open
    label = "Hide technical details ▴" if new_state else "Show technical details ▾"
    return new_state, label


@app.callback(
    Output("references-collapse", "is_open"),
    Output("show-references-btn", "children"),
    Input("show-references-btn", "n_clicks"),
    State("references-collapse", "is_open"),
)
def toggle_references(n_clicks, is_open):
    if not n_clicks:
        return False, "Show references ▾"
    new_state = not is_open
    label = "Hide references ▴" if new_state else "Show references ▾"
    return new_state, label


def apply_sort(records, sort_by):
    """Applies an explicit user-chosen sort, overriding whatever ordering
    (relevance or newest-first) compute_filtered_results produced by
    default."""
    if sort_by == "oldest":
        return sorted(records, key=lambda r: r["published"])
    if sort_by == "severity":
        return sorted(
            records,
            key=lambda r: SEVERITY_ORDER.index(r["cvss_severity"])
            if r.get("cvss_severity") in SEVERITY_ORDER else len(SEVERITY_ORDER),
        )
    if sort_by == "cvss":
        return sorted(
            records,
            key=lambda r: (r.get("cvss_score") is None, -(r.get("cvss_score") or 0)),
        )
    return records


def compute_filtered_results(severity, attack_vector, year, privileges,
                              user_interaction, os_value, vendor, search_query,
                              cwe=None, attack_complexity=None, confidentiality_impact=None,
                              integrity_impact=None, availability_impact=None,
                              kev_only_value=None, recency=None, sort_by=None):
    """Shared by render_list, export_csv, and export_json so all three apply
    the exact same filter/search logic instead of maintaining copies of it."""
    filtered = filter_corpus(
        STORE.records, severity=severity, attack_vector=attack_vector, year=year,
        privileges=privileges, user_interaction=user_interaction, os=os_value,
        vendor=vendor, cwe=cwe, attack_complexity=attack_complexity,
        confidentiality_impact=confidentiality_impact, integrity_impact=integrity_impact,
        availability_impact=availability_impact,
        kev_only=bool(kev_only_value), recency_days=recency,
    )

    query = (search_query or "").strip()
    if query:
        search_results = SEARCH_ENGINE.search(query) or []
        filtered_ids = {r["id"] for r in filtered}
        results = [r for r in search_results if r["id"] in filtered_ids]
    else:
        results = sorted(filtered, key=lambda r: r["published"], reverse=True)

    if sort_by and sort_by != "newest":
        results = apply_sort(results, sort_by)
    return results


@app.callback(
    Output("list-container", "children"),
    Output("stat-cards-container", "children"),
    Output("overview-chart", "figure"),
    Output("overview-chart-subtitle", "children"),
    Output("page-store", "data"),
    Output("page-indicator", "children"),
    Output("prev-page-btn", "disabled"),
    Output("next-page-btn", "disabled"),
    Input("severity-dropdown", "value"),
    Input("attack-vector-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("privileges-dropdown", "value"),
    Input("user-interaction-dropdown", "value"),
    Input("os-dropdown", "value"),
    Input("vendor-dropdown", "value"),
    Input("search-input", "value"),
    Input("selected-cve-store", "data"),
    Input("chart-dimension-dropdown", "value"),
    Input("prev-page-btn", "n_clicks"),
    Input("next-page-btn", "n_clicks"),
    Input("cwe-dropdown", "value"),
    Input("attack-complexity-dropdown", "value"),
    Input("confidentiality-impact-dropdown", "value"),
    Input("integrity-impact-dropdown", "value"),
    Input("availability-impact-dropdown", "value"),
    Input("kev-only-checklist", "value"),
    Input("recency-dropdown", "value"),
    Input("sort-dropdown", "value"),
    State("page-store", "data"),
)
def render_list(severity, attack_vector, year, privileges, user_interaction,
                 os_value, vendor, search_query, selected_id, dimension,
                 _prev_clicks, _next_clicks, cwe, attack_complexity,
                 confidentiality_impact, integrity_impact, availability_impact,
                 kev_only_value, recency, sort_by, current_page):
    final = compute_filtered_results(
        severity, attack_vector, year, privileges, user_interaction, os_value,
        vendor, search_query, cwe=cwe, attack_complexity=attack_complexity,
        confidentiality_impact=confidentiality_impact, integrity_impact=integrity_impact,
        availability_impact=availability_impact, kev_only_value=kev_only_value,
        recency=recency, sort_by=sort_by,
    )

    active = bool(severity or attack_vector or year or privileges or
                  user_interaction or os_value or vendor or (search_query or "").strip() or
                  cwe or attack_complexity or confidentiality_impact or integrity_impact or
                  availability_impact or kev_only_value or recency)

    matching = len(final)
    critical = sum(1 for r in final if r["cvss_severity"] == "CRITICAL")
    kev = sum(1 for r in final if r.get("kev_listed"))

    dimension_label = CHART_DIMENSION_LABELS.get(dimension, "Severity")
    subtitle = (f"{matching:,} CVEs matching current filters — by {dimension_label}" if active
                else f"{matching:,} CVEs across the full corpus — by {dimension_label}")

    # Pagination: reset to page 1 on a real filter/search change, but
    # preserve the current page across an Explain/Back round trip (matching
    # this project's existing "filter state survives the round trip"
    # precedent) and across a chart-dimension switch (which only changes
    # how the chart is drawn, not which CVEs are in the list).
    total_pages = max(1, math.ceil(matching / PAGE_SIZE))
    current_page = current_page or 0
    triggered_id = ctx.triggered_id
    if triggered_id == "prev-page-btn":
        page = current_page - 1
    elif triggered_id == "next-page-btn":
        page = current_page + 1
    elif triggered_id in ("selected-cve-store", "chart-dimension-dropdown"):
        page = current_page
    else:
        page = 0
    page = max(0, min(page, total_pages - 1))

    page_records = final[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    return (
        build_list(page_records, selected_id),
        build_stat_cards(matching, critical, kev, active),
        build_overview_chart(final, dimension),
        subtitle,
        page,
        f"Page {page + 1} of {total_pages}",
        page == 0,
        page >= total_pages - 1,
    )


EXPORT_FIELDS = [
    "CVE ID", "Published", "Severity", "CVSS score", "Attack vector",
    "KEV listed", "EPSS score", "EPSS percentile", "Vendor", "Product",
    "Affected type", "CWE IDs", "CWE names",
]


def record_to_export_dict(record):
    cwe_list = record.get("cwe") or []
    return {
        "CVE ID": record["id"],
        "Published": record.get("published"),
        "Severity": record.get("cvss_severity"),
        "CVSS score": record.get("cvss_score"),
        "Attack vector": record.get("attack_vector"),
        "KEV listed": bool(record.get("kev_listed")),
        "EPSS score": record.get("epss_score"),
        "EPSS percentile": record.get("epss_percentile"),
        "Vendor": record.get("vendor"),
        "Product": record.get("product_subtitle"),
        "Affected type": record.get("affected_type"),
        "CWE IDs": [c["id"] for c in cwe_list],
        "CWE names": [c["name"] for c in cwe_list],
    }


def build_csv(records):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(EXPORT_FIELDS)
    for r in records:
        row = record_to_export_dict(r)
        writer.writerow([
            ", ".join(row[field]) if isinstance(row[field], list) else row[field]
            for field in EXPORT_FIELDS
        ])
    return buf.getvalue()


def build_json(records):
    return json.dumps([record_to_export_dict(r) for r in records], indent=2)


EXPORT_FILTER_STATES = [
    State("severity-dropdown", "value"),
    State("attack-vector-dropdown", "value"),
    State("year-dropdown", "value"),
    State("privileges-dropdown", "value"),
    State("user-interaction-dropdown", "value"),
    State("os-dropdown", "value"),
    State("vendor-dropdown", "value"),
    State("search-input", "value"),
    State("cwe-dropdown", "value"),
    State("attack-complexity-dropdown", "value"),
    State("confidentiality-impact-dropdown", "value"),
    State("integrity-impact-dropdown", "value"),
    State("availability-impact-dropdown", "value"),
    State("kev-only-checklist", "value"),
    State("recency-dropdown", "value"),
    State("sort-dropdown", "value"),
]


def _export_filtered_results(severity, attack_vector, year, privileges, user_interaction,
                              os_value, vendor, search_query, cwe, attack_complexity,
                              confidentiality_impact, integrity_impact, availability_impact,
                              kev_only_value, recency, sort_by):
    return compute_filtered_results(
        severity, attack_vector, year, privileges, user_interaction, os_value,
        vendor, search_query, cwe=cwe, attack_complexity=attack_complexity,
        confidentiality_impact=confidentiality_impact, integrity_impact=integrity_impact,
        availability_impact=availability_impact, kev_only_value=kev_only_value,
        recency=recency, sort_by=sort_by,
    )


@app.callback(
    Output("csv-download", "data"),
    Input("csv-export-btn", "n_clicks"),
    *EXPORT_FILTER_STATES,
    prevent_initial_call=True,
)
def export_csv(_n_clicks, *filter_state):
    final = _export_filtered_results(*filter_state)
    return dcc.send_string(build_csv(final), filename="cve_results.csv")


@app.callback(
    Output("json-download", "data"),
    Input("json-export-btn", "n_clicks"),
    *EXPORT_FILTER_STATES,
    prevent_initial_call=True,
)
def export_json(_n_clicks, *filter_state):
    final = _export_filtered_results(*filter_state)
    return dcc.send_string(build_json(final), filename="cve_results.json")


@app.callback(
    Output("selected-cve-store", "data", allow_duplicate=True),
    Input({"type": "explain-btn", "index": ALL}, "n_clicks"),
    Input({"type": "similar-cve-link", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def select_cve(_explain_clicks, _similar_clicks):
    triggered = ctx.triggered_id
    if not triggered:
        return dash.no_update
    # Pattern-matching Explain / Similar-CVE buttons are recreated every time
    # the list or detail view re-renders, and a freshly-mounted button
    # reports n_clicks=None. Without this guard that mount event is
    # indistinguishable from a real click and silently auto-selects a CVE
    # with no click at all.
    triggered_value = ctx.triggered[0]["value"]
    if not triggered_value:
        return dash.no_update
    return triggered["index"]


@app.callback(
    Output("list-view", "style"),
    Output("detail-view", "style"),
    Output("detail-card-body", "children"),
    Input("selected-cve-store", "data"),
    prevent_initial_call=True,
)
def render_detail(cve_id):
    if not cve_id:
        return {"display": "block"}, {"display": "none"}, []

    record = STORE.get(cve_id)
    if record is None:
        return {"display": "none"}, {"display": "block"}, [html.Div(
            "CVE not found in the corpus.", className="detail-error")]

    if SUMMARY_GENERATOR is None:
        return {"display": "none"}, {"display": "block"}, [html.Div(
            "ANTHROPIC_API_KEY is not set in .env, so a summary cannot be "
            "generated for this CVE.", className="detail-error",
        )]

    try:
        summary = SUMMARY_GENERATOR.get_or_generate(record)
    except Exception as e:
        return {"display": "none"}, {"display": "block"}, [html.Div(
            f"Could not generate a summary for {cve_id}: {e}",
            className="detail-error",
        )]

    try:
        content = build_detail_content(record, summary)
    except Exception as e:
        return {"display": "none"}, {"display": "block"}, [html.Div(
            f"Could not display the summary for {cve_id}: {e}",
            className="detail-error",
        )]

    return {"display": "none"}, {"display": "block"}, content


# List-view and detail-view are the same long page with one hidden via
# style.display -- there's no route change, so the browser keeps whatever
# scroll position you had on the list. If that was scrolled down (a very
# normal thing to do before clicking Explain on a row further down), the
# detail view opens already scrolled past its own CVE-ID header. Reset to
# the top on every switch, either direction.
app.clientside_callback(
    "function(_) { window.scrollTo(0, 0); return ''; }",
    Output("scroll-reset-store", "data"),
    Input("selected-cve-store", "data"),
    prevent_initial_call=True,
)


@app.callback(
    Output("selected-cve-store", "data", allow_duplicate=True),
    Input("back-to-list-btn", "n_clicks"),
    prevent_initial_call=True,
)
def back_to_list(_n_clicks):
    return None


@app.callback(
    Output("severity-dropdown", "value"),
    Output("attack-vector-dropdown", "value"),
    Output("year-dropdown", "value"),
    Output("privileges-dropdown", "value"),
    Output("user-interaction-dropdown", "value"),
    Output("os-dropdown", "value"),
    Output("vendor-dropdown", "value"),
    Output("cwe-dropdown", "value"),
    Output("attack-complexity-dropdown", "value"),
    Output("confidentiality-impact-dropdown", "value"),
    Output("integrity-impact-dropdown", "value"),
    Output("availability-impact-dropdown", "value"),
    Output("kev-only-checklist", "value"),
    Output("recency-dropdown", "value"),
    Output("search-input", "value"),
    Input("clear-filters-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_all_filters(_n_clicks):
    return None, None, None, None, None, None, None, None, None, None, None, None, [], None, ""


if __name__ == "__main__":
    # Defaults reproduce the previous local behavior (python app.py ->
    # http://127.0.0.1:8050, debug on). A container deployment overrides
    # these via env vars (HOST=0.0.0.0, PORT=<platform port>, DASH_DEBUG=0 --
    # debug mode's live-reload/debugger has no place on a public host).
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 8050)),
        debug=os.environ.get("DASH_DEBUG", "1") == "1",
    )
