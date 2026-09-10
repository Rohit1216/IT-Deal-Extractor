"""
CLI entry point for Phase 1.

Usage:
    python scripts/run_research.py "Google Wiz acquisition"

Run this from the project root (the folder that contains the
`deal_research_engine` package), not from inside `scripts/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python scripts/run_research.py` from the project root
# without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from deal_research_engine.config import get_settings  # noqa: E402
from deal_research_engine.search.provider import get_search_provider  # noqa: E402
from deal_research_engine.sources.collector import SourceCollector  # noqa: E402
from deal_research_engine.utils.logging import get_logger  # noqa: E402

logger = get_logger(__name__)


def slugify(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in text.strip()]
    slug = "".join(keep)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "research"


def main() -> int:
    parser = argparse.ArgumentParser(description="Deal Research Engine — Phase 1")
    parser.add_argument("subject", help='Company or transaction, e.g. "Google Wiz acquisition"')
    args = parser.parse_args()

    settings = get_settings()

    print("=" * 40)
    print("DEAL RESEARCH ENGINE")
    print("=" * 20)
    print()
    print(f"Query:\n{args.subject}\n")
    if settings.mock_mode:
        print("(MOCK_MODE=true — no external API calls will be made)\n")
    else:
        problems = settings.validate_for_live_run()
        if problems:
            for p in problems:
                print(f"ERROR: {p}")
            return 1

    provider = get_search_provider(settings)

    print("Generating search queries...")
    print("Searching web...")
    collector = SourceCollector(search_provider=provider, settings=settings)
    result = collector.collect(args.subject)

    print()
    print(f"Sources discovered: {result.total_sources_discovered}")
    print(f"After deduplication: {result.total_after_dedup}")
    print(f"Relevant sources: {result.total_relevant}")
    for tier, count in sorted(result.tier_counts.items()):
        print(f"  {tier}: {count}")

    print()
    print("=" * 40)
    print("RESULT")
    print("=" * 6)
    print()
    print("(Deal extraction is not part of Phase 1 — this milestone stops")
    print(" at source collection, deduplication, and classification.)")
    print()
    print("Top sources:")
    for s in result.sources[:10]:
        primary_flag = " [PRIMARY]" if s.is_primary_source else ""
        syndicated_flag = " [SYNDICATED?]" if s.likely_syndicated else ""
        print(f"  ({s.relevance_score:.2f}) [{s.source_tier}]{primary_flag}{syndicated_flag} {s.title}")
        print(f"        {s.canonical_url}")

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = settings.output_dir / f"{slugify(args.subject)}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(json.loads(result.model_dump_json()), f, indent=2, ensure_ascii=False)

    print()
    print(f"Full structured result saved to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
