"""
Application configuration.

All configuration is loaded from environment variables (via a local .env
file during development). Nothing sensitive is ever hardcoded here.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings, populated from environment/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General app metadata
    app_name: str = Field(default="Autonomous Multi-Agent Research System")
    environment: str = Field(default="development")

    # OpenAI / Agents SDK configuration
    openai_api_key: str = Field(default="")
    planner_model: str = Field(default="gpt-4o-mini")

    # Planner-specific limits
    max_topic_length: int = Field(default=300)
    min_topic_length: int = Field(default=3)

    # Web Researcher / search provider configuration
    tavily_api_key: str = Field(default="")
    web_search_max_results: int = Field(default=5)
    web_search_timeout_seconds: float = Field(default=15.0)

    # Logging
    log_level: str = Field(default="INFO")

    def config_warnings(self) -> List[str]:
        """
        Return a list of human-readable warnings about the current
        configuration (e.g. missing API key). Used by /health and can be
        surfaced elsewhere without raising hard errors at import time.
        """
        warnings: List[str] = []
        if not self.openai_api_key:
            warnings.append(
                "OPENAI_API_KEY is not set. The Planner Agent will not be "
                "able to call the OpenAI API until this is configured in .env."
            )
        if not self.tavily_api_key:
            warnings.append(
                "TAVILY_API_KEY is not set. The Web Researcher Agent will not "
                "be able to search the web until this is configured in .env."
            )
        return warnings


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton for the process)."""
    return Settings()
