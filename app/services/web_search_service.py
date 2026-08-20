"""
Web search tool/service.

This module is the ONLY place that talks to the external search provider
(Tavily). It is deliberately kept separate from `app.agents.web_researcher`
so the HTTP/provider-specific details (endpoint, auth, response shape) stay
isolated and swappable - if the project ever switches search providers,
only this file should need to change.

Tavily was chosen because it is purpose-built for LLM/agentic research
workflows (returns clean, pre-extracted page content rather than raw HTML),
but nothing outside this module depends on that choice.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class WebSearchConfigError(RuntimeError):
    """Raised when the search provider is not configured (e.g. no API key)."""


class WebSearchError(RuntimeError):
    """Raised when the search provider call fails (network, HTTP, parsing)."""


async def search_web(query: str, max_results: int | None = None) -> List[Dict[str, Any]]:
    """
    Run a web search for `query` and return a list of raw result dicts as
    provided by the search API, e.g.:

        [
            {
                "title": "...",
                "url": "...",
                "content": "...",
                "score": 0.87,
                "published_date": "2024-05-01",
            },
            ...
        ]

    Raises:
        WebSearchConfigError: if the search provider API key is not set.
        WebSearchError: if the HTTP call fails, times out, or returns a
            response that cannot be parsed as expected.
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        logger.error("Web search invoked without TAVILY_API_KEY configured.")
        raise WebSearchConfigError(
            "TAVILY_API_KEY is not configured. Set it in your .env file "
            "before calling the Web Researcher Agent."
        )

    effective_max_results = max_results or settings.web_search_max_results

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "max_results": effective_max_results,
        "search_depth": "basic",
        "include_answer": False,
    }

    logger.info("Web search: query=%r max_results=%d", query, effective_max_results)

    try:
        async with httpx.AsyncClient(timeout=settings.web_search_timeout_seconds) as client:
            response = await client.post(TAVILY_SEARCH_URL, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        logger.error("Web search timed out for query %r: %s", query, exc)
        raise WebSearchError(f"Search request timed out for query: {query!r}") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Web search API returned an error for query %r: %s", query, exc
        )
        raise WebSearchError(
            f"Search provider returned HTTP {exc.response.status_code} for "
            f"query {query!r}."
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Web search network error for query %r: %s", query, exc)
        raise WebSearchError(f"Network error while searching for {query!r}: {exc}") from exc
    except ValueError as exc:  # JSON decoding failure
        logger.error("Web search returned unparseable JSON for query %r: %s", query, exc)
        raise WebSearchError(f"Search provider returned an invalid response: {exc}") from exc

    results = data.get("results")
    if not isinstance(results, list):
        logger.error("Web search response missing 'results' list for query %r.", query)
        raise WebSearchError(
            "Search provider response did not contain the expected 'results' list."
        )

    logger.info("Web search returned %d result(s) for query %r.", len(results), query)
    return results
