"""
Source deduplication (spec sections 7 & 8).

Two separate concerns, handled with two separate confidence levels:

1. Exact duplicates — same canonical_url after normalization. These are
   removed outright (kept once); this is a hard, mechanical rule.

2. Likely-syndicated copies — different URLs/domains but near-identical
   title text (e.g. a BusinessWire release copied verbatim onto Yahoo
   Finance). We do NOT have page content yet in Phase 1 (that's section 21,
   a later stage), so this is a heuristic on title similarity only. Matches
   are flagged (`likely_syndicated=True`, shared `syndicated_group_id`) but
   *kept*, not deleted — the extraction stage needs to know these are not
   independent confirmations (section 8), but removing them here would
   throw away a source that might still be useful (e.g. it's the only copy
   with a working link).
"""

from __future__ import annotations

import difflib
import re

from ..models import Source
from ..utils.logging import get_logger
from ..utils.url_utils import normalize_url

logger = get_logger(__name__)

_TITLE_SIMILARITY_THRESHOLD = 0.90


def _normalize_title(title: str) -> str:
    title = title.lower().strip()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def deduplicate_sources(sources: list[Source]) -> list[Source]:
    """Return a de-duplicated list of sources.

    - Exact URL duplicates (after normalization) are collapsed into one
      entry; later occurrences are dropped, but any distinct query that
      surfaced them is preserved (`matched_queries` merged) so relevance
      scoring downstream isn't penalized for the merge.
    - Remaining sources are then scanned pairwise for likely syndication
      and flagged (not dropped).
    """
    by_canonical: dict[str, Source] = {}
    order: list[str] = []

    exact_dupes = 0
    for src in sources:
        canonical = normalize_url(src.url)
        src = src.model_copy(update={"canonical_url": canonical})

        if canonical in by_canonical:
            exact_dupes += 1
            existing = by_canonical[canonical]
            merged_queries = sorted(set(existing.matched_queries) | set(src.matched_queries))
            by_canonical[canonical] = existing.model_copy(
                update={"matched_queries": merged_queries}
            )
            continue

        by_canonical[canonical] = src
        order.append(canonical)

    deduped = [by_canonical[c] for c in order]
    if exact_dupes:
        logger.info("Duplicate sources removed: %d", exact_dupes)

    flagged = _flag_likely_syndicated(deduped)
    return flagged


def _flag_likely_syndicated(sources: list[Source]) -> list[Source]:
    """Group sources with near-identical titles across different domains."""
    from ..utils.url_utils import get_domain

    normalized_titles = [_normalize_title(s.title) for s in sources]
    group_id_by_index: dict[int, str] = {}
    next_group_id = 0

    n = len(sources)
    for i in range(n):
        for j in range(i + 1, n):
            if get_domain(sources[i].url) == get_domain(sources[j].url):
                continue  # same publisher isn't "syndication", it's just the same site
            if not normalized_titles[i] or not normalized_titles[j]:
                continue
            ratio = difflib.SequenceMatcher(
                None, normalized_titles[i], normalized_titles[j]
            ).ratio()
            if ratio >= _TITLE_SIMILARITY_THRESHOLD:
                group_key = group_id_by_index.get(i) or group_id_by_index.get(j)
                if not group_key:
                    group_key = f"syn-{next_group_id}"
                    next_group_id += 1
                group_id_by_index[i] = group_key
                group_id_by_index[j] = group_key

    if not group_id_by_index:
        return sources

    result = []
    for i, src in enumerate(sources):
        if i in group_id_by_index:
            result.append(
                src.model_copy(
                    update={
                        "likely_syndicated": True,
                        "syndicated_group_id": group_id_by_index[i],
                    }
                )
            )
        else:
            result.append(src)

    n_flagged = len(group_id_by_index)
    if n_flagged:
        logger.info("Likely-syndicated sources flagged: %d", n_flagged)
    return result
