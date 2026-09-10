"""
Source classification (spec section 5).

Deliberately simple and *configurable*: classification is driven by the
plain dicts below (domain -> type/tier), not buried in conditional logic,
so adding a publisher or a new regulator is a one-line change and doesn't
require touching the classification function itself.
"""

from __future__ import annotations

from ..models import Source, SourceTier, SourceType
from ..utils.url_utils import get_domain

# --- Tier 1: primary sources --------------------------------------------
GOVERNMENT_REGULATOR_DOMAINS: dict[str, str] = {
    "sec.gov": "SEC",
    "ftc.gov": "FTC",
    "justice.gov": "DOJ",
    "ec.europa.eu": "European Commission",
    "gov.uk": "UK Government / CMA",
    "canada.ca": "Competition Bureau Canada",
}

# --- Tier 2: major financial / business media ---------------------------
MAJOR_MEDIA_DOMAINS: set[str] = {
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "cnbc.com",
    "marketwatch.com",
    "finance.yahoo.com",
    "yahoo.com",
    "apnews.com",
    "nytimes.com",
    "washingtonpost.com",
}

# --- Wire services: original distribution, but frequently syndicated ----
WIRE_SERVICE_DOMAINS: set[str] = {
    "businesswire.com",
    "prnewswire.com",
    "globenewswire.com",
}

# --- Tier 3: industry / trade publications (extend as needed) -----------
INDUSTRY_PUBLICATION_DOMAINS: set[str] = {
    "techcrunch.com",
    "theinformation.com",
    "axios.com",
    "sec-edgar.com",
}


def classify_source(source: Source, subject_domains: set[str] | None = None) -> Source:
    """Return a copy of `source` with source_type / source_tier / is_primary
    populated. `subject_domains` are the acquirer/target/seller's own
    domains when known (e.g. {"blog.google", "wiz.io"}) — matches there are
    classified as company-owned Tier 1 sources.
    """
    domain = get_domain(source.url)
    subject_domains = subject_domains or set()

    source_type = SourceType.UNKNOWN
    source_tier = SourceTier.UNCLASSIFIED
    is_primary = False

    if domain in GOVERNMENT_REGULATOR_DOMAINS:
        source_type = SourceType.GOVERNMENT_AGENCY
        source_tier = SourceTier.TIER_1_PRIMARY
        is_primary = True
    elif any(domain == d or domain.endswith("." + d) for d in subject_domains):
        source_type = SourceType.ACQUIRER_WEBSITE  # caller can refine acquirer/target/seller
        source_tier = SourceTier.TIER_1_PRIMARY
        is_primary = True
    elif domain in WIRE_SERVICE_DOMAINS:
        source_type = SourceType.WIRE_SERVICE
        source_tier = SourceTier.TIER_2_MAJOR_MEDIA
        is_primary = False
    elif domain in MAJOR_MEDIA_DOMAINS:
        source_type = SourceType.FINANCIAL_MEDIA
        source_tier = SourceTier.TIER_2_MAJOR_MEDIA
        is_primary = False
    elif domain in INDUSTRY_PUBLICATION_DOMAINS:
        source_type = SourceType.INDUSTRY_PUBLICATION
        source_tier = SourceTier.TIER_3_INDUSTRY
        is_primary = False
    else:
        source_type = SourceType.OTHER
        source_tier = SourceTier.TIER_4_OTHER
        is_primary = False

    return source.model_copy(
        update={
            # model_copy() does not re-run validators, so `use_enum_values`
            # on the model won't coerce these — store the plain string
            # ourselves to keep every Source.source_tier/.source_type
            # instance consistently a str, never a raw Enum member.
            "source_type": source_type.value,
            "source_tier": source_tier.value,
            "is_primary_source": is_primary,
            "publisher": source.publisher or _guess_publisher(domain),
        }
    )


def _guess_publisher(domain: str) -> str:
    """Very small heuristic: turn 'reuters.com' into 'Reuters'. Good enough
    for a display label; not meant to be authoritative.
    """
    label = domain.split(".")[0]
    return label.replace("-", " ").title()
