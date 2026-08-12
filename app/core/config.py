"""
Application configuration.

This is the ONLY place in the codebase that should read environment
variables directly. Every other module should import `settings` from
here instead of calling os.getenv() itself — that way, if you ever
change how a setting is loaded, you only change it in one place.

The OpenAI API key is never hardcoded. It is read from the environment
(populated from the local `.env` file via python-dotenv), and if it's
missing, the app fails fast with a clear error instead of silently
running with no key and failing confusingly later.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load variables from a local .env file into the process environment.
# In production/deployment, real environment variables would be set
# directly and this call would simply find no .env file and do nothing.
load_dotenv()


class Settings:
    """Holds all configuration values used across the application."""

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "Autonomous Multi-Agent Research System")
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # OpenAI configuration — required for later phases (agents), but we
        # validate it now so setup problems are caught in Phase 1, not Phase 2.
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    def validate(self) -> list[str]:
        """
        Returns a list of human-readable problems with the current config.
        An empty list means the config is valid.
        Called at startup so missing configuration is reported clearly,
        not discovered later as a confusing runtime error.
        """
        problems = []
        if not self.openai_api_key:
            problems.append(
                "OPENAI_API_KEY is not set. Add it to your .env file "
                "(see .env.example). Agents in Phase 2+ will not work without it."
            )
        return problems


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance — ensures the .env file is only read once
    and the same Settings object is reused across the app.
    """
    return Settings()


settings = get_settings()
