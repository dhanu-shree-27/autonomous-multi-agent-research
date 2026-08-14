"""
Health check endpoint (Phase 1).

Kept as-is in Phase 2 so existing behavior/tests continue to pass.
"""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return basic service health/status information."""
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "config_warnings": settings.config_warnings(),
    }
