"""
compose_agent.py — Agent 4: Assemble Full Newsletter Output

Reads per-item briefs and brand rules, then produces the full structured
Markdown newsletter output across all 4 sections. Identifies the strongest
signal item and drafts the 100–150 word insert.

Input:  sources/briefs_YYYYMMDD.json
        brand/ac_style_guide.md
        brand/newsletter_template_rules.md
Output: output/newsletter_YYYYMMDD.md
API:    Claude (claude-sonnet-4-6)
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import anthropic

import harness


class ComposeAgent:
    def __init__(
        self,
        api_key: str,
        sources_dir: Path,
        output_dir: Path,
        brand_dir: Path,
        run_date: date,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.sources_dir = sources_dir
        self.output_dir = output_dir
        self.brand_dir = brand_dir
        self.run_date = run_date

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, briefs_path: Path, triage_meta: dict | None = None) -> Path:
        """
        Assemble full newsletter Markdown. Returns output path.
        If insert word count is out of range, retries once.

        triage_meta: optional dict with keys raw_items, num_queries, shortlist_count
        """
        with open(briefs_path, encoding="utf-8") as f:
            briefs_data = json.load(f)

        style_guide = self._load_brand_file("ac_style_guide.md")
        template_rules = self._load_brand_file("newsletter_template_rules.md")

        output = self._call_claude(
            briefs_data["items"], style_guide, template_rules, triage_meta=triage_meta
        )

        # Verify insert word count; retry once if out of range
        insert_wc = self._extract_insert_word_count(output)
        if not (harness.NEWSLETTER_INSERT_MIN_WORDS <= insert_wc <= harness.NEWSLETTER_INSERT_MAX_WORDS):
            output = self._call_claude(
                briefs_data["items"],
                style_guide,
                template_rules,
                triage_meta=triage_meta,
                rewrite_note=(
                    f"Your previous newsletter insert was {insert_wc} words. "
                    f"Rewrite Section 4 so the insert is exactly "
                    f"{harness.NEWSLETTER_INSERT_MIN_WORDS}–"
                    f"{harness.NEWSLETTER_INSERT_MAX_WORDS} words. "
                    f"Keep Sections 1, 2, and 3 unchanged."
                ),
            )

        output_path = self.output_dir / f"newsletter_{self.run_date.strftime('%Y%m%d')}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)

        return output_path

    # ------------------------------------------------------------------
    # Claude call
    # ------------------------------------------------------------------

    def _call_claude(
        self,
        items: list[dict],
        style_guide: str,
        template_rules: str,
        triage_meta: dict | None = None,
        rewrite_note: str = "",
    ) -> str:
        items_text = json.dumps(items, indent=2, ensure_ascii=False)

        rewrite_block = f"\n\nIMPORTANT: {rewrite_note}" if rewrite_note else ""

        if triage_meta:
            triage_block = (
                f"\nTRIAGE META (use for the trace sentence in Section 1):\n"
                f"  Raw items identified: {triage_meta.get('raw_items', '?')}\n"
                f"  Searches run: {triage_meta.get('num_queries', '?')}\n"
                f"  Items selected: {triage_meta.get('shortlist_count', '?')}\n"
            )
        else:
            triage_block = ""

        user_prompt = (
            f"Today is {self.run_date.isoformat()}.\n"
            f"{triage_block}"
            f"{rewrite_block}\n\n"
            f"Produce the full newsletter output for the Allen + Clarke "
            f"Policy + Regulation section.\n\n"
            f"Use the brand style guide and template rules provided in your "
            f"system prompt. Follow all section formats exactly.\n\n"
            f"ITEM BRIEFS:\n{items_text}\n\n"
            f"Produce all four sections in order. Return only the Markdown "
            f"content — no preamble, no explanation."
        )

        system = (
            f"{harness.COMPOSE_SYSTEM_PROMPT}\n\n"
            f"--- STYLE GUIDE ---\n{style_guide}\n\n"
            f"--- TEMPLATE RULES ---\n{template_rules}"
        )

        response = self.client.messages.create(
            model=harness.CLAUDE_MODEL,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return response.content[0].text.strip()

    # ------------------------------------------------------------------
    # Count insert body words using the shared harness utility.
    # Never trusts Claude's self-reported [Word count: N] tag.
    # ------------------------------------------------------------------

    def _extract_insert_word_count(self, output: str) -> int:
        body = harness.extract_insert_body(output)
        return harness.word_count(body)

    # ------------------------------------------------------------------
    # Load brand file contents
    # ------------------------------------------------------------------

    def _load_brand_file(self, filename: str) -> str:
        path = self.brand_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Brand file not found: {path}. "
                "Ensure brand/ directory is populated before running compose agent."
            )
        return path.read_text(encoding="utf-8")
