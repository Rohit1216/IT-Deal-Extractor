from deal_research_engine.models import Source, SourceTier, SourceType
from deal_research_engine.sources.classifier import classify_source


def make_source(url: str, title: str = "Test") -> Source:
    return Source(url=url, canonical_url=url, title=title)


def test_sec_gov_is_tier1_primary():
    result = classify_source(make_source("https://www.sec.gov/edgar/1234"))
    assert result.source_tier == SourceTier.TIER_1_PRIMARY.value
    assert result.is_primary_source is True
    assert result.source_type == SourceType.GOVERNMENT_AGENCY.value


def test_reuters_is_tier2_major_media():
    result = classify_source(make_source("https://www.reuters.com/technology/story"))
    assert result.source_tier == SourceTier.TIER_2_MAJOR_MEDIA.value
    assert result.is_primary_source is False


def test_businesswire_is_wire_service_not_primary():
    result = classify_source(make_source("https://www.businesswire.com/news/home/123"))
    assert result.source_type == SourceType.WIRE_SERVICE.value
    assert result.is_primary_source is False


def test_unknown_domain_falls_back_to_tier4():
    result = classify_source(make_source("https://some-random-blog.example/post"))
    assert result.source_tier == SourceTier.TIER_4_OTHER.value


def test_subject_domain_is_classified_as_primary():
    result = classify_source(
        make_source("https://blog.google/announcement"),
        subject_domains={"blog.google"},
    )
    assert result.is_primary_source is True
    assert result.source_tier == SourceTier.TIER_1_PRIMARY.value
