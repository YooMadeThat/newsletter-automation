"""
triage_agent.py — Agent 2: Score, Rank, Select, and Assign Persona

Receives raw candidate items from research_agent and produces a ranked
shortlist of 3–5 items with scores, persona assignments, and flags.

Input:  sources/raw_YYYYMMDD.json
Output: sources/triage_YYYYMMDD.json
API:    Claude (claude-sonnet-4-6)
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

import anthropic

import harness


class TriageAgent:
    def __init__(self, api_key: str, sources_dir: Path, run_date: date):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.sources_dir = sources_dir
        self.run_date = run_date

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, raw_path: Path) -> Path:
        """Score and rank items. Returns path to triage JSON."""
        with open(raw_path, encoding="utf-8") as f:
            raw_data = json.load(f)

        items = raw_data.get("items", [])
        if not items:
            raise RuntimeError("Research agent returned zero items. Cannot proceed.")

        # Filter out items with rejected jurisdiction tags before sending to Claude
        eligible = [
            i for i in items
            if i.get(harness.FIELD_JURISDICTION_TAG) not in harness.REJECTED_JURISDICTIONS
        ]

        if len(eligible) < harness.MIN_SHORTLIST_ITEMS:
            raise RuntimeError(
                f"Only {len(eligible)} eligible items found (minimum {harness.MIN_SHORTLIST_ITEMS} required). "
                "Consider expanding search or adjusting date window."
            )

        shortlist = self._call_claude(eligible)
        try:
            self._validate_shortlist(shortlist)
        except RuntimeError as exc:
            # Retry once — LLMs occasionally drop a required field
            shortlist = self._call_claude(eligible)
            self._validate_shortlist(shortlist)

        output_path = self.sources_dir / f"triage_{self.run_date.strftime('%Y%m%d')}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_date": self.run_date.isoformat(),
                    "prompt_version": harness.PROMPT_VERSION,
                    "item_count": len(shortlist),
                    "items": shortlist,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return output_path

    # ------------------------------------------------------------------
    # Claude call
    # ------------------------------------------------------------------

    def _call_claude(self, items: list[dict]) -> list[dict]:
        items_text = json.dumps(items, indent=2, ensure_ascii=False)

        user_prompt = (
            f"Today is {self.run_date.isoformat()}.\n\n"
            f"Below are {len(items)} candidate policy and regulation items "
            f"found via web search. Score, rank, and select the strongest "
            f"{harness.MIN_SHORTLIST_ITEMS}–{harness.MAX_SHORTLIST_ITEMS} items only.\n\n"
            f"For each selected item, return ALL of these fields:\n"
            f"- rank (integer, 1 = strongest)\n"
            f"- title\n"
            f"- url\n"
            f"- source_name\n"
            f"- published_date\n"
            f"- jurisdiction (one of: NZ, AU, NZ/AU, INT-relevant)\n"
            f"- score_total (float, calculated from rubric)\n"
            f"- score_breakdown (object: jurisdiction, recency, credibility, ac_relevance — each 0–5)\n"
            f"- persona (one of: Debbie, Inia, Pete)\n"
            f"- persona_rationale (one sentence explaining why)\n"
            f"- confidence (High / Medium / Low)\n"
            f"- why_it_matters (one sentence — practical implication for A+C consultants)\n"
            f"- category (one of: Policy Reform, Regulatory Update, Consultation Open, "
            f"Implementation Guidance, Standards & Compliance, Other)\n\n"
            f"Return ONLY a JSON array. No prose, no markdown fences.\n\n"
            f"CANDIDATE ITEMS:\n{items_text}"
        )

        response = self.client.messages.create(
            model=harness.CLAUDE_MODEL,
            max_tokens=4096,
            system=harness.TRIAGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = response.content[0].text.strip()
        content = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`").strip()

        try:
            shortlist = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                shortlist = json.loads(match.group())
            else:
                raise RuntimeError(
                    f"Triage agent: Claude returned unparseable output.\n{content[:500]}"
                )

        if not isinstance(shortlist, list):
            raise RuntimeError("Triage agent: Claude returned non-list output.")

        return shortlist

    # ------------------------------------------------------------------
    # Validate the shortlist meets hard constraints
    # ------------------------------------------------------------------

    def _validate_shortlist(self, shortlist: list[dict]) -> None:
        if len(shortlist) < harness.MIN_SHORTLIST_ITEMS:
            raise RuntimeError(
                f"Triage returned {len(shortlist)} items (minimum {harness.MIN_SHORTLIST_ITEMS})."
            )
        if len(shortlist) > harness.MAX_SHORTLIST_ITEMS:
            raise RuntimeError(
                f"Triage returned {len(shortlist)} items (maximum {harness.MAX_SHORTLIST_ITEMS})."
            )

        for i, item in enumerate(shortlist, 1):
            errors = harness.validate_fields(item, harness.TRIAGE_REQUIRED_FIELDS, f"Item {i}")
            if errors:
                raise RuntimeError(f"Triage validation error: {errors}")

            jurisdiction = item.get(harness.FIELD_JURISDICTION, "")
            if jurisdiction in harness.REJECTED_JURISDICTIONS:
                raise RuntimeError(
                    f"Item {i} has rejected jurisdiction '{jurisdiction}'. "
                    "Triage agent must not include items with no NZ/AU relevance."
                )

            persona = item.get(harness.FIELD_PERSONA, "")
            if persona not in harness.PERSONAS:
                raise RuntimeError(
                    f"Item {i} has invalid persona '{persona}'. "
                    f"Must be one of: {list(harness.PERSONAS.keys())}"
                )

        # AU balance check — at least one AU or NZ/AU item required
        au_jurisdictions = {harness.JURISDICTION_AU, harness.JURISDICTION_NZ_AU}
        au_items = [
            item for item in shortlist
            if item.get(harness.FIELD_JURISDICTION) in au_jurisdictions
        ]
        if not au_items:
            raise RuntimeError(
                "Triage returned zero AU items. NZ and AU are equal priority — "
                "at least one AU or NZ/AU item must be included in the shortlist."
            )
