"""
SourceCollector — Phase 1 orchestration.

Wires together: query_generator -> SearchProvider -> Source objects ->
deduplicate_sources -> classify_source -> score_source -> filtering.

This intentionally stops at classification + scoring (spec section 35,
milestone 1). Content retrieval, extraction, validation and storage are
later stages and are not called from here.
"""

from __future__ import annotations

from ..config import Settings
from ..models import Source, SourceCollectionResult
from ..query_generator import generate_queries
from ..search.base import SearchProvider
from ..utils.logging import get_logger
from .classifier import classify_source
from .deduplicator import deduplicate_sources
from .relevance import score_source

logger = get_logger(__name__)


class SourceCollector:
    def __init__(self, search_provider: SearchProvider, settings: Settings):
        self._search = search_provider
        self._settings = settings

    def collect(self, subject: str, subject_domains: set[str] | None = None) -> SourceCollectionResult:
        queries = generate_queries(subject, iteration=0)
        logger.info("Generated %d search queries", len(queries))

        raw_sources: list[Source] = []
        for q in queries:
            logger.info("Searching query: %s", q.text)
            results = self._search.search(q.text, num_results=self._settings.results_per_query)
            for r in results:
                raw_sources.append(
                    Source(
                        url=r.url,
                        canonical_url=r.url,  # normalized properly during dedup
                        title=r.title,
                        snippet=r.snippet,
                        publication_date=r.publication_date,
                        matched_queries=[q.text],
                    )
                )

        total_discovered = len(raw_sources)
        logger.info("Total raw source hits across all queries: %d", total_discovered)

        deduped = deduplicate_sources(raw_sources)
        total_after_dedup = len(deduped)

        classified = [classify_source(s, subject_domains=subject_domains) for s in deduped]

        scored = [s.model_copy(update={"relevance_score": score_source(s, subject)}) for s in classified]

        # Rank by relevance, then apply the configured floor and cap.
        scored.sort(key=lambda s: s.relevance_score, reverse=True)
        relevant = [s for s in scored if s.relevance_score >= self._settings.min_relevance_score]
        relevant = relevant[: self._settings.max_sources]

        logger.info(
            "Sources discovered: %d | after dedup: %d | relevant (>= %.2f): %d",
            total_discovered,
            total_after_dedup,
            self._settings.min_relevance_score,
            len(relevant),
        )

        tier_counts: dict[str, int] = {}
        for s in relevant:
            tier_counts[str(s.source_tier)] = tier_counts.get(str(s.source_tier), 0) + 1

        return SourceCollectionResult(
            subject=subject,
            queries_used=queries,
            sources=relevant,
            total_sources_discovered=total_discovered,
            total_after_dedup=total_after_dedup,
            total_relevant=len(relevant),
            tier_counts=tier_counts,
            mock_mode=self._settings.mock_mode,
        )
