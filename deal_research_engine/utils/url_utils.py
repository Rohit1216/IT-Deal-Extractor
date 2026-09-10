"""
URL normalization utilities.

Goal: two URLs that point at the same underlying page (differing only by
tracking params, trailing slash, fragment, casing of the host, etc.) should
normalize to the same `canonical_url`. Two URLs that are genuinely different
pages must NOT be merged.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Params that never carry page-identifying information — safe to strip.
TRACKING_PARAM_PREFIXES = ("utm_",)
TRACKING_PARAMS_EXACT = {
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "ref_src",
    "ref_url",
    "spm",
    "source",
    "cmpid",
    "icid",
}

# Hosts that are commonly served with/without "www." — treat as identical.
_WWW_PREFIX = "www."


def _is_tracking_param(key: str) -> bool:
    key_lower = key.lower()
    if key_lower in TRACKING_PARAMS_EXACT:
        return True
    return any(key_lower.startswith(p) for p in TRACKING_PARAM_PREFIXES)


def strip_tracking_params(url: str) -> str:
    """Remove known tracking query parameters, preserving all others
    (and their original order) since some sites use query params to
    identify genuinely distinct content (e.g. ?id=123).
    """
    parsed = urlparse(url)
    if not parsed.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not _is_tracking_param(k)]
    new_query = urlencode(kept)
    return urlunparse(parsed._replace(query=new_query))


def normalize_url(url: str) -> str:
    """Produce a canonical form of a URL for deduplication purposes.

    Steps:
      1. Lowercase the scheme and host.
      2. Drop a leading "www." (example.com == www.example.com).
      3. Strip the fragment (#section).
      4. Strip known tracking query params.
      5. Sort remaining query params for stable comparison.
      6. Remove a trailing slash on the path (except root "/").
    """
    url = url.strip()
    parsed = urlparse(url)

    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    if netloc.startswith(_WWW_PREFIX):
        netloc = netloc[len(_WWW_PREFIX):]

    path = parsed.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    kept = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_tracking_param(k)
    ]
    kept.sort()
    query = urlencode(kept)

    canonical = urlunparse((scheme, netloc, path, "", query, ""))
    return canonical


def get_domain(url: str) -> str:
    """Return the bare registrable-ish domain (host without 'www.')."""
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith(_WWW_PREFIX):
        netloc = netloc[len(_WWW_PREFIX):]
    # Drop a port if present.
    return netloc.split(":")[0]
