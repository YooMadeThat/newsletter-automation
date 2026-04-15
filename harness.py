"""
harness.py — Allen + Clarke Intel Master Rules Engine

All shared constants, scoring rubrics, persona definitions, query templates,
system prompts, and JSON field names live here. Every agent imports from
this module. No agent defines its own rules.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

PROMPT_VERSION = "1.0.0"
WORKFLOW_NAME = "Allen + Clarke Policy + Regulation Newsletter"

# ---------------------------------------------------------------------------
# Date / recency settings
# ---------------------------------------------------------------------------

MAX_ITEM_AGE_DAYS = 30       # Hard cutoff — items older than this are dropped
PREFERRED_RECENCY_DAYS = 7   # Items within this window score maximum recency

# ---------------------------------------------------------------------------
# Output constraints
# ---------------------------------------------------------------------------

MIN_SHORTLIST_ITEMS = 3
MAX_SHORTLIST_ITEMS = 5
NEWSLETTER_INSERT_MIN_WORDS = 100
NEWSLETTER_INSERT_MAX_WORDS = 150

# ---------------------------------------------------------------------------
# Jurisdiction tags
# ---------------------------------------------------------------------------

JURISDICTION_NZ = "NZ"
JURISDICTION_AU = "AU"
JURISDICTION_NZ_AU = "NZ/AU"
JURISDICTION_INT_RELEVANT = "INT-relevant"
JURISDICTION_INT_IRRELEVANT = "INT-irrelevant"
JURISDICTION_UNKNOWN = "unknown"

VALID_JURISDICTIONS = {
    JURISDICTION_NZ,
    JURISDICTION_AU,
    JURISDICTION_NZ_AU,
    JURISDICTION_INT_RELEVANT,
}

REJECTED_JURISDICTIONS = {
    JURISDICTION_INT_IRRELEVANT,
    JURISDICTION_UNKNOWN,
}

# ---------------------------------------------------------------------------
# Scoring rubric
# Weights must sum to 1.0
# ---------------------------------------------------------------------------

SCORING_WEIGHTS = {
    "jurisdiction": 0.35,
    "recency": 0.25,
    "credibility": 0.20,
    "ac_relevance": 0.20,
}

JURISDICTION_SCORES = {
    JURISDICTION_NZ: 5,
    JURISDICTION_AU: 5,
    JURISDICTION_NZ_AU: 5,
    JURISDICTION_INT_RELEVANT: 2,
    JURISDICTION_INT_IRRELEVANT: 0,
    JURISDICTION_UNKNOWN: 0,
}

# Recency: age in days → score
RECENCY_SCORE_BANDS = [
    (7, 5),    # ≤ 7 days → 5
    (14, 3),   # 8–14 days → 3
    (30, 1),   # 15–30 days → 1
]

# Credibility tiers
CREDIBILITY_SCORES = {
    "government": 5,          # Govt, statutory body, regulator
    "reputable_media": 3,     # Major NZ/AU news outlets
    "academic": 3,            # Peer-reviewed or research institutions
    "other": 1,               # Everything else
}

# A+C practice area relevance — scored 0–5 by Claude
AC_RELEVANCE_MIN = 0
AC_RELEVANCE_MAX = 5

# ---------------------------------------------------------------------------
# Confidence levels
# ---------------------------------------------------------------------------

CONFIDENCE_HIGH = "High"
CONFIDENCE_MEDIUM = "Medium"
CONFIDENCE_LOW = "Low"

# ---------------------------------------------------------------------------
# Persona definitions
# ---------------------------------------------------------------------------

PERSONAS = {
    "Debbie": {
        "focus": "Strategy, accountability, defensibility, outcomes",
        "assign_when": (
            "The item has direct implications for how policy is designed, "
            "how accountability is structured, or how organisations defend "
            "decisions to ministers, boards, or the public."
        ),
    },
    "Inia": {
        "focus": "Evidence, methods, implementation, sound decisions",
        "assign_when": (
            "The item concerns how analysis is done, how evidence is gathered "
            "or weighted, how implementation is structured, or how decisions "
            "are made to be robust."
        ),
    },
    "Pete": {
        "focus": "Clarity, practicality, reducing ambiguity, delivery",
        "assign_when": (
            "The item concerns operational clarity, reducing regulatory "
            "ambiguity, practical guidance for agencies, or how implementation "
            "actually gets done on the ground."
        ),
    },
}

# ---------------------------------------------------------------------------
# A+C practice areas (used in triage relevance scoring)
# ---------------------------------------------------------------------------

AC_PRACTICE_AREAS = [
    "Policy development and reform",
    "Regulatory analysis and design",
    "Stakeholder engagement and consultation",
    "Cross-agency coordination and governance",
    "Implementation planning and support",
    "Monitoring, evaluation, and reporting",
]

# ---------------------------------------------------------------------------
# Perplexity search query templates
# NZ queries run first, AU second, international only if needed
# ---------------------------------------------------------------------------

SEARCH_QUERIES = [
    # NZ — Primary
    "New Zealand government consultation paper policy reform {year}",
    "New Zealand regulatory update compliance guidance {year}",
    "New Zealand public sector policy implementation {year}",
    # AU — Secondary
    "Australia government regulatory reform consultation {year}",
    "Australia policy development regulation guidance {year}",
    # International — only if NZ/AU yield is low
    "OECD regulatory policy framework New Zealand Australia influence {year}",
]

PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_API_BASE = "https://api.perplexity.ai"
PERPLEXITY_RECENCY_FILTER = "month"  # Perplexity search_recency_filter value

# ---------------------------------------------------------------------------
# Claude model
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# JSON field name constants (data contract between agents)
# ---------------------------------------------------------------------------

# Raw items (research_agent output)
FIELD_TITLE = "title"
FIELD_URL = "url"
FIELD_SOURCE_NAME = "source_name"
FIELD_PUBLISHED_DATE = "published_date"
FIELD_SNIPPET = "snippet"
FIELD_JURISDICTION_TAG = "jurisdiction_tag"
FIELD_IS_PAYWALLED = "is_paywalled"
FIELD_QUERY_USED = "query_used"

# Triage items
FIELD_RANK = "rank"
FIELD_JURISDICTION = "jurisdiction"
FIELD_SCORE_TOTAL = "score_total"
FIELD_SCORE_BREAKDOWN = "score_breakdown"
FIELD_PERSONA = "persona"
FIELD_PERSONA_RATIONALE = "persona_rationale"
FIELD_CONFIDENCE = "confidence"
FIELD_CONFIDENCE_EVIDENCE = "confidence_evidence"
FIELD_WHY_IT_MATTERS = "why_it_matters"
FIELD_CATEGORY = "category"

# Briefs
FIELD_WHAT_HAPPENED = "what_happened"
FIELD_WHY_IT_MATTERS_AC = "why_it_matters_ac"
FIELD_SO_WHAT_FOR_US = "so_what_for_us"

# Validation
FIELD_CHECKED_AT = "checked_at"
FIELD_OVERALL_PASS = "overall_pass"
FIELD_CHECKS = "checks"
FIELD_RULE = "rule"
FIELD_PASSED = "passed"
FIELD_DETAIL = "detail"

# ---------------------------------------------------------------------------
# System prompts (injected into Claude calls by each agent)
# ---------------------------------------------------------------------------

from pathlib import Path as _Path

_BRAND_KIT_PATH = _Path(__file__).parent / "brand" / "ac_style_guide.md"
try:
    BRAND_KIT = _BRAND_KIT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    BRAND_KIT = ""

STYLE_GUIDE_BLOCK = f"""
BRAND KIT & STYLE GUIDE — follow these conventions in all written output:

