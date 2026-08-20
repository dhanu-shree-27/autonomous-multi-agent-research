"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.research import router as research_router
from app.config import get_settings
from app.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Autonomous Multi-Agent Research & Report Generator. "
        "Phase 1: service health. Phase 2: Planner Agent. "
        "Phase 3: Web Researcher Agent."
    ),
    version="0.3.0",
)

app.include_router(health_router)
app.include_router(research_router)

for warning in settings.config_warnings():
    logger.warning(warning)

logger.info(
    "Application '%s' starting in '%s' environment.",
    settings.app_name,
    settings.environment,
)
