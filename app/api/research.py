"""
Research endpoints.

Phase 2: POST /research/plan, which delegates to the Planner Agent to turn
a raw topic into a structured ResearchPlan.

Phase 3: POST /research/web-search, which delegates to the Web Researcher
Agent to turn a single research task into structured, sourced web results.
Kept in this same router/file (both under the `/research` prefix) so the
two agents' HTTP surface stays in one place; the agents themselves remain
in separate modules under `app/agents/`.
"""

from fastapi import APIRouter, HTTPException, status

from app.agents.planner_agent import run_planner
from app.agents.web_researcher import run_web_researcher
from app.config import get_settings
from app.logging_config import get_logger
from app.models.research_plan import ResearchPlanRequest, ResearchPlanResponse
from app.models.research_result import WebResearchRequest, WebResearchResponse
from app.services.web_search_service import WebSearchConfigError

logger = get_logger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


@router.post(
    "/plan",
    response_model=ResearchPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a structured research plan for a topic",
)
async def create_research_plan(payload: ResearchPlanRequest) -> ResearchPlanResponse:
    """
    Generate a structured ResearchPlan for the given topic using the
    Planner Agent.
    """
    settings = get_settings()
    topic = payload.topic.strip()

    # --- Validation -------------------------------------------------
    if not topic:
        logger.warning("Rejected /research/plan request: empty topic.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The 'topic' field must not be empty or whitespace-only.",
        )

    if len(topic) < settings.min_topic_length:
        logger.warning("Rejected /research/plan request: topic too short.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"The 'topic' field must be at least "
                f"{settings.min_topic_length} characters long."
            ),
        )

    if len(topic) > settings.max_topic_length:
        logger.warning("Rejected /research/plan request: topic too long.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"The 'topic' field must not exceed "
                f"{settings.max_topic_length} characters "
                f"(received {len(topic)})."
            ),
        )

    # --- Execution ----------------------------------------------------
    try:
        plan = await run_planner(topic)
    except RuntimeError as exc:
        # Configuration problems (e.g. missing API key) -> service unavailable.
        logger.error("Planner configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001 - translate any SDK/API error
        logger.exception("Planner Agent failed to generate a research plan.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "The Planner Agent failed to generate a research plan. "
                f"Reason: {exc}"
            ),
        ) from exc

    return ResearchPlanResponse(plan=plan)


@router.post(
    "/web-search",
    response_model=WebResearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the Web Researcher Agent on a single research task",
)
async def run_web_search(payload: WebResearchRequest) -> WebResearchResponse:
    """
    Run the Web Researcher Agent for a single research task, independent of
    the Planner Agent. Useful for testing/exercising the Web Researcher on
    its own before it is wired up to consume a full ResearchPlan.
    """
    task = payload.task.strip()

    # --- Validation -------------------------------------------------
    if not task:
        logger.warning("Rejected /research/web-search request: empty task.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The 'task' field must not be empty or whitespace-only.",
        )

    query = payload.query.strip() if payload.query else None
    if payload.query is not None and not query:
        logger.warning("Rejected /research/web-search request: whitespace-only query.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The 'query' field, if provided, must not be empty or whitespace-only.",
        )

    # --- Execution ----------------------------------------------------
    try:
        result = await run_web_researcher(
            task=task, query=query, max_results=payload.max_results
        )
    except WebSearchConfigError as exc:
        # Configuration problems (e.g. missing API key) -> service unavailable.
        logger.error("Web Researcher configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001 - translate any unexpected error
        logger.exception("Web Researcher Agent failed unexpectedly.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The Web Researcher Agent failed unexpectedly. Reason: {exc}",
        ) from exc

    return WebResearchResponse(result=result)
