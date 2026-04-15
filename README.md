# Allen + Clarke Intel — Policy + Regulation Newsletter Workflow

Automated weekly research and newsletter drafting for the Allen + Clarke
Policy + Regulation service group. NZ-first, AU-second.

---

## What this does

Runs a 6-step pipeline that:
1. Searches for recent NZ/AU policy and regulation items via Perplexity
2. Scores, ranks, and selects the strongest 3–5 items (triage)
3. Writes a structured brief for each item
4. Runs a hard-rules validation pass
5. Assembles the full newsletter output (4-section Markdown)
6. Renders a formatted Word document

---

## Prerequisites

- Python 3.10 or higher
- A Perplexity API key (sonar-pro access recommended)
- An Anthropic API key

---

## Setup

### 1. Clone or copy this folder

```bash
cd allen-clarke-intel
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
.venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API keys

Edit `.env` and replace the placeholder values:

```
PERPLEXITY_API_KEY=your_actual_key_here
ANTHROPIC_API_KEY=your_actual_key_here
```

The `.env` file is in `.gitignore` — it will never be committed.

---

## Running the workflow

```bash
python orchestrator.py
```

The workflow runs interactively. You will be prompted at two human review
gates before the final Word document is produced.

---

## Output files

All outputs are date-stamped. Each run is preserved independently.

| File | Contents |
|---|---|
| `sources/raw_YYYYMMDD.json` | Raw Perplexity search results |
| `sources/triage_YYYYMMDD.json` | Scored shortlist with personas and flags |
| `sources/briefs_YYYYMMDD.json` | Per-item structured briefs |
| `sources/validation_YYYYMMDD.json` | Hard rules compliance check |
| `output/newsletter_YYYYMMDD.md` | Full newsletter Markdown (all 4 sections) |
| `output/newsletter_YYYYMMDD.docx` | Final Word document |

---

## Project structure

```
allen-clarke-intel/
├── CLAUDE.md                   ← Harness rules (read this first)
├── README.md                   ← This file
├── .env                        ← Your API keys (never commit)
├── .gitignore
├── requirements.txt
├── harness.py                  ← All shared constants, prompts, rubrics
├── orchestrator.py             ← Run this
├── agents/
│   ├── research_agent.py       ← Perplexity search
│   ├── triage_agent.py         ← Scoring and ranking
│   ├── summarise_agent.py      ← Per-item briefs
│   ├── compose_agent.py        ← Newsletter assembly
│   └── format_agent.py         ← Word document render
├── brand/
│   ├── ac_style_guide.md       ← A+C voice and tone rules
│   └── newsletter_template_rules.md  ← Section structure rules
├── review/
│   └── gate1_instructions.md  ← Human review checklist
├── sources/                    ← JSON outputs per run
└── output/                     ← Markdown + Word outputs per run
```

---

## Hard rules (always applied)

1. Never speculate beyond what the source directly states
2. Always include the original source URL
3. NZ/AU jurisdiction only — items with no clear NZ/AU relevance are rejected at triage
4. Facts and news only — partisan content, opinion pieces, and advocacy are rejected
5. Every brief and insert must include a "so what for us" line connecting to Allen + Clarke's work
6. Newsletter inserts use "we" (shared team voice) — no second-person address
7. Items older than 30 days are excluded; items older than 7 days score lower

---

## Troubleshooting

**"PERPLEXITY_API_KEY is not set"**
Edit your `.env` file and add your real key. Do not use the placeholder value.

**"Only N items found (minimum 3 required)"**
The search returned too few eligible items this week. The workflow halts at Gate 1.
Options: lower the score threshold in `harness.py`, broaden the queries, or abort
and run again later in the week when more content is available.

**"Validation checks failed"**
The hard rules compliance check found a problem in the briefs. The specific
failed checks are displayed. Review the briefs JSON in `sources/`, correct the
issue, and re-run from Step 4 (or restart the full workflow).

**Word document looks wrong**
Check that `python-docx` is installed (`pip install python-docx`). The format
agent logs a warning if the insert word count is outside the 100–150 word range.
