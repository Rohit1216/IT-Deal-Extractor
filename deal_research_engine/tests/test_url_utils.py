from deal_research_engine.utils.url_utils import get_domain, normalize_url, strip_tracking_params


def test_strips_utm_params():
    url = "https://example.com/article?id=123&utm_source=twitter&utm_medium=social"
    assert strip_tracking_params(url) == "https://example.com/article?id=123"


def test_normalize_url_treats_tracking_variants_as_identical():
    a = normalize_url("https://example.com/article?id=123")
    b = normalize_url("https://example.com/article?id=123&utm_source=twitter")
    assert a == b


def test_normalize_url_strips_www_and_fragment():
    a = normalize_url("https://www.example.com/page#section2")
    b = normalize_url("https://example.com/page")
    assert a == b


def test_normalize_url_strips_trailing_slash_except_root():
    assert normalize_url("https://example.com/page/") == normalize_url("https://example.com/page")
    assert normalize_url("https://example.com/") == normalize_url("https://example.com")


def test_normalize_url_does_not_merge_genuinely_different_pages():
    a = normalize_url("https://example.com/article?id=123")
    b = normalize_url("https://example.com/article?id=456")
    assert a != b


def test_get_domain_strips_www_and_port():
    assert get_domain("https://www.example.com:443/page") == "example.com"
    assert get_domain("https://example.com/page") == "example.com"
