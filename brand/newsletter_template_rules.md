# Allen + Clarke — Newsletter Template Rules
## Policy + Regulation Section

This file defines the exact structure, section order, and formatting
rules for the Policy + Regulation newsletter output. The compose agent
and format agent must follow these rules precisely.

---

## Full Output Structure

The newsletter output consists of four sections produced in order.

---

### Section 1 — Ranked Item Table

**Format:** Markdown table

**Columns (in order):**
| Rank | Title | Source | Date | Jurisdiction | Persona | Why It Matters | Category |

**Rules:**
- Rank is an integer: 1 (strongest) to 5 (weakest of shortlisted items)
- Title is the article/document title as published — do not paraphrase
- Source is the organisation name (not the full URL)
- Date is the publication date in day-month-year format (e.g. 8 April 2025)
- Jurisdiction is one of: NZ, AU, NZ/AU, INT-relevant
- Persona is one of: Debbie, Inia, Pete
- Why It Matters is one sentence, maximum 20 words
- Category is one of: Policy Reform, Regulatory Update, Consultation Open,
  Implementation Guidance, Standards & Compliance, Other

---

### Section 2 — Per-Item Blocks

**Format:** Plain text blocks, one per item

**Template:**
```
ITEM [N]: [Title]
Source: [URL]
Persona: [Name] — [one sentence reason for persona assignment]
Why it matters: [one sentence — practical implication for A+C consultants]
Confidence: [High / Medium / Low]
```

**Rules:**
- N matches the Rank from Section 1
- The persona rationale sentence explains the fit — it is not a summary of the item
- "Why it matters" focuses on what A+C consultants should do or think — not just what happened
- Confidence level must match the value in the briefs JSON

---

### Section 3 — Strongest Signal Statement

**Format:** One sentence, italicised in Markdown

**Template:**
```
*The strongest item this week is [title] because [reason].*
```

**Rules:**
- "Reason" must explain why this item outranks others — not merely summarise it
- The reason should reference jurisdictional relevance, recency, or strategic importance
- Maximum 40 words for the full sentence

---

### Section 4 — Draft Newsletter Insert

**Format:** Headed block, 100–150 words

**Template:**
```
**Policy + Regulation — [Topic Area]**

[FACT] [Opening sentence — what happened]

[FACT or INTERPRETATION] [Context sentence(s)]

[INTERPRETATION] [Practical implication for A+C consultants]

Source: [URL]
[Word count: N]
```

**Rules:**
- Heading uses the topic area, not the article title
- Topic area examples: "Regulatory Review", "Consultation Deadline",
  "Implementation Guidance", "Standards Update", "Policy Reform"
- Every sentence carries a [FACT] or [INTERPRETATION] label
- Source line appears after the body, before the word count
- Word count covers body text only (excludes heading, source line, and word count note)
- Word count must be between 100 and 150 inclusive
- No speculation, no client names, third person throughout

---

## Word Document Formatting (for format_agent.py)

When rendering to .docx, apply these styles:

| Element | Style |
|---|---|
| Section headings (e.g. "Section 1 — Ranked Item Table") | Heading 2 |
| Item block headings (e.g. "ITEM [1]: Title") | Heading 3 |
| Newsletter insert heading | Heading 2 |
| Body text | Normal |
| [FACT] and [INTERPRETATION] labels | Bold inline |
| Table | Word Table style — no shading, simple borders |
| Source URLs | Hyperlink style (blue, underlined) |

**Font:** Use document default (do not hard-code a font — let the
Word template control typography).

**Spacing:** Single line spacing, 6pt space after each paragraph.

**Page setup:** A4, 2.5cm margins on all sides.

---

## Category Definitions

Use these definitions when assigning the Category field:

| Category | When to use |
|---|---|
| Policy Reform | Proposed or enacted changes to policy settings or legislation |
| Regulatory Update | Changes to regulations, rules, or regulatory frameworks |
| Consultation Open | Active consultation with submissions currently open |
| Implementation Guidance | Official guidance on how to implement existing policy or law |
| Standards & Compliance | Changes to standards, codes, or compliance requirements |
| Other | Items that do not fit the above — use sparingly |
