"""
Planner Agent.

Responsible for turning a raw research topic/question into a structured
ResearchPlan. This module is intentionally self-contained ("modular") so
that later phases (Web Researcher, Academic Researcher, Fact Checker,
Synthesizer, Report Generator, etc.) can each live in their own module and
be orchestrated independently.

The agent itself never touches FastAPI - it exposes a single async
function, `run_planner`, that the API layer calls.
"""

from __future__ import annotations

from agents import Agent, Runner, set_default_openai_key

from app.config import get_settings
from app.logging_config import get_logger
from app.models.research_plan import ResearchPlan

logger = get_logger(__name__)

PLANNER_INSTRUCTIONS = """\
You are the Planner Agent inside an autonomous multi-agent research system.

Your ONLY job is to take a research topic or question from the user and
produce a structured, high-quality research plan. You do not perform any
research yourself and you do not draft a report - later agents in the
pipeline will do that using the plan you create.

When planning, think like an experienced research lead who needs to brief a
team of researchers. Produce:

- research_questions: 3-6 specific, answerable questions that, together,
  would let a team fully address the topic.
- subtopics: 3-8 distinct themes/angles that decompose the topic.
- research_tasks: concrete, actionable tasks (e.g. "Compare adoption rates
  of X across three countries"), each linked to the subtopic it supports.
- evidence_requirements: the kinds of evidence needed to answer the
  questions credibly (e.g. quantitative statistics, peer-reviewed studies,
  expert commentary, case studies, survey data).
- recommended_source_types: categories of sources to consult (e.g.
  peer-reviewed journals, government/NGO reports, reputable news outlets,
  industry whitepapers, official statistics agencies). Do not invent
  specific URLs or article titles - only source categories.
- priorities: the subtopics/questions ordered from most to least important
  for a team with limited time/resources to tackle first.

Be specific to the given topic - avoid generic, boilerplate answers that
could apply to any subject. Keep each list item concise (one sentence or
short phrase).
"""


def _build_planner_agent() -> Agent:
    """Construct the Planner Agent with structured (Pydantic) output."""
    settings = get_settings()
    return Agent(
        name="PlannerAgent",
        instructions=PLANNER_INSTRUCTIONS,
        model=settings.planner_model,
        output_type=ResearchPlan,
    )


async def run_planner(topic: str) -> ResearchPlan:
    """
    Run the Planner Agent for a given topic and return a validated
    ResearchPlan.

    Raises:
        RuntimeError: if the OpenAI API key is not configured.
        Exception: propagates any error raised by the Agents SDK/OpenAI API
            so the API layer can translate it into an appropriate HTTP
            error response.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.error("Planner Agent invoked without OPENAI_API_KEY configured.")
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in your .env file "
            "before calling the Planner Agent."
        )

    # Ensure the Agents SDK uses the key from our settings (loaded from
    # .env) rather than relying on ambient process environment variables.
    set_default_openai_key(settings.openai_api_key)

    agent = _build_planner_agent()

    logger.info("Running Planner Agent for topic: %r", topic)
    result = await Runner.run(agent, topic)

    plan = result.final_output
    if not isinstance(plan, ResearchPlan):
        # Defensive check: with output_type set, the SDK should always
        # return a validated ResearchPlan, but we guard against drift.
        logger.error("Planner Agent returned unexpected output type: %s", type(plan))
        raise RuntimeError("Planner Agent returned an unexpected output type.")

    logger.info(
        "Planner Agent produced plan with %d research questions, %d subtopics.",
        len(plan.research_questions),
        len(plan.subtopics),
    )
    return plan
