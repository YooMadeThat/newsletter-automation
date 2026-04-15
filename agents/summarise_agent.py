"""
summarise_agent.py — Agent 3: Per-Item Structured Briefs

Generates a 4-question brief for each shortlisted item. All statements
are labelled [FACT] or [INTERPRETATION]. No speculation beyond the source.

Input:  sources/triage_YYYYMMDD.json (after Gate 1 human approval)
Output: sources/briefs_YYYYMMDD.json
API:    Claude (claude-sonnet-4-6)
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import anthropic

import harness


class SummariseAgent:
    def __init__(self, api_key: str, sources_dir: Path, run_date: date):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.sources_dir = sources_dir
        self.run_date = run_date

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, triage_path: Path) -> Path:
        """Generate briefs for all shortlisted items. Returns path to briefs JSON."""
        with open(triage_path, encoding="utf-8") as f:
            triage_data = json.load(f)

        items = triage_data.get("items", [])
        if not items:
            raise RuntimeError("Triage data has no items.")

        briefs = []

        for item in items:
            brief = self._brief_for_item(item)
            briefs.append(brief)

        self._validate_briefs(briefs)

        output_path = self.sources_dir / f"briefs_{self.run_date.strftime('%Y%m%d')}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_date": self.run_date.isoformat(),
                    "prompt_version": harness.PROMPT_VERSION,
                    "item_count": len(briefs),
                    "items": briefs,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return output_path

    # ------------------------------------------------------------------
    # Generate one brief via Claude
    # ------------------------------------------------------------------

    def _brief_for_item(self, item: dict) -> dict:
        score_breakdown = item.get(harness.FIELD_SCORE_BREAKDOWN, {})
        user_prompt = (
            f"Today is {self.run_date.isoformat()}.\n\n"
            f"Write a structured brief for this policy/regulation item.\n\n"
            f"Item details:\n"
            f"Title: {item.get(harness.FIELD_TITLE)}\n"
            f"URL: {item.get(harness.FIELD_URL)}\n"
            f"Source: {item.get(harness.FIELD_SOURCE_NAME)}\n"
            f"Date: {item.get(harness.FIELD_PUBLISHED_DATE)}\n"
            f"Jurisdiction: {item.get(harness.FIELD_JURISDICTION)}\n"
            f"Persona: {item.get(harness.FIELD_PERSONA)}\n"
            f"Persona rationale: {item.get(harness.FIELD_PERSONA_RATIONALE)}\n"
            f"Confidence: {item.get(harness.FIELD_CONFIDENCE)}\n"
            f"Score breakdown (0–5 each): "
            f"jurisdiction={score_breakdown.get('jurisdiction', '?')}, "
            f"recency={score_breakdown.get('recency', '?')}, "
            f"credibility={score_breakdown.get('credibility', '?')}, "
            f"ac_relevance={score_breakdown.get('ac_relevance', '?')}\n"
            f"Snippet: {item.get(harness.FIELD_SNIPPET)}\n\n"
            f"Return a JSON object with exactly these fields:\n"
            f"- rank: {item.get(harness.FIELD_RANK)}\n"
            f"- title: (as provided)\n"
            f"- url: (as provided)\n"
            f"- what_happened: one plain sentence stating the factual news "
            f"(source, action, date). No [FACT]/[INTERPRETATION] labels.\n"
            f"- why_it_matters_ac: 1–2 sentences on why this matters for NZ/AU "
            f"policy and regulation. Concrete, evidence-led, no labels.\n"
            f"- so_what_for_us: one short sentence on how this connects to "
            f"Allen + Clarke's work or a client situation. May use 'we' / "
            f"'our work'. Not a call-to-action.\n"
            f"- persona: (as provided)\n"
            f"- persona_rationale: one sentence — why this persona fits this item\n"
            f"- confidence: (as provided)\n"
            f"- confidence_evidence: one short sentence citing the specific reason "
            f"for this confidence level — name the source type, recency in days, "
            f"and jurisdiction directness. Use the score breakdown above as evidence. "
            f"Example: 'High — government primary source (Public Service Commission), "
            f"published 16 days ago, NZ direct.'\n\n"
            f"Return ONLY a JSON object. No prose, no markdown fences."
        )

        response = self.client.messages.create(
            model=harness.CLAUDE_MODEL,
            max_tokens=1024,
            system=harness.SUMMARISE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = response.content[0].text.strip()
        content = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`").strip()

        try:
            brief = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                brief = json.loads(match.group())
            else:
                raise RuntimeError(
                    f"Summarise agent: Claude returned unparseable output for "
                    f"item rank {item.get(harness.FIELD_RANK)}.\n{content[:300]}"
                )

        return brief

    # ------------------------------------------------------------------
    # Validate briefs against data contract
    # ------------------------------------------------------------------

    def _validate_briefs(self, briefs: list[dict]) -> None:
        for brief in briefs:
            rank = brief.get(harness.FIELD_RANK, "?")
            errors = harness.validate_fields(
                brief, harness.BRIEF_REQUIRED_FIELDS, f"Brief rank {rank}"
            )
            if errors:
                raise RuntimeError(f"Brief validation error: {errors}")

            if not brief.get(harness.FIELD_SO_WHAT_FOR_US, "").strip():
                raise RuntimeError(
                    f"Brief rank {rank}: 'so_what_for_us' is missing or empty."
                )
