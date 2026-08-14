"""
Pydantic schemas for the Planner Agent's structured output.

These models define the exact shape of a ResearchPlan. The Agents SDK uses
the `ResearchPlan` model as the `output_type` for the Planner Agent, which
forces the underlying LLM call to return data matching this schema.
"""

from typing import List

from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    """A single actionable research task derived from the topic."""

    task: str = Field(description="A concrete, actionable research task.")
    related_subtopic: str = Field(
        description="The subtopic this task primarily supports."
    )


class ResearchPlan(BaseModel):
    """
    Structured research plan produced by the Planner Agent.

    This is intentionally scoped to Phase 2: it describes WHAT should be
    researched and HOW, but does not perform any research itself. Later
    phases (Web Researcher, Academic Researcher, News Agent, Fact Checker,
    Synthesizer, Report Generator, etc.) will consume this plan.
    """

    topic: str = Field(description="The original research topic/question.")

    research_questions: List[str] = Field(
        description="Key questions the research should answer.",
        min_length=1,
    )

    subtopics: List[str] = Field(
        description="Distinct subtopics/themes that break down the main topic.",
        min_length=1,
    )

    research_tasks: List[ResearchTask] = Field(
        description="Concrete research tasks to execute, each tied to a subtopic.",
        min_length=1,
    )

    evidence_requirements: List[str] = Field(
        description=(
            "Types of evidence needed to answer the research questions "
            "credibly (e.g. statistics, case studies, expert opinions)."
        ),
        min_length=1,
    )

    recommended_source_types: List[str] = Field(
        description=(
            "Recommended categories of sources to consult "
            "(e.g. peer-reviewed journals, government reports, news articles)."
        ),
        min_length=1,
    )

    priorities: List[str] = Field(
        description=(
            "Research priorities ordered from most to least important, "
            "guiding which subtopics/tasks should be tackled first."
        ),
        min_length=1,
    )


class ResearchPlanRequest(BaseModel):
    """Request body for POST /research/plan."""

    topic: str = Field(
        description="The research topic or question to plan for.",
    )


class ResearchPlanResponse(BaseModel):
    """Response body for POST /research/plan."""

    plan: ResearchPlan
