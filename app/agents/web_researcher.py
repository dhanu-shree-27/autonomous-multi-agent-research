"""
Web Researcher Agent.

Responsible for taking a single research task (optionally with an explicit
search query) and gathering structured, sourced information about it from
the web. This module is intentionally self-contained ("modular"), mirroring
`app.agents.planner_agent`, so that:

- it can be exercised on its own via `POST /research/web-search`, and
- it can later be looped over every `ResearchTask` in a `ResearchPlan`
  (Phase 2's output) without either module needing to change.

Unlike the Planner Agent, the Web Researcher does not need an LLM call to
do its core job - "search the web and return structured sources" is a tool
call, not a text-generation task. It therefore talks directly to the search
tool/service (`app.services.web_search_service`) and maps the results into
Pydantic models. Keeping it as a plain async function (rather than forcing
it through the OpenAI Agents SDK) keeps it fast, cheap, and testable without
network access or an API key - while still fitting into the same
agent-per-module architecture as the rest of the pipeline.
"""

from __future__ import annotations

from typing import Optional

from app.logging_config import get_logger
from app.models.research_result import (
    SourceMetadata,
    WebResearchResult,
    WebSearchResultItem,
)
from app.services.web_search_service import (
    WebSearchConfigError,
    WebSearchError,
    search_web,
)

logger = get_logger(__name__)


def _build_query(task: str, query: Optional[str]) -> str:
    """Derive the search query to use for a given task."""
    if query and query.strip():
        return query.strip()
    return task.strip()


def _to_result_item(task: str, query: str, raw: dict) -> WebSearchResultItem:
    """Map one raw provider search hit into a structured WebSearchResultItem."""
    url = str(raw.get("url", "")).strip()
    domain = None
    if url:
        # Best-effort domain extraction without pulling in a URL-parsing
        # dependency just for this - good enough for display/metadata.
        domain = url.split("//")[-1].split("/")[0] or None

    metadata = SourceMetadata(
        domain=domain,
        published_date=raw.get("published_date"),
        relevance_score=raw.get("score"),
        raw={
            k: v
            for k, v in raw.items()
            if k not in {"title", "url", "content", "score", "published_date"}
        },
    )

    return WebSearchResultItem(
        task=task,
        query=query,
        source_title=str(raw.get("title", "") or "Untitled source"),
        source_url=url,
        content=str(raw.get("content", "") or ""),
        metadata=metadata,
    )


async def run_web_researcher(
    task: str,
    query: Optional[str] = None,
    max_results: Optional[int] = None,
) -> WebResearchResult:
    """
    Run the Web Researcher Agent for a single research task and return a
    structured, validated WebResearchResult.

    This function is designed to degrade gracefully: if the search
    provider call fails (network error, timeout, bad response, etc.), the
    failure is caught here and returned as a `WebResearchResult` with
    `success=False` and a populated `error` field rather than propagating
    an exception - so that iterating over many tasks later (e.g. every task
    in a ResearchPlan) can continue past individual failures.

    Raises:
        WebSearchConfigError: only for configuration problems (e.g. missing
            API key), since that affects every task and should be
            surfaced/handled once by the caller (the API layer maps this to
            a 503), rather than silently degrading every single result.
    """
    effective_query = _build_query(task, query)
    logger.info("Running Web Researcher for task: %r (query: %r)", task, effective_query)

    try:
        raw_results = await search_web(effective_query, max_results=max_results)
    except WebSearchConfigError:
        # Let the caller (API layer) handle configuration errors explicitly -
        # every call will fail identically until the API key is set, so
        # there's no value in "gracefully" swallowing this one.
        raise
    except WebSearchError as exc:
        logger.warning(
            "Web Researcher degraded gracefully for task %r: %s", task, exc
        )
        return WebResearchResult(
            task=task,
            query=effective_query,
            results=[],
            success=False,
            error=str(exc),
        )

    items = [_to_result_item(task, effective_query, raw) for raw in raw_results]

    logger.info(
        "Web Researcher produced %d structured result(s) for task: %r", len(items), task
    )
    return WebResearchResult(
        task=task,
        query=effective_query,
        results=items,
        success=True,
        error=None,
    )
