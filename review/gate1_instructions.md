# Gate 1 — Human Review Instructions
## Post-Triage Checkpoint

This checklist is for the human reviewer at Gate 1. At this point the
workflow has completed the research and triage phases. The shortlisted
items are displayed in the terminal. No briefs have been written yet.

Your decisions here control what the agents analyse, summarise, and
include in the newsletter. Take 3–5 minutes with this checklist before
approving.

---

## What You Are Seeing

The terminal displays:

1. **Scored shortlist table** — the triage agent's top 3–5 items, with:
   - Rank, Title, Source, Date, Jurisdiction, Score, Persona
   - Political sensitivity flag (! = flagged)

2. **Validation report** — a pass/fail check of hard rules against the
   shortlisted items. Any failures are highlighted in red.

3. **Warnings** (if any) — e.g. "Only 4 raw items found", "Item 2 is
   politically sensitive".

---

## Checklist — Work Through This Before Deciding

### Jurisdiction
- [ ] Are all items clearly NZ or AU? (No item with no NZ/AU relevance
      should be in the shortlist — if one is, drop it.)
- [ ] Is the NZ/AU balance appropriate? (NZ items should dominate.)

### Recency
- [ ] Are the items reasonably recent? (Items >14 days old should have
      a strong reason to remain — check the score breakdown.)
- [ ] Is there a very recent (≤7 days) item that is clearly the strongest?

### Source quality
- [ ] Are the source names recognisable and credible?
- [ ] Are any sources paywalled (flagged by agent)? If so, consider whether
      the snippet alone is sufficient for a useful brief.

### Political sensitivity
- [ ] Are any items flagged as politically sensitive (!)?
- [ ] If yes: Is inclusion appropriate given current political context?
- [ ] If the item names a minister, discusses Treaty obligations, or touches
      on co-governance: consider whether this is the right week to include it.

### Persona assignment
- [ ] Does the persona assignment feel right for each item?
- [ ] If an item feels more like a different persona, note it — you can
      add a note that will be passed to the summarise agent.

### Coverage
- [ ] Do the shortlisted items collectively cover a useful spread of
      topic areas, or are they all the same category?
- [ ] Is the strongest item clearly identifiable?

---

## Your Options

Type one of the following commands at the prompt:

| Command | Effect |
|---|---|
| `approve` | Accept shortlist as-is — workflow continues to briefs |
| `drop 2` | Remove item 2 from the shortlist (adjust number as needed) |
| `drop 2 3` | Remove items 2 and 3 (space-separated) |
| `note 1 [text]` | Add a context note to item 1 (passed to summarise agent) |
| `rerun` | Abort this run and restart the research phase |
| `abort` | Stop the workflow entirely — no output produced |

You can combine drop and note before approving:
```
drop 3
note 1 This relates to the recent Cabinet paper on agency accountability
approve
```

---

## Minimum Requirements to Approve

Do not approve a shortlist that:
- Contains fewer than 3 items
- Contains any item with no clear NZ/AU jurisdiction
- Contains an unreviewed politically sensitive item (either drop it or
  consciously decide to keep it)
- Contains items older than 30 days

If you are uncertain about quality this week, use `abort` and run again
when better source material is available. A thin newsletter is worse than
no newsletter.

---

## After You Approve

The workflow will:
1. Pass the approved shortlist (with any notes) to the summarise agent
2. Produce per-item briefs with [FACT] / [INTERPRETATION] labels
3. Run a validation pass against the hard rules
4. Halt if any validation check fails (you will be notified)
5. Proceed to compose agent to assemble the full newsletter output
6. Pause again at Gate 2 for your review of the Markdown before the
   Word document is rendered
