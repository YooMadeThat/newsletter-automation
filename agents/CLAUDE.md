# agents/CLAUDE.md — Agent Roles & Data Contracts

All rules are enforced via `harness.py`. Do not define rules inside
agent files. See root `CLAUDE.md` for hard rules that apply everywhere.

---

## Agent Roles

| Agent | File | API | Input | Output |
|---|---|---|---|---|
| Research | `research_agent.py` | Perplexity sonar-pro | Search queries | `raw_YYYYMMDD.json` |
| Triage | `triage_agent.py` | Claude sonnet-4-6 | `raw_YYYYMMDD.json` | `triage_YYYYMMDD.json` |
| Summarise | `summarise_agent.py` | Claude sonnet-4-6 | `triage_YYYYMMDD.json` | `briefs_YYYYMMDD.json` |
| Compose | `compose_agent.py` | Claude sonnet-4-6 | `briefs_YYYYMMDD.json` | `newsletter_YYYYMMDD.md` |
| Format | `format_agent.py` | None (python-docx) | `newsletter_YYYYMMDD.md` | `newsletter_YYYYMMDD.docx` |

Agents hand off via JSON files only. No agent calls another directly.

---

## Persona Definitions

Each shortlisted item is assigned exactly one persona. Justify in one sentence.

**Debbie** — Strategy, accountability, defensibility, outcomes.
Assign when the item has implications for how policy is designed, how
accountability is structured, or how organisations defend decisions to
ministers, boards, or the public.

**Inia** — Evidence, methods, implementation, sound decisions.
Assign when the item concerns how analysis is done, how evidence is gathered
or weighted, how implementation is structured, or how decisions are made robust.

**Pete** — Clarity, practicality, reducing ambiguity, delivery.
Assign when the item concerns operational clarity, reducing regulatory
ambiguity, practical guidance for agencies, or how implementation gets done.

---

## A+C Practice Areas (Relevance Anchors for Triage)

- Policy development and reform
- Regulatory analysis and design
- Stakeholder engagement and consultation
- Cross-agency coordination and governance
- Implementation planning and support
- Monitoring, evaluation, and reporting

Items with no connection to any of these areas score zero for A+C relevance.

---

## Data Contract — JSON Field Names

Use constants from `harness.py`. Do not improvise field names.

### raw_YYYYMMDD.json
```
title, url, source_name, published_date, snippet,
jurisdiction_tag, is_paywalled, query_used
```

### triage_YYYYMMDD.json
```
rank, title, url, source_name, published_date, jurisdiction,
score_total, score_breakdown, persona, persona_rationale,
confidence, why_it_matters, category
```

### briefs_YYYYMMDD.json
```
rank, title, url, what_happened, why_it_matters_ac, so_what_for_us,
persona, persona_rationale, confidence
```

### validation_YYYYMMDD.json
```
checked_at, overall_pass, checks: [{ rule, passed, detail }]
```

---

## Validation Rules (checked by compose agent pass)

1. `source_urls` — every item has a non-empty URL
2. `jurisdiction_valid` — all items have a valid NZ/AU jurisdiction tag
3. `so_what_for_us_present` — every item has a non-empty so_what_for_us field
4. `no_partisan_commentary` — no partisan framing, advocacy, or editorial tone
5. `no_promotional_tone` — no hyperbole or superlatives
