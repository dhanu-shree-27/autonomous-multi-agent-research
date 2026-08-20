"""
Shared pytest fixtures.

Sets safe environment variables *before* the app is imported so tests never
depend on a real .env file or a real OpenAI API key.
"""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MAX_TOPIC_LENGTH", "300")
os.environ.setdefault("MIN_TOPIC_LENGTH", "3")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
