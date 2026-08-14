"""
Research planning endpoint (Phase 2).

Exposes POST /research/plan, which delegates to the Planner Agent to turn a
raw topic into a structured ResearchPlan.
"""

from fastapi import APIRouter, HTTPException, status

from app.agents.planner_agent import run_planner
from app.config import get_settings
from app.logging_config import get_logger
from app.models.research_plan import ResearchPlanRequest, ResearchPlanResponse

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
