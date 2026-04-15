"""
research_agent.py — Agent 1: Perplexity Web Search

Runs 4–6 targeted queries against the Perplexity API to find recent
policy and regulatory items relevant to New Zealand and Australia.

Input:  Configuration from harness.py (queries, date window, API key)
Output: sources/raw_YYYYMMDD.json — deduplicated list of candidate items
API:    Perplexity sonar-pro (REST)
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

import harness


class ResearchAgent:
    def __init__(self, api_key: str, sources_dir: Path, run_date: date):
        self.api_key = api_key
        self.sources_dir = sources_dir
        self.run_date = run_date
        self.cutoff_date = run_date - timedelta(days=harness.MAX_ITEM_AGE_DAYS)
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Path:
        """Execute all queries, deduplicate, and save raw JSON. Returns output path."""
        year = self.run_date.year
        queries = [q.format(year=year) for q in harness.SEARCH_QUERIES]

        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for query in queries:
            items = self._query_perplexity(query)
            for item in items:
                url = item.get(harness.FIELD_URL, "").strip()
                if not url or url in seen_urls:
                    continue
                if not self._is_within_date_window(item):
                    continue
                seen_urls.add(url)
                all_items.append(item)
            # Polite delay between queries
            time.sleep(1)

        output_path = self.sources_dir / f"raw_{self.run_date.strftime('%Y%m%d')}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_date": self.run_date.isoformat(),
                    "prompt_version": harness.PROMPT_VERSION,
                    "item_count": len(all_items),
                    "items": all_items,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return output_path

    # ------------------------------------------------------------------
    # Perplexity API call
    # ------------------------------------------------------------------

    def _query_perplexity(self, query: str) -> list[dict]:
        payload = {
            "model": harness.PERPLEXITY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant. For each search query, return "
                        "a JSON array of relevant results. Each result must include: "
                        "title, url, source_name, published_date (YYYY-MM-DD or empty string), "
                        "snippet (2-3 sentence summary), jurisdiction_tag (NZ/AU/NZ\u2013AU/"
                        "INT-relevant/INT-irrelevant/unknown), is_paywalled (true/false). "
                        "Return ONLY the JSON array — no prose, no markdown code fences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Search for recent New Zealand and Australian policy and regulation "
                        f"news. Query: {query}\n\n"
                        f"Focus on: government consultations, regulatory updates, policy reform, "
                        f"implementation guidance, compliance changes. "
                        f"Return results from the last {harness.MAX_ITEM_AGE_DAYS} days only. "
                        f"Today is {self.run_date.isoformat()}."
                    ),
                },
            ],
            "search_recency_filter": harness.PERPLEXITY_RECENCY_FILTER,
            "return_citations": True,
            "temperature": 0.1,
        }

        try:
            response = self._session.post(
                f"{harness.PERPLEXITY_API_BASE}/chat/completions",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Perplexity API error for query '{query}': {exc}"
            ) from exc

        raw_content = response.json()["choices"][0]["message"]["content"]
        items = self._parse_response(raw_content, query)
        return items

    # ------------------------------------------------------------------
    # Parse Perplexity response into structured items
    # ------------------------------------------------------------------

    def _parse_response(self, content: str, query: str) -> list[dict]:
        # Strip markdown fences if model wraps output despite instructions
        content = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`").strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Attempt to extract JSON array from within the response
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    return []
            else:
                return []

        if not isinstance(data, list):
            return []

        results = []
        for raw in data:
            if not isinstance(raw, dict):
                continue
            item = self._normalise_item(raw, query)
            if item:
                results.append(item)
        return results

    # ------------------------------------------------------------------
    # Normalise a single raw item into the data contract fields
    # ------------------------------------------------------------------

    def _normalise_item(self, raw: dict[str, Any], query: str) -> dict | None:
        title = str(raw.get("title", "")).strip()
        url = str(raw.get("url", "")).strip()
        if not title or not url:
            return None

        jurisdiction_raw = str(raw.get("jurisdiction_tag", "unknown")).strip()
        jurisdiction = self._normalise_jurisdiction(jurisdiction_raw)

        return {
            harness.FIELD_TITLE: title,
            harness.FIELD_URL: url,
            harness.FIELD_SOURCE_NAME: str(raw.get("source_name", "")).strip(),
            harness.FIELD_PUBLISHED_DATE: str(raw.get("published_date", "")).strip(),
            harness.FIELD_SNIPPET: str(raw.get("snippet", "")).strip(),
            harness.FIELD_JURISDICTION_TAG: jurisdiction,
            harness.FIELD_IS_PAYWALLED: bool(raw.get("is_paywalled", False)),
            harness.FIELD_QUERY_USED: query,
        }

    # ------------------------------------------------------------------
    # Normalise jurisdiction tag to canonical values
    # ------------------------------------------------------------------

    def _normalise_jurisdiction(self, raw: str) -> str:
        raw_lower = raw.lower().replace(" ", "").replace("/", "").replace("-", "")
        mapping = {
            "nz": harness.JURISDICTION_NZ,
            "newzealand": harness.JURISDICTION_NZ,
            "au": harness.JURISDICTION_AU,
            "australia": harness.JURISDICTION_AU,
            "nzau": harness.JURISDICTION_NZ_AU,
            "aunz": harness.JURISDICTION_NZ_AU,
            "intrelevant": harness.JURISDICTION_INT_RELEVANT,
            "international": harness.JURISDICTION_INT_IRRELEVANT,
            "intirrelevant": harness.JURISDICTION_INT_IRRELEVANT,
        }
        return mapping.get(raw_lower, harness.JURISDICTION_UNKNOWN)

    # ------------------------------------------------------------------
    # Date window check
    # ------------------------------------------------------------------

    def _is_within_date_window(self, item: dict) -> bool:
        date_str = item.get(harness.FIELD_PUBLISHED_DATE, "")
        if not date_str:
            # No date — include with caution (triage will down-score)
            return True
        try:
            published = date.fromisoformat(date_str[:10])
            return published >= self.cutoff_date
        except ValueError:
            return True  # Unparseable date — let triage handle it
