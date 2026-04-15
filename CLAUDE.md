# CLAUDE.md — Allen + Clarke Intel

Automated weekly research and newsletter drafting for the Allen + Clarke
Policy + Regulation service group.

**Scope:** NZ and AU equal priority. International items only if they
directly and materially influence NZ/AU policy or regulation.

See [agents/CLAUDE.md](agents/CLAUDE.md) for agent roles and data contracts.
See [brand/CLAUDE.md](brand/CLAUDE.md) for voice and style conventions.

---

## Hard Rules (Non-Negotiable)

Applied to every agent output, every run, without exception. Enforced
programmatically in `harness.py` and via system prompts.

1. **No speculation.** Never state anything not directly supported by the
   cited source.
2. **Always cite.** Every item must include its original source URL.
3. **NZ/AU only.** Items with no clear NZ or AU relevance are rejected at
   triage. `INT-irrelevant` and `unknown` jurisdiction tags are dropped.
4. **Perspective.** Newsletter inserts use "we" (shared team voice). No
   second-person address ("you", "your") in any output.
5. **Facts and news only.** Partisan content, opinion pieces, editorials,
   advocacy material, and election coverage are rejected at triage.
6. **"So what for us" required.** Every brief and insert must include a
   short note connecting the item to Allen + Clarke's work. A pointer for
   internal readers, not a call-to-action.
7. **Recency.** Items older than 30 days are excluded. Items older than 7
   days score lower in triage.
8. **Word count.** Newsletter insert must be 100–150 words. Compose retries
   once if out of range.

---

## Build Principles

1. All shared constants, prompts, and rubrics live in `harness.py`. Agents
   import from harness — they do not define their own rules.
2. Every run produces date-stamped files in `sources/` and `output/`. Old
   runs are never overwritten.
3. The orchestrator halts on failure and surfaces the error. It does not
   silently skip items or continue past a failed validation.
4. Prompts are versioned via `PROMPT_VERSION` in `harness.py`.
5. One human gate only — after the newsletter draft is composed. Triage
   is fully automated; the human reviews the final draft, not the shortlist.
