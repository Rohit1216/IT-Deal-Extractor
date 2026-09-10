"""
Central configuration for the Deal Research Engine.

Everything that could change between environments (API keys, iteration
limits, thresholds, mock mode) lives here and is loaded from environment
variables / a local .env file. Nothing here should ever contain a real
secret — .env is git-ignored and only .env.example is committed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# python-dotenv is optional at runtime, but we depend on it (see
# requirements.txt) so .env is picked up automatically without the caller
# having to export variables manually.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is a declared dependency
    pass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # --- Mode -------------------------------------------------------
    mock_mode: bool = field(default_factory=lambda: _env_bool("MOCK_MODE", True))

    # --- API keys (never logged, never hard-coded) -------------------
    claude_api_key: str | None = field(default_factory=lambda: os.getenv("CLAUDE_API_KEY"))
    search_api_key: str | None = field(default_factory=lambda: os.getenv("SEARCH_API_KEY"))
    search_provider_name: str = field(
        default_factory=lambda: os.getenv("SEARCH_PROVIDER", "serper")
    )

    # --- Research loop controls --------------------------------------
    max_search_iterations: int = field(
        default_factory=lambda: _env_int("MAX_SEARCH_ITERATIONS", 5)
    )
    max_sources: int = field(default_factory=lambda: _env_int("MAX_SOURCES", 50))
    min_relevance_score: float = field(
        default_factory=lambda: _env_float("MIN_RELEVANCE_SCORE", 0.50)
    )
    results_per_query: int = field(
        default_factory=lambda: _env_int("RESULTS_PER_QUERY", 10)
    )

    # --- Paths ---------------------------------------------------------
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "outputs")))

    def validate_for_live_run(self) -> list[str]:
        """Return a list of problems that would block a *non-mock* run.

        Kept separate from __post_init__ so mock-mode / unit tests never
        need a real key to construct Settings.
        """
        problems: list[str] = []
        if not self.mock_mode and not self.search_api_key:
            problems.append(
                "SEARCH_API_KEY is not set. Set it in .env or run with MOCK_MODE=true."
            )
        return problems


def get_settings() -> Settings:
    """Factory so callers/tests can always get a fresh read of the env."""
    return Settings()
