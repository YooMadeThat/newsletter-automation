"""
orchestrator.py — Allen + Clarke Intel: Main Entry Point

Run this file to execute the full newsletter workflow.

Usage:
    python orchestrator.py

The workflow:
    1. Research agent   → Perplexity search → raw_YYYYMMDD.json
    2. Triage agent     → Score + rank → triage_YYYYMMDD.json
    3. Summarise agent  → Per-item briefs → briefs_YYYYMMDD.json
    4. Validation pass  → Hard rules check → validation_YYYYMMDD.json
    5. Compose agent    → Full newsletter → newsletter_YYYYMMDD.md
    6. Format agent     → Word render → newsletter_YYYYMMDD.docx
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box

import anthropic
import harness
from agents import (
    ResearchAgent,
    TriageAgent,
    SummariseAgent,
    ComposeAgent,
    FormatAgent,
)

load_dotenv()
console = Console()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
SOURCES_DIR = BASE_DIR / "sources"
OUTPUT_DIR = BASE_DIR / "output"
BRAND_DIR = BASE_DIR / "brand"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    console.rule("[bold blue]Allen + Clarke Intel — Policy + Regulation Newsletter[/bold blue]")
    run_date = date.today()
    console.print(f"Run date: [bold]{run_date.isoformat()}[/bold]  |  Prompt version: {harness.PROMPT_VERSION}\n")

    perplexity_key = _require_env("PERPLEXITY_API_KEY")
    anthropic_key = _require_env("ANTHROPIC_API_KEY")

    # ------------------------------------------------------------------
    # Step 1: Research
    # ------------------------------------------------------------------
    console.print("[bold cyan]Step 1 of 6 — Research Agent (Perplexity)[/bold cyan]")
    research_agent = ResearchAgent(perplexity_key, SOURCES_DIR, run_date)
    try:
        raw_path = research_agent.run()
    except RuntimeError as exc:
        _fatal(f"Research agent failed: {exc}")
        return

    with open(raw_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    raw_count = raw_data.get("item_count", 0)
    console.print(f"  Found [bold]{raw_count}[/bold] candidate items → {raw_path.name}")

    if raw_count < harness.MIN_SHORTLIST_ITEMS:
        console.print(
            f"  [yellow]WARNING: Only {raw_count} items found. "
            f"Minimum required is {harness.MIN_SHORTLIST_ITEMS}.[/yellow]"
        )

    # ------------------------------------------------------------------
    # Step 2: Triage
    # ------------------------------------------------------------------
    console.print("\n[bold cyan]Step 2 of 6 — Triage Agent (Claude)[/bold cyan]")
    triage_agent = TriageAgent(anthropic_key, SOURCES_DIR, run_date)
    try:
        triage_path = triage_agent.run(raw_path)
    except RuntimeError as exc:
        _fatal(f"Triage agent failed: {exc}")
        return

    with open(triage_path, encoding="utf-8") as f:
        triage_data = json.load(f)

    shortlist = triage_data.get("items", [])
    console.print(f"  Shortlisted [bold]{len(shortlist)}[/bold] items → {triage_path.name}")
    _display_shortlist(shortlist)

    triage_meta = {
        "raw_items": raw_count,
        "num_queries": len(harness.SEARCH_QUERIES),
        "shortlist_count": len(shortlist),
    }

    # ------------------------------------------------------------------
    # Step 3: Summarise
    # ------------------------------------------------------------------
    console.print("\n[bold cyan]Step 3 of 6 — Summarise Agent (Claude)[/bold cyan]")
    summarise_agent = SummariseAgent(anthropic_key, SOURCES_DIR, run_date)
    try:
        briefs_path = summarise_agent.run(triage_path)
    except RuntimeError as exc:
        _fatal(f"Summarise agent failed: {exc}")
        return

    console.print(f"  Briefs written → {briefs_path.name}")

    # ------------------------------------------------------------------
    # Step 4: Validation Pass
    # ------------------------------------------------------------------
    console.print("\n[bold cyan]Step 4 of 6 — Validation Pass (Claude)[/bold cyan]")
    validation_path = SOURCES_DIR / f"validation_{run_date.strftime('%Y%m%d')}.json"
    try:
        validation_result = _run_validation(anthropic_key, briefs_path, validation_path, run_date)
    except RuntimeError as exc:
        _fatal(f"Validation pass failed: {exc}")
        return

    _display_validation(validation_result)

    if not validation_result.get(harness.FIELD_OVERALL_PASS, False):
        _fatal(
            "Validation checks failed. Review the issues above, correct the briefs, "
            "and re-run from Step 3. Workflow halted."
        )
        return

    # ------------------------------------------------------------------
    # Step 5: Compose
    # ------------------------------------------------------------------
    console.print("\n[bold cyan]Step 5 of 6 — Compose Agent (Claude)[/bold cyan]")
    compose_agent = ComposeAgent(anthropic_key, SOURCES_DIR, OUTPUT_DIR, BRAND_DIR, run_date)
    try:
        md_path = compose_agent.run(briefs_path, triage_meta=triage_meta)
    except RuntimeError as exc:
        _fatal(f"Compose agent failed: {exc}")
        return

    console.print(f"  Newsletter Markdown written → {md_path.name}")

    # ------------------------------------------------------------------
    # Step 6: Format
    # ------------------------------------------------------------------
    console.print("\n[bold cyan]Step 6 of 6 — Format Agent (Word render)[/bold cyan]")
    format_agent = FormatAgent(OUTPUT_DIR, run_date)
    try:
        docx_path = format_agent.run(md_path)
    except Exception as exc:
        _fatal(f"Format agent failed: {exc}")
        return

    console.print(f"  Word document written → {docx_path.name}")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    console.rule("[bold green]Workflow Complete[/bold green]")
    console.print(f"\n  Markdown: {md_path}")
    console.print(f"  Word doc: {docx_path}\n")


# ---------------------------------------------------------------------------
# Validation pass (invokes Claude with a short compliance-check prompt)
# ---------------------------------------------------------------------------

def _run_validation(
    api_key: str,
    briefs_path: Path,
    validation_path: Path,
    run_date: date,
) -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    with open(briefs_path, encoding="utf-8") as f:
        briefs_text = f.read()

    response = client.messages.create(
        model=harness.CLAUDE_MODEL,
        max_tokens=1024,
        system=harness.VALIDATION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today is {run_date.isoformat()}.\n\n"
                    f"Review these briefs against the hard rules and return "
                    f"a validation report as a JSON object.\n\n"
                    f"BRIEFS:\n{briefs_text}\n\n"
                    f"Return ONLY a JSON object with fields: "
                    f"checked_at, overall_pass, checks. No prose."
                ),
            }
        ],
    )

    import re
    content = response.content[0].text.strip()
    content = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`").strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"Validation pass returned unparseable output:\n{content[:300]}")

    result[harness.FIELD_CHECKED_AT] = datetime.now(timezone.utc).isoformat()

    with open(validation_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _display_shortlist(shortlist: list[dict]) -> None:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
    table.add_column("Rank", width=4)
    table.add_column("Title", width=40)
    table.add_column("Source", width=20)
    table.add_column("Date", width=12)
    table.add_column("Juri.", width=10)
    table.add_column("Score", width=6)
    table.add_column("Persona", width=8)

    for item in shortlist:
        table.add_row(
            str(item.get(harness.FIELD_RANK, "")),
            str(item.get(harness.FIELD_TITLE, ""))[:38],
            str(item.get(harness.FIELD_SOURCE_NAME, ""))[:18],
            str(item.get(harness.FIELD_PUBLISHED_DATE, ""))[:10],
            str(item.get(harness.FIELD_JURISDICTION, "")),
            str(item.get(harness.FIELD_SCORE_TOTAL, "")),
            str(item.get(harness.FIELD_PERSONA, "")),
        )

    console.print(table)


def _display_validation(result: dict) -> None:
    overall = result.get(harness.FIELD_OVERALL_PASS, False)
    status = "[green]PASS[/green]" if overall else "[red]FAIL[/red]"
    console.print(f"  Validation result: {status}")

    checks = result.get(harness.FIELD_CHECKS, [])
    for check in checks:
        passed = check.get(harness.FIELD_PASSED, False)
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        rule = check.get(harness.FIELD_RULE, "")
        detail = check.get(harness.FIELD_DETAIL, "")
        console.print(f"    {icon} {rule}: {detail}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _require_env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value or value.startswith("your_"):
        _fatal(
            f"Environment variable '{key}' is not set or still contains the placeholder value. "
            f"Set it in your .env file."
        )
    return value


def _fatal(message: str) -> None:
    console.print(f"\n[bold red]FATAL: {message}[/bold red]\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
