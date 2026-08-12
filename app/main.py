"""
Application entry point.

This file is responsible ONLY for creating and configuring the FastAPI
app object — wiring together settings, logging, routers, and error
handlers. It should never contain business logic (that will live in
app/agents/ from Phase 2 onward) or route logic (that lives in app/api/).

Run with:
    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import health
from app.core.config import settings
from app.core.logging_config import setup_logging

# Logging must be configured before anything else logs a message.
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup (before the yield) and once at shutdown (after).
    This is the modern replacement for the deprecated @app.on_event("startup").
    """
    problems = settings.validate()
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
    if problems:
        for problem in problems:
            logger.warning("Config warning: %s", problem)
    else:
        logger.info("Configuration validated successfully.")

    yield  # app runs here

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory — makes the app easy to import and test."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Backend for the Autonomous Multi-Agent Research & Report "
            "Generator. Phase 1: project setup and health check only."
        ),
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Register routers. From Phase 2 onward, a `research` router will be
    # added here (e.g. app.include_router(research.router)) to expose the
    # actual research workflow as an endpoint.
    app.include_router(health.router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catches any exception not already handled elsewhere, logs it with
        a full stack trace, and returns a clean JSON error instead of
        letting the server crash or leak a raw traceback to the client.
        """
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error. Check server logs for details."},
        )

    return app


app = create_app()