{BRAND_KIT}
""".strip() if BRAND_KIT else ""

HARD_RULES_BLOCK = """
HARD RULES — apply without exception:
1. Never speculate beyond what the source directly states.
2. Always include the original source URL.
3. NZ and AU jurisdiction items only — reject anything with no clear NZ/AU relevance.
4. Perspective: use "we" for newsletter inserts (shared team voice).
   Use "I" only in signed blog posts. No second-person address to the reader.
5. Facts and news only — no partisan commentary, no opinion pieces, no
   editorials, no advocacy content. Outputs describe what rules, consultations,
   or releases exist — never take a political position.
""".strip()

TRIAGE_SYSTEM_PROMPT = f"""
You are a senior policy analyst working for Allen + Clarke, a New Zealand
management consultancy specialising in policy development, regulatory analysis,
stakeholder engagement, and implementation support.

Your task is to score, rank, and select the 3–5 strongest items from a list of
candidate news and regulatory items for a weekly internal newsletter.

SCORING RUBRIC:
- Jurisdiction relevance (weight 35%): NZ direct = 5, AU direct = 5,
  INT with clear NZ/AU influence = 2, no NZ/AU relevance = 0 (reject)
- Recency (weight 25%): ≤7 days = 5, 8–14 days = 3, 15–30 days = 1
- Source credibility (weight 20%): government/statutory body = 5,
  reputable media = 3, academic/research = 3, other = 1
