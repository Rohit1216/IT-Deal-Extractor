"""
Pydantic data models used across the Deal Research Engine.

Phase 1 only needs the models for the search -> collection -> dedup ->
classification stages. Extraction/validation models (DealField, Evidence,
Conflict, ResearchRun, Deal) will be added in a later phase but are stubbed
here with a short comment so the intended shape is documented up front.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    ACQUIRER_WEBSITE = "acquirer_website"
    TARGET_WEBSITE = "target_website"
    SELLER_WEBSITE = "seller_website"
    INVESTOR_RELATIONS = "investor_relations"
    SEC_FILING = "sec_filing"
    REGULATORY_FILING = "regulatory_filing"
    GOVERNMENT_AGENCY = "government_agency"
    COURT_DOCUMENT = "court_document"
    WIRE_SERVICE = "wire_service"  # BusinessWire, PR Newswire, GlobeNewswire
    FINANCIAL_MEDIA = "financial_media"
    INDUSTRY_PUBLICATION = "industry_publication"
    OTHER = "other"
    UNKNOWN = "unknown"


class SourceTier(str, Enum):
    TIER_1_PRIMARY = "tier_1_primary"
    TIER_2_MAJOR_MEDIA = "tier_2_major_media"
    TIER_3_INDUSTRY = "tier_3_industry"
    TIER_4_OTHER = "tier_4_other"
    UNCLASSIFIED = "unclassified"


class SearchResult(BaseModel):
    """Raw result as returned by a SearchProvider, before any enrichment."""

    query: str
    url: str
    title: str
    snippet: str = ""
    publication_date: Optional[str] = None  # kept as raw string from provider
    rank: Optional[int] = None
    provider: str = "unknown"


class Source(BaseModel):
    """A discovered source, enriched with classification/dedup metadata.

    This matches the source object shape from the spec (section 6), with a
    couple of Phase-1-only additions (`likely_syndicated`, `matched_queries`)
    that make the dedup/classification stages auditable.
    """

    url: str
    canonical_url: str
    title: str
    snippet: str = ""
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    source_type: SourceType = SourceType.UNKNOWN
    source_tier: SourceTier = SourceTier.UNCLASSIFIED
    is_primary_source: bool = False
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None  # canonical_url of the original
    likely_syndicated: bool = False
    syndicated_group_id: Optional[str] = None
    relevance_score: float = 0.0
    content_available: bool = False
    matched_queries: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class ResearchQuery(BaseModel):
    text: str
    category: str = "general"  # e.g. "financial", "regulatory", "advisors"
    iteration: int = 0


class SourceCollectionResult(BaseModel):
    """Output of the source-collection stage: everything up to and including
    deduplication + classification, ready to hand off to extraction later.
    """

    subject: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    queries_used: list[ResearchQuery] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    total_sources_discovered: int = 0
    total_after_dedup: int = 0
    total_relevant: int = 0
    tier_counts: dict[str, int] = Field(default_factory=dict)
    mock_mode: bool = False

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
