"""
Source relevance scoring (spec section 20).

Phase 1 only has search metadata (title/snippet/date) and classification
to work with — no extracted deal fields yet, since extraction is a later
stage. So this implements the subset of factors that are available now:

  - keyword overlap between the source title/snippet and the subject
  - source tier / primary-source authority
  - recency (a rough bonus for having a resolvable publication date)

Advisor/deal-value-specific relevance (factors that need extracted fields)
are intentionally left as a documented gap — the scoring function is a
single, transparent place to add those weights once extraction exists,
rather than leaving the LLM to decide relevance implicitly.
"""

from __future__ import annotations

import re

from ..models import Source, SourceTier

_TIER_WEIGHT = {
    SourceTier.TIER_1_PRIMARY: 0.40,
    SourceTier.TIER_2_MAJOR_MEDIA: 0.25,
    SourceTier.TIER_3_INDUSTRY: 0.15,
    SourceTier.TIER_4_OTHER: 0.05,
    SourceTier.UNCLASSIFIED: 0.0,
}
# Enum members compare equal to their `.value` string because Source uses
# use_enum_values=True, so the dict above also matches the plain strings
# pydantic will actually store.
_TIER_WEIGHT = {(k.value if hasattr(k, "value") else k): v for k, v in _TIER_WEIGHT.items()}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def score_source(source: Source, subject: str) -> float:
    """Return a 0.0-1.0 relevance score. Weights sum to 1.0 across the
    three factors currently implemented (keyword 0.45, tier 0.40, date 0.15)."""
    subject_tokens = _tokenize(subject)
    text_tokens = _tokenize(f"{source.title} {source.snippet}")

    if subject_tokens:
        overlap = len(subject_tokens & text_tokens) / len(subject_tokens)
    else:
        overlap = 0.0
    keyword_score = min(overlap, 1.0) * 0.45

    tier_score = _TIER_WEIGHT.get(source.source_tier, 0.0)
    if source.is_primary_source:
        tier_score = max(tier_score, _TIER_WEIGHT.get(SourceTier.TIER_1_PRIMARY.value, 0.40))

    date_score = 0.15 if source.publication_date else 0.0

    return round(min(keyword_score + tier_score + date_score, 1.0), 3)
