"""
Concrete SearchProvider implementations.

SerperSearchProvider
    Wraps https://serper.dev (a Google Search results API). Recommended
    default for Phase 1 — see README "Why Serper" for the reasoning.

MockSearchProvider
    Returns deterministic canned results for a small set of known test
    subjects (currently "Google Wiz acquisition") plus a generic fallback
    for anything else, so the whole pipeline can be exercised with
    MOCK_MODE=true and zero API calls / zero cost.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

from ..config import Settings
from ..models import SearchResult
from ..utils.logging import get_logger
from .base import SearchProvider

logger = get_logger(__name__)

_MOCK_DATA_PATH = Path(__file__).parent / "mock_data.json"


class SerperSearchProvider(SearchProvider):
    """Search provider backed by the Serper.dev Google Search API."""

    name = "serper"
    ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, api_key: str, timeout_seconds: float = 15.0) -> None:
        if not api_key:
            raise ValueError("SerperSearchProvider requires a non-empty api_key.")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": num_results}

        try:
            response = requests.post(
                self.ENDPOINT, headers=headers, json=payload, timeout=self._timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.warning("Search timed out for query: %s", query)
            return []
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            logger.warning("Search HTTP error (%s) for query: %s", status, query)
            return []
        except requests.exceptions.RequestException as exc:
            logger.warning("Search request failed for query %r: %s", query, exc.__class__.__name__)
            return []

        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.warning("Search returned malformed JSON for query: %s", query)
            return []

        organic = data.get("organic", []) or []
        results: list[SearchResult] = []
        for i, item in enumerate(organic[:num_results]):
            results.append(
                SearchResult(
                    query=query,
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    publication_date=item.get("date"),
                    rank=i + 1,
                    provider=self.name,
                )
            )
        logger.info("Search returned %d results", len(results))
        return [r for r in results if r.url]


class MockSearchProvider(SearchProvider):
    """Offline, deterministic provider for development and unit tests."""

    name = "mock"

    def __init__(self) -> None:
        self._dataset = self._load_dataset()

    @staticmethod
    def _load_dataset() -> dict:
        if _MOCK_DATA_PATH.exists():
            with open(_MOCK_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        query_lower = query.lower()

        matched_key = None
        for key in self._dataset:
            if key.lower() in query_lower:
                matched_key = key
                break

        raw_results = self._dataset.get(matched_key, self._dataset.get("_default", []))

        results: list[SearchResult] = []
        for i, item in enumerate(raw_results[:num_results]):
            results.append(
                SearchResult(
                    query=query,
                    url=item["url"],
                    title=item["title"],
                    snippet=item.get("snippet", ""),
                    publication_date=item.get("publication_date"),
                    rank=i + 1,
                    provider=self.name,
                )
            )
        logger.info("[mock] Search returned %d results", len(results))
        return results


def get_search_provider(settings: Settings) -> SearchProvider:
    """Factory: returns the provider implied by `settings`.

    Mock mode always wins, regardless of which provider name is configured,
    so flipping MOCK_MODE never accidentally requires a real key.
    """
    if settings.mock_mode:
        return MockSearchProvider()

    if settings.search_provider_name == "serper":
        if not settings.search_api_key:
            raise ValueError(
                "SEARCH_API_KEY is required for the 'serper' provider. "
                "Set it in .env or switch to MOCK_MODE=true."
            )
        return SerperSearchProvider(api_key=settings.search_api_key)

    raise ValueError(
        f"Unknown SEARCH_PROVIDER '{settings.search_provider_name}'. "
        "Supported: 'serper' (add more providers in search/provider.py)."
    )
