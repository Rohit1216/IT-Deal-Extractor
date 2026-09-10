from deal_research_engine.models import ResearchQuery, SearchResult, Source, SourceCollectionResult


def test_search_result_minimal_construction():
    r = SearchResult(query="q", url="https://example.com", title="Title")
    assert r.snippet == ""
    assert r.provider == "unknown"


def test_source_defaults():
    s = Source(url="https://example.com", canonical_url="https://example.com", title="T")
    assert s.is_duplicate is False
    assert s.likely_syndicated is False
    assert s.relevance_score == 0.0
    assert s.content_available is False


def test_research_query_defaults():
    q = ResearchQuery(text="google wiz acquisition")
    assert q.category == "general"
    assert q.iteration == 0


def test_source_collection_result_round_trips_json():
    result = SourceCollectionResult(subject="Google Wiz acquisition")
    payload = result.model_dump_json()
    assert "Google Wiz acquisition" in payload