- A+C practice area relevance (weight 20%): score 0–5 based on fit with:
  {", ".join(AC_PRACTICE_AREAS)}

PERSONA ASSIGNMENT — assign exactly one of Debbie, Inia, or Pete per item.
No other persona values are permitted.

- Debbie: {PERSONAS["Debbie"]["assign_when"]}
- Inia: {PERSONAS["Inia"]["assign_when"]}
- Pete: {PERSONAS["Pete"]["assign_when"]}

Disambiguation: if an item is primarily about HOW to implement or demonstrate
compliance operationally (e.g. a compliance deadline, practical step-by-step
guidance for agencies, incident reporting obligations), assign Pete even if
accountability language is present. Debbie applies when the item reshapes
strategic accountability structures or defensibility — not when it is
primarily a compliance-implementation task.
The assignment must be convincing and match the item's primary lens.

INCLUDE / REJECT FILTER (apply before scoring):

INCLUDE — items whose content is factual news:
- Government announcements, releases, and official publications
- Regulator consultations, exposure drafts, discussion documents
- Statutory body reports and guidance
- Law-firm summaries, legal digests, and regulatory updates
- Academic or research publications on policy / regulation

REJECT — items whose core framing is partisan, opinion-led, or
contested:
- Opinion pieces, editorials, op-eds
- Commentary that takes a partisan position
- Election coverage, polling, political strategy pieces
- Items about named politicians in contested contexts
- Advocacy content or position papers from lobbying groups
- Items whose primary purpose is to persuade rather than inform

If uncertain whether an item is primarily factual or primarily
opinion, REJECT it. Only factual news reaches the shortlist.

SOURCE QUALITY — prefer primary over aggregator sources:
- PREFER: government websites (.govt.nz, .gov.au), regulator sites,
  law firm insights (e.g. MinterEllison, Chapman Tripp), major NZ/AU
  mastheads (NZ Herald, Australian Financial Review).
- AVOID: content aggregators (Mirage News, PR Newswire, GlobeNewswire,
  BusinessWire, EIN Presswire, and similar wire/aggregator services).
  These score credibility = 1 (other tier).
- If an aggregator is the ONLY available source for a relevant item,
  include it but set confidence to Medium or Low and note in
  confidence_evidence: "Aggregator source only — primary source not
  located. Recommend manual verification before circulation."

OUTPUT: Return a JSON array of {MIN_SHORTLIST_ITEMS}–{MAX_SHORTLIST_ITEMS} items.
Each item must include all triage fields as specified.
Reject items with jurisdiction score = 0.

AU BALANCE REQUIREMENT: At least 1 item must be from AU or NZ/AU jurisdiction.
NZ and AU are equal priority — a shortlist of all-NZ items is not acceptable.
If AU candidates exist and score reasonably (≥3.0 total), include at least one.

{HARD_RULES_BLOCK}
""".strip()

SUMMARISE_SYSTEM_PROMPT = f"""
You are a senior adviser at Allen + Clarke, a New Zealand consultancy.
You write for internal colleagues — trusted peers, not a public audience.

Your task is to write a structured brief for each shortlisted item.
Each brief answers:
1. what_happened — one plain sentence stating the factual news. Source,
   action, date. No labels, no throat-clearing.
2. why_it_matters — one or two sentences on why this matters for NZ/AU
   policy and regulation. Concrete, evidence-led, not abstract.
3. so_what_for_us — one short sentence on how this connects to Allen +
   Clarke's work or a client situation. Not a call-to-action; a pointer
   for internal readers. May use "we" / "our work".
4. persona_rationale — one sentence on why this persona fits.
5. confidence — High / Medium / Low.
6. confidence_evidence — one short sentence citing the specific evidence
   for this confidence level. Name the source type (government primary /
   law firm summary / regulator / OECD / etc.), the recency (days since
   publication), and the jurisdiction directness (NZ direct / AU direct /
   NZ applied from AU, etc.). Example: "High — government primary source
   (Public Service Commission), published 16 days ago, NZ direct."

Confidence guidance:
- High: Government primary source, clear NZ/AU direct relevance, published ≤7 days
- Medium: Secondary source, AU relevance applied to NZ context, 8–14 days old
- Low: International with inferred NZ/AU relevance, >14 days old, or limited source access

Write in plain NZ/British English. No [FACT] or [INTERPRETATION] labels
in this output — the audit trail lives in the JSON structure.

{HARD_RULES_BLOCK}

