from deal_research_engine.models import Source
from deal_research_engine.sources.deduplicator import deduplicate_sources


def make_source(url: str, title: str, matched_queries=None) -> Source:
    return Source(
        url=url,
        canonical_url=url,
        title=title,
        matched_queries=matched_queries or [],
    )


def test_exact_duplicate_urls_are_collapsed():
    sources = [
        make_source("https://reuters.com/a?utm_source=x", "Deal A", ["q1"]),
        make_source("https://reuters.com/a", "Deal A", ["q2"]),
    ]
    result = deduplicate_sources(sources)
    assert len(result) == 1
    assert set(result[0].matched_queries) == {"q1", "q2"}


def test_different_pages_are_not_merged():
    sources = [
        make_source("https://reuters.com/a", "Deal A"),
        make_source("https://reuters.com/b", "Deal B"),
    ]
    result = deduplicate_sources(sources)
    assert len(result) == 2


def test_near_identical_titles_on_different_domains_are_flagged_syndicated():
    sources = [
        make_source("https://businesswire.com/press/deal", "Google and Wiz Announce Definitive Agreement"),
        make_source("https://finance.yahoo.com/news/deal", "Google and Wiz Announce Definitive Agreement"),
    ]
    result = deduplicate_sources(sources)
    assert len(result) == 2
    assert all(s.likely_syndicated for s in result)
    assert result[0].syndicated_group_id == result[1].syndicated_group_id


def test_same_domain_is_never_flagged_as_syndicated():
    sources = [
        make_source("https://reuters.com/a", "Google buys Wiz for $32 billion"),
        make_source("https://reuters.com/b", "Google buys Wiz for $32 billion"),
    ]
    result = deduplicate_sources(sources)
    assert not any(s.likely_syndicated for s in result)


def test_dissimilar_titles_are_not_flagged():
    sources = [
        make_source("https://reuters.com/a", "Google buys Wiz for $32 billion"),
        make_source("https://bloomberg.com/b", "FTC opens antitrust review of tech merger"),
    ]
    result = deduplicate_sources(sources)
    assert not any(s.likely_syndicated for s in result)
