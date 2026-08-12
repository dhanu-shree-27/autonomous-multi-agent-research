"""
Health-check endpoint.

Purpose: a simple, dependency-free way to confirm the server is running
and the configuration loaded correctly. This is the first thing you test
after starting the server, and the first thing a deployment platform
would call to check the app is alive.
"""

import logging

from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["System"])
def health_check() -> dict:
    """
    Returns basic status information about the running application.

    Deliberately does NOT call OpenAI or any external service — a health
    check should be fast and only confirm that the app itself is up.
    Configuration problems (like a missing API key) are reported here as
    a warning, not a failure, so you can still start the server and see
    the problem clearly, then fix your .env file.
    """
    config_problems = settings.validate()

    logger.info("Health check requested. Config problems: %s", config_problems or "none")

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "config_warnings": config_problems,
    }
