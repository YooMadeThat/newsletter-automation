# brand/CLAUDE.md — Voice & Style

The authoritative style reference is `ac_style_guide.md` in this folder.
It is loaded automatically into the summarise and compose system prompts
via `harness.py` at run time. Edit that file to shift tone, vocabulary,
or newsletter structure across the whole pipeline — no Python changes needed.

---

## Key conventions (quick reference)

- **Name:** *Allen + Clarke* — always `+`, never "and" or "&"
- **Spelling:** NZ/British English — *prioritise, organisation, colour, programme*
- **Voice:** Expert but human. Confident, never cold. Write like a trusted
  senior adviser.
- **Pronouns:** "We" for the team voice in newsletter inserts. No "you".
- **Māori language:** Use macrons (*Māori, whānau, iwi, kaupapa*).
- **Numbers:** Spell out one to nine; numerals for 10+. Always numerals
  for percentages, measurements, and currencies.

## What lives where

| File | Purpose |
|---|---|
| `ac_style_guide.md` | Full brand kit — injected into agent system prompts |
| `brand/CLAUDE.md` (this file) | Quick reference for development context only |

Do not duplicate style rules here. The style guide is the single source
of truth. Update `ac_style_guide.md`, not this file.
