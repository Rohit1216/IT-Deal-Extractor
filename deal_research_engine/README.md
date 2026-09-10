# Deal Research Engine — Phase 1

Phase 1 builds only the first milestone of the pipeline:

```
INPUT → SEARCH → SOURCE COLLECTION → SOURCE DEDUPLICATION →
BASIC SOURCE CLASSIFICATION → RELEVANCE SCORING → JSON OUTPUT
```

Query generation, web search, source dedup, source classification and a
transparent relevance score are implemented and tested. Content retrieval,
LLM-based deal extraction, cross-source validation, conflict detection and
the SQLite store are **not** part of this phase — they're the next
milestones, once you confirm this one works.

---

## 1–7. Design decisions

**1–2. Recommended search API: [Serper](https://serper.dev)**
It's a thin wrapper around Google Search results, returns clean JSON
(title/link/snippet/date), has a generous free tier, and needs no SDK —
just an API key and a POST request. Bing and Tavily are reasonable
alternatives (Tavily in particular is built for LLM/agentic research and
already fetches page content, which would help Phase 2's content
retrieval stage) — swapping providers later only means adding a new class
in `search/provider.py` that implements `SearchProvider.search()`.

**3. Python libraries:** `pydantic` (strict data models), `requests`
(HTTP), `python-dotenv` (env loading), `pytest` (tests). Deliberately
nothing else yet — no ORM, no async framework, no task queue.

**4. Major technical risks:**
- Search APIs return inconsistent/missing publication dates, which weakens
  recency-based scoring and later "most recent status" extraction.
- Syndicated-content detection is title-similarity only in this phase
  (no page content yet), so it will miss syndicated copies with reworded
  headlines and can rarely false-positive on two genuinely different
  stories that happen to share a generic headline.
- Rate limits / API cost scale with `MAX_SEARCH_ITERATIONS × queries ×
  RESULTS_PER_QUERY` — worth tuning down before running against many deals.

**5. Limitations to expect in this phase:** no page content, no extracted
deal fields, no evidence, no confidence scores, no conflict detection, no
persistence between runs — this milestone only proves out search →
collection → dedup → classification → scoring.

**6. Preventing hallucinated deal information:** none is extracted yet, so
there's nothing to hallucinate. The design principle carried into later
phases: every extracted field must cite an evidence excerpt from a
retrieved source (section 12–13 of the brief), and the extractor will be
instructed to output `NOT_FOUND` rather than guess.

**7. Maximizing source coverage:** broad multi-angle query generation
(general/financial/advisors/regulatory/publishers/status — 21 queries per
subject today), a `MAX_SEARCH_ITERATIONS` hook already wired into config
for the iterative research loop (Phase 2), and a relevance floor
(`MIN_RELEVANCE_SCORE`) that filters noise without silently dropping
sources — everything below the floor is still counted in the logs, just
excluded from the final JSON.

---

## Project structure (this phase)

```
deal_research_engine/
    __init__.py
    config.py                 # env-driven settings (MOCK_MODE, limits, keys)
    models.py                  # Pydantic models: SearchResult, Source, etc.
    query_generator.py         # multi-angle query generation
    search/
        __init__.py
        base.py                 # SearchProvider abstract interface
        provider.py              # SerperSearchProvider + MockSearchProvider
        mock_data.json            # canned results for MOCK_MODE
    sources/
        __init__.py
        collector.py             # orchestrates the whole Phase 1 pipeline
        deduplicator.py           # exact-URL dedup + syndication flagging
        classifier.py             # Tier 1-4 classification
        relevance.py               # transparent relevance scoring
    utils/
        __init__.py
        logging.py                 # no-secrets-logged logger
        url_utils.py                 # URL normalization
    tests/
        test_url_utils.py
        test_deduplication.py
        test_classification.py
        test_models.py
    scripts/
        run_research.py               # CLI entry point
    outputs/                            # JSON results land here (git-ignored)
    .env.example
    .gitignore
    requirements.txt
    README.md
```

`extraction/`, `validation/`, `storage/`, and `llm/` (from the full spec)
are intentionally not created yet — they belong to later milestones.

---

## Setup (Windows)

Open **Command Prompt** or **PowerShell** in the folder where you unzipped
the project (the folder that contains `deal_research_engine/`).

```bat
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r deal_research_engine\requirements.txt
copy deal_research_engine\.env.example deal_research_engine\.env
```

You now have a `.env` file inside `deal_research_engine\`. Leave
`MOCK_MODE=true` for now — you don't need any API key to test this phase.

---

## Run it (MOCK_MODE — no API key needed)

From the folder that contains `deal_research_engine\` (one level above it):

```bat
python deal_research_engine\scripts\run_research.py "Google Wiz acquisition"
```

**Expected output:** a `====` banner, the query, a count of sources
discovered / after dedup / relevant, a per-tier breakdown, and a ranked
list of the top sources with their relevance score, tier, and any
`[PRIMARY]` / `[SYNDICATED?]` flags. The full structured result is also
saved to `deal_research_engine\outputs\google_wiz_acquisition.json`.

Try it with a different subject too — the mock dataset has one real
matched case ("google wiz") and falls back to a generic placeholder result
for anything else, so the *pipeline* still runs end-to-end, it just won't
have realistic mock content for other deals until you add more entries to
`search/mock_data.json` or switch off mock mode.

---

## Run the tests

```bat
cd deal_research_engine
pytest
```

Expected: all tests pass, no network calls are made (classification and
dedup tests use plain Python objects; nothing here hits Serper).

---

## Switching off MOCK_MODE (real search)

1. Get a free API key from https://serper.dev.
2. Edit `deal_research_engine\.env`:
   ```
   MOCK_MODE=false
   SEARCH_API_KEY=your-real-key-here
   ```
3. Run the same command as above. `CLAUDE_API_KEY` is **not** needed yet —
   nothing in this phase calls Claude; that's part of the extraction
   milestone.

---

## What's required from you before Phase 2

Nothing — this milestone should just work with `MOCK_MODE=true`. Once
you've confirmed the output looks right (and, if you want, tried it with a
real Serper key), let me know and I'll build the next milestone: content
retrieval + LLM-based deal extraction with field-level evidence.