{STYLE_GUIDE_BLOCK}
""".strip()

VALIDATION_SYSTEM_PROMPT = f"""
You are a compliance checker. Review the provided briefs JSON against the
following hard rules and return a validation report.

For each rule, report: rule name, passed (true/false), and a detail note.

Rules to check:
1. source_urls: Every item has a non-empty URL
2. jurisdiction_valid: All items have a valid NZ/AU jurisdiction tag
3. so_what_for_us_present: Every item has a non-empty so_what_for_us
   field connecting the item to Allen + Clarke's work or a client
   situation
4. no_partisan_commentary: No partisan opinion, advocacy, or editorial
   framing appears in any brief. Items that merely describe government
   or regulator actions are fine; items that take sides are not.
5. no_promotional_tone: No hyperbole, superlatives, or marketing
   phrasing (e.g. "world-class", "cutting-edge")

Return JSON with fields: checked_at, overall_pass (bool), checks (array).

{HARD_RULES_BLOCK}
""".strip()

COMPOSE_SYSTEM_PROMPT = f"""
You are the lead editor of the Allen + Clarke weekly internal Policy +
Regulation newsletter. You write for internal colleagues — a trusted
senior-adviser tone, confident but human. Use "we" for the team voice.

You will receive a set of structured item briefs. Your tasks:

Section 1 — Before the table, include exactly one sentence showing the triage
trace. Use this format:
   "X items were identified across Y searches; the Z selected scored highest on
   NZ/AU relevance, recency, source credibility, and Allen + Clarke practice
   relevance."
(Substitute the actual numbers from the TRIAGE META provided in the user prompt.)

Then produce the ranked summary table with EXACTLY these columns in this order:

Rank | Title | Source | Jurisdiction | Persona | So What For Us | Category

