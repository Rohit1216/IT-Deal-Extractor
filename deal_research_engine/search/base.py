"""
Abstract search provider interface.

Every concrete provider (Serper, Google, Bing, Tavily, ...) implements
`search()` and returns plain `SearchResult` objects, so nothing downstream
of this layer needs to know which API was actually called.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SearchResult


class SearchProvider(ABC):
    """Interface every web search backend must implement."""

    name: str = "unknown"

    @abstractmethod
    def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Run a single query and return normalized results.

        Implementations must not raise on ordinary failure modes (timeout,
        HTTP error, rate limit, empty result) — they should log a warning
        and return an empty list so the caller can continue with other
        queries/sources.
        """
        raise NotImplementedError
