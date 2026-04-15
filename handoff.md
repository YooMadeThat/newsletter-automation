# Allen + Clarke Intel — Handoff

Automated weekly research and newsletter drafting for the Policy + Regulation
service group. NZ and AU equal priority, international only where there is
direct and material NZ/AU influence.

---

## 1. What this does

One command produces a weekly internal newsletter draft (Markdown + Word) by:

1. Searching the web for recent NZ/AU policy and regulation news
2. Scoring, ranking, and shortlisting 3–5 items (fully automated)
3. Writing structured briefs for each item
4. Running a compliance check against hard rules
5. Composing a full newsletter draft with a 100–150-word insert
6. Pausing for a human to review and approve the draft
7. Rendering the approved draft as a Word document

Two APIs: Perplexity (`sonar-pro`) for research, Claude (`claude-sonnet-4-6`)
for all reasoning and writing. python-docx for the Word render. No database.
Every run writes date-stamped JSON artefacts under `sources/` and final
outputs under `output/`.

---

## 2. Run it

```bash
cd allen-clarke-intel
python orchestrator.py
```

Requirements: `.env` with `PERPLEXITY_API_KEY` and `ANTHROPIC_API_KEY`.

At the gate (Step 6), type `approve` (or `rewrite` once, or `abort`).

Outputs:
- `output/newsletter_YYYYMMDD.md`
- `output/newsletter_YYYYMMDD.docx`

---

## 3. Repo layout

```
allen-clarke-intel/
├── orchestrator.py          # Entry point — runs all 8 steps
├── harness.py               # Single rulebook: prompts, constants, rubrics
├── agents/
│   ├── research_agent.py    # Perplexity search → raw_YYYYMMDD.json
│   ├── triage_agent.py      # Score + rank + reject partisan → triage_YYYYMMDD.json
│   ├── summarise_agent.py   # Per-item briefs → briefs_YYYYMMDD.json
│   ├── compose_agent.py     # Full newsletter Markdown → newsletter_YYYYMMDD.md
│   └── format_agent.py      # Word render → newsletter_YYYYMMDD.docx
├── brand/
│   └── ac_style_guide.md    # Brand kit — loaded into system prompts
├── review/
│   └── gate1_instructions.md
├── sources/                 # Date-stamped JSON artefacts (one set per run)
└── output/                  # Markdown + Word newsletters
```

Principle: all shared rules live in `harness.py`. Agents import; they do not
define their own rules. The brand kit is loaded from disk into the summarise
and compose system prompts at run time, so editing
`brand/ac_style_guide.md` is enough to shift tone across the pipeline.

---

## 4. Hard rules (enforced in prompts + validator)

1. No speculation beyond the source
2. Every item cites a URL
3. Every brief/insert has a `so_what_for_us` line (not a CTA)
4. NZ/AU only — `INT-irrelevant` and `unknown` are dropped
5. No client names (A+C itself is not a client)
6. "We" for newsletter inserts; no second-person "you"
7. Facts and news only — partisan/opinion/advocacy rejected at triage
8. Max item age 30 days; ≤7 days scores highest
9. Insert word count 100–150 (compose retries once)
10. Source credibility: government > reputable media > academic > other

Full rule text in `CLAUDE.md` and `harness.py` (`HARD_RULES_BLOCK`).

---

## 5. Data contract

Field names are constants in `harness.py`. Required-field sets:

- **raw**: title, url, source_name, published_date, snippet,
  jurisdiction_tag, is_paywalled, query_used
- **triage**: rank, title, url, source_name, published_date, jurisdiction,
  score_total, score_breakdown, persona, persona_rationale, confidence,
  why_it_matters, category
- **briefs**: rank, title, url, what_happened, why_it_matters_ac,
  so_what_for_us, persona, persona_rationale, confidence
- **validation**: checked_at, overall_pass, checks[{rule, passed, detail}]

---

## 6. Personas

Each item is assigned exactly one:

- **Debbie** — strategy, accountability, defensibility, outcomes
- **Inia** — evidence, methods, implementation, sound decisions
- **Pete** — clarity, practicality, reducing ambiguity, delivery

Definitions in `harness.py` (`PERSONAS`) and the brand kit §7.

---

## 7. Key design decisions

- **One rulebook, many agents.** All prompts, scoring weights, field names,
  and the brand kit funnel through `harness.py`. Change rules in one place.
- **One human gate, after the draft.** Triage is fully automated — the
  agent scoring is consistent enough to not need shortlist review. The human
  sees the finished draft and either approves, rewrites once, or aborts.
- **Reject partisan at triage, don't flag-and-debate.** Earlier versions
  tagged items `politically_sensitive` and a second LLM validator disagreed
  with the first. Now triage filters at the front door; the validator only
  checks mechanical rules.
- **Brand kit as a file, not a prompt.** `brand/ac_style_guide.md` is loaded
  into system prompts at run time. Non-technical editors can adjust voice
  without touching Python.
- **Stateless agents, file-based handoff.** Each agent reads one JSON file
  and writes another. Easy to rerun, inspect, or swap out individually.

---

## 8. Known limits / next candidates

- **No exemplar newsletters.** The system has rules but no past examples.
  Adding 2–3 edited prior inserts to `brand/examples/` and showing them
  to the compose agent would tighten voice.
- **Validator is LLM-only.** Mechanical checks (URL presence, word count,
  regex for banned phrases) could move to Python to remove a Claude call.
- **No cost/latency logging.** Each run burns ~4–6 Claude calls and 6
  Perplexity queries; no record of per-run spend.
- **CLI only.** Non-technical users need a terminal. A thin wrapper
  (shell script or small web UI) would remove that friction.
- **No gate feedback capture.** When a human rewrites the draft, none
  of those edits feed back into future prompts.
- **No tests.** Agents are exercised only by end-to-end runs.

---

## 9. Troubleshooting

- **`Environment variable not set`** — `.env` missing or still has
  `your_...` placeholder. Edit `.env` at repo root.
- **`Only N eligible items found`** — Perplexity returned too few NZ/AU
  items. Expand the date window (`MAX_ITEM_AGE_DAYS` in `harness.py`) or
  rerun; Perplexity results vary day-to-day.
- **Validation fails** — read `sources/validation_YYYYMMDD.json` for the
  failing rule and detail. Fix the brief JSON or tighten the prompt, then
  rerun from Step 4.
- **Word count out of range** — compose retries once automatically. If it
  still fails, tighten or loosen `NEWSLETTER_INSERT_MIN/MAX_WORDS`.
- **Interactive gate hangs in non-TTY shell** — pipe input:
  `printf 'approve\napprove\n' | python orchestrator.py`.

---

## 10. Where to look first when changing things

| Want to change... | Edit... |
|---|---|
| Voice, tone, vocabulary | `brand/ac_style_guide.md` |
| Hard rules | `harness.py` → `HARD_RULES_BLOCK` + `CLAUDE.md` |
| Scoring weights or bands | `harness.py` → `SCORING_WEIGHTS`, `RECENCY_SCORE_BANDS` |
| Search queries | `harness.py` → `SEARCH_QUERIES` |
| Personas | `harness.py` → `PERSONAS` + brand kit §7 |
| Insert structure | `harness.py` → `COMPOSE_SYSTEM_PROMPT` + brand kit §8 |
| Validator rules | `harness.py` → `VALIDATION_SYSTEM_PROMPT` |
| Gate UX | `orchestrator.py` → `_gate1_prompt`, `_gate2_prompt` |
| Word render styling | `agents/format_agent.py` |
