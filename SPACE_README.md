---
title: CVETranslate
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# CVETranslate

An LLM-powered CVE Intelligence Dashboard. Browse CVEs enriched with CISA KEV
and FIRST EPSS data, and generate a plain-language three-part explanation
(what's vulnerable, how it's exploited, what to do about it) for any of them
via RAG-based summarisation.

Built as part of an MSc Cyber Security Management thesis (University of
Warwick, WMG).

Note: summaries are generated live via the Anthropic API for any CVE not
already cached. If the API key on this Space runs out of credit, "Explain"
will show an error message for uncached CVEs instead of a summary.
