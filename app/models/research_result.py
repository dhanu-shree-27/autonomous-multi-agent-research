"""
Pydantic schemas for the Web Researcher Agent's structured output.

These models define the exact shape of a single web search "hit" as well
as the overall result of running the Web Researcher on one research task.
They are intentionally decoupled from `app.models.research_plan` so the
Web Researcher can be exercised on its own (Phase 3), then later be wired
up to consume a `ResearchTask` produced by the Planner Agent (Phase 2)
without requiring changes to either model.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    """Optional metadata about a web source, when the provider supplies it."""

    domain: Optional[str] = Field(
        default=None, description="Domain the source was published on, e.g. 'nytimes.com'."
    )
    published_date: Optional[str] = Field(
        default=None, description="Publication date of the source, if known."
    )
    relevance_score: Optional[float] = Field(
        default=None,
        description="Provider-assigned relevance/similarity score for this result, if any.",
    )
    raw: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Any additional provider-specific fields that don't map to a "
            "named field above, kept as-is for forward compatibility."
        ),
    )


class WebSearchResultItem(BaseModel):
    """A single search result ('source') returned for a research task."""

    task: str = Field(description="The research task this result was gathered for.")
    query: str = Field(description="The exact search query used to find this source.")
    source_title: str = Field(description="Title of the source page/article.")
    source_url: str = Field(description="URL of the source page/article.")
    content: str = Field(
        description="Extracted or relevant content/summary snippet from the source."
    )
    metadata: SourceMetadata = Field(
        default_factory=SourceMetadata,
        description="Source metadata where available (domain, date, score, etc.).",
    )


class WebResearchResult(BaseModel):
    """
    Structured output of running the Web Researcher Agent on a single
    research task. Kept separate from a "batch" wrapper so this same model
    can represent one task's results whether it was requested directly via
    the API or produced internally while iterating over a full
    `ResearchPlan` in a later phase.
    """

    task: str = Field(description="The research task that was investigated.")
    query: str = Field(description="The search query actually used.")
    results: List[WebSearchResultItem] = Field(
        default_factory=list,
        description="Structured search results found for this task.",
    )
    success: bool = Field(
        description="Whether the web search completed successfully (even if 0 results)."
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error message if the search failed or degraded.",
    )


class WebResearchRequest(BaseModel):
    """Request body for POST /research/web-search."""

    task: str = Field(description="The research task to investigate, in plain language.")
    query: Optional[str] = Field(
        default=None,
        description=(
            "Optional explicit search query to use instead of deriving one "
            "from `task`. Useful once the Planner Agent supplies tasks that "
            "need query refinement."
        ),
    )
    max_results: Optional[int] = Field(
        default=None,
        description="Optional override for the number of results to return.",
        ge=1,
        le=20,
    )


class WebResearchResponse(BaseModel):
    """Response body for POST /research/web-search."""

    result: WebResearchResult