Column rules:
- Source: combine source name (as a markdown hyperlink), and date in one cell.
  Format: [Source Name](URL) — DD Month YYYY
  Example: [Public Service Commission](https://www.publicservice.govt.nz/...) — 30 March 2026
- Persona: one of exactly Debbie, Inia, or Pete. No other values.
- So What For Us: one short sentence — the A+C practice-relevant implication.

Section 2 — Per-item blocks:
   ITEM [N]: [Source title]
   Source: [URL]
   Persona: [Name] — [one sentence reason]
   Why it matters: [one or two sentences]
   Why It Matters for Us: [one sentence — connection to A+C work / client situation]
   Confidence: High / Medium / Low
   Confidence evidence: [one short sentence — source type, recency, jurisdiction directness]

Section 3 — Strongest signal. Identify the single strongest item or
through-line across the shortlist. State it in one sentence. This item
becomes the subject of the Section 4 newsletter insert — name it
explicitly so the link is clear.

Section 4 — Newsletter insert ({NEWSLETTER_INSERT_MIN_WORDS}–{NEWSLETTER_INSERT_MAX_WORDS} words, body only) written about
the item or signal named in Section 3. Use this exact structure:

  1. **Title** — Specific, number-driven, slightly unexpected. Max 12
     words. Not a summary; earn the click.
  2. **Lead sentence** — The "so what" first, in the first 10 words.
     No throat-clearing.
  3. **Context paragraph** — 2–3 sentences. What's changing and why
     it matters to NZ/AU policy.
  4. **Implication line** — One sentence. What this means for the
     reader's work or decisions.
  5. **Persona tag + "So what for us" line** — Flag the persona
     (Debbie / Inia / Pete). Follow with a short line on how this
     connects to Allen + Clarke's work or a client situation. Named,
     low-pressure, service-specific. No "contact us" phrasing.
  6. **Source line:** Source: [URL]

Do NOT include a word count tag or note in the output.

Voice rules for the insert:
- Use "we" for the team voice. Do not address the reader as "you".
- NZ/British English spelling throughout.
- No [FACT] or [INTERPRETATION] labels in the insert.
- Vary sentence rhythm. Target medium-medium-short or long-short-medium.
- Specific numbers and named methodologies over vague qualifiers.
- Bold used only for key ideas, one or two per paragraph.

IMPORTANT: The body (points 2–5) must be {NEWSLETTER_INSERT_MIN_WORDS}–{NEWSLETTER_INSERT_MAX_WORDS} words.
Count carefully before outputting. If over {NEWSLETTER_INSERT_MAX_WORDS}, trim the context
paragraph or implication line. Do not include a word count in the output.

{HARD_RULES_BLOCK}

{STYLE_GUIDE_BLOCK}
""".strip()

# ---------------------------------------------------------------------------
# Utility: compute recency score from age in days
# ---------------------------------------------------------------------------

def recency_score(age_days: int) -> int:
    for threshold, score in RECENCY_SCORE_BANDS:
        if age_days <= threshold:
            return score
    return 0


# ---------------------------------------------------------------------------
# Utility: compute weighted total score
# ---------------------------------------------------------------------------

def compute_total_score(
    jurisdiction_score: int,
    recency_score_val: int,
    credibility_score: int,
    ac_relevance_score: int,
) -> float:
    return round(
        jurisdiction_score * SCORING_WEIGHTS["jurisdiction"]
        + recency_score_val * SCORING_WEIGHTS["recency"]
        + credibility_score * SCORING_WEIGHTS["credibility"]
        + ac_relevance_score * SCORING_WEIGHTS["ac_relevance"],
        3,
    )


# ---------------------------------------------------------------------------
# Utility: word count
# ---------------------------------------------------------------------------

def word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Utility: validate required JSON fields are present
# ---------------------------------------------------------------------------

RAW_REQUIRED_FIELDS = {
    FIELD_TITLE, FIELD_URL, FIELD_SOURCE_NAME,
    FIELD_PUBLISHED_DATE, FIELD_SNIPPET,
    FIELD_JURISDICTION_TAG, FIELD_IS_PAYWALLED, FIELD_QUERY_USED,
}

TRIAGE_REQUIRED_FIELDS = {
    FIELD_RANK, FIELD_TITLE, FIELD_URL, FIELD_SOURCE_NAME,
    FIELD_PUBLISHED_DATE, FIELD_JURISDICTION,
    FIELD_SCORE_TOTAL, FIELD_SCORE_BREAKDOWN,
    FIELD_PERSONA, FIELD_PERSONA_RATIONALE,
    FIELD_CONFIDENCE,
    FIELD_WHY_IT_MATTERS, FIELD_CATEGORY,
}

BRIEF_REQUIRED_FIELDS = {
    FIELD_RANK, FIELD_TITLE, FIELD_URL,
    FIELD_WHAT_HAPPENED, FIELD_WHY_IT_MATTERS_AC, FIELD_SO_WHAT_FOR_US,
    FIELD_PERSONA, FIELD_PERSONA_RATIONALE, FIELD_CONFIDENCE,
    FIELD_CONFIDENCE_EVIDENCE,
}


def validate_fields(item: dict, required: set, item_label: str = "item") -> list[str]:
    missing = required - set(item.keys())
    if missing:
        return [f"{item_label} missing fields: {sorted(missing)}"]
    return []


# ---------------------------------------------------------------------------
# Utility: extract Section 4 insert body text for accurate word counting
#
# "Body" = points 2–5 of the insert structure (lead sentence through persona
# tag line). Excludes: section heading, category heading, insert title,
# source line, word count tag, and markdown formatting characters.
# ---------------------------------------------------------------------------

import re as _re

def extract_insert_body(markdown: str) -> str:
    """Return plain-text body of the Section 4 insert for word counting."""
    # Isolate the newsletter insert section — matches either legacy "## Section 4 ..."
    # or the simplified "## Newsletter Insert" heading used in the tighter output format.
    section4 = _re.search(
        r"##\s*(?:Section 4\b|Newsletter Insert).*?(?=##|\Z)", markdown, _re.DOTALL | _re.IGNORECASE
    )
    if not section4:
        return ""
    text = section4.group()

    # Strip section heading lines
    text = _re.sub(r"^##.*$", "", text, flags=_re.MULTILINE)
    # Strip [Word count: N] tag if present (legacy)
    text = _re.sub(r"\[Word count:.*?\]", "", text)
    # Strip Source: line
    text = _re.sub(r"^Source:.*$", "", text, flags=_re.MULTILINE)
    # Strip category/type heading  (**Policy + Regulation — ...**)
    text = _re.sub(r"^\*\*Policy \+ Regulation.*?\*\*\s*$", "", text, flags=_re.MULTILINE)
    # Strip the insert title — the first remaining **...** standalone line
    lines = text.split("\n")
    title_stripped = False
    kept = []
    for line in lines:
        s = line.strip()
        if not title_stripped and _re.match(r"^\*\*.+\*\*$", s):
            title_stripped = True
            continue
        kept.append(line)
    text = "\n".join(kept)

    # Strip markdown bold/italic markers and inline links, leaving plain words
    text = _re.sub(r"\*+([^*\n]+)\*+", r"\1", text)
    text = _re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    return text.strip()
