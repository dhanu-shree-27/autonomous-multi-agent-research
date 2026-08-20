import pytest

from app.agents.web_researcher import run_web_researcher
from app.services.web_search_service import WebSearchConfigError, WebSearchError

RAW_RESULTS = [
    {
        "title": "Generative AI in K-12 Classrooms",
        "url": "https://example.edu/genai-k12",
        "content": "A summary of how generative AI tools are used in schools today.",
        "score": 0.91,
        "published_date": "2025-03-10",
    },
    {
        "title": "AI Tutoring Tools: A Review",
        "url": "https://research.example.org/ai-tutoring",
        "content": "An overview of AI tutoring adoption and outcomes.",
        "score": 0.77,
    },
]


# ---------------------------------------------------------------------------
# Unit tests for the Web Researcher Agent (no HTTP, no FastAPI)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_web_researcher_success(monkeypatch):
    async def _fake_search_web(query, max_results=None):
        assert query == "AI tutoring tools in schools"
        return RAW_RESULTS

    monkeypatch.setattr(
        "app.agents.web_researcher.search_web", _fake_search_web
    )

    result = await run_web_researcher(
        task="Collect case studies of AI tutoring tools in K-12 settings",
        query="AI tutoring tools in schools",
    )

    assert result.success is True
    assert result.error is None
    assert result.query == "AI tutoring tools in schools"
    assert len(result.results) == 2

    first = result.results[0]
    assert first.task == "Collect case studies of AI tutoring tools in K-12 settings"
    assert first.source_title == "Generative AI in K-12 Classrooms"
    assert first.source_url == "https://example.edu/genai-k12"
    assert "generative AI tools" in first.content
    assert first.metadata.domain == "example.edu"
    assert first.metadata.published_date == "2025-03-10"
    assert first.metadata.relevance_score == 0.91

    second = result.results[1]
    assert second.metadata.published_date is None
    assert second.metadata.relevance_score == 0.77


@pytest.mark.asyncio
async def test_run_web_researcher_derives_query_from_task(monkeypatch):
    captured = {}

    async def _fake_search_web(query, max_results=None):
        captured["query"] = query
        return []

    monkeypatch.setattr(
        "app.agents.web_researcher.search_web", _fake_search_web
    )

    result = await run_web_researcher(task="Impact of remote work on productivity")

    assert captured["query"] == "Impact of remote work on productivity"
    assert result.query == "Impact of remote work on productivity"
    assert result.results == []
    assert result.success is True


@pytest.mark.asyncio
async def test_run_web_researcher_degrades_gracefully_on_search_error(monkeypatch):
    async def _fake_search_web(query, max_results=None):
        raise WebSearchError("Network error while searching for 'x'")

    monkeypatch.setattr(
        "app.agents.web_researcher.search_web", _fake_search_web
    )

    result = await run_web_researcher(task="Some task", query="x")

    assert result.success is False
    assert result.results == []
    assert "Network error" in result.error


@pytest.mark.asyncio
async def test_run_web_researcher_propagates_config_error(monkeypatch):
    async def _fake_search_web(query, max_results=None):
        raise WebSearchConfigError("TAVILY_API_KEY is not configured.")

    monkeypatch.setattr(
        "app.agents.web_researcher.search_web", _fake_search_web
    )

    with pytest.raises(WebSearchConfigError):
        await run_web_researcher(task="Some task")


# ---------------------------------------------------------------------------
# API tests for POST /research/web-search
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_web_researcher(monkeypatch):
    """Patch run_web_researcher so tests never call the real search API."""

    async def _fake_run_web_researcher(task, query=None, max_results=None):
        from app.models.research_result import WebResearchResult, WebSearchResultItem

        return WebResearchResult(
            task=task,
            query=query or task,
            results=[
                WebSearchResultItem(
                    task=task,
                    query=query or task,
                    source_title="Example Source",
                    source_url="https://example.com/article",
                    content="Relevant extracted content about the task.",
                )
            ],
            success=True,
            error=None,
        )

    monkeypatch.setattr(
        "app.api.research.run_web_researcher", _fake_run_web_researcher
    )


def test_web_search_endpoint_success(client, mock_web_researcher):
    response = client.post(
        "/research/web-search",
        json={"task": "Survey recent adoption statistics for generative AI"},
    )
    assert response.status_code == 200

    body = response.json()["result"]
    assert body["task"] == "Survey recent adoption statistics for generative AI"
    assert body["success"] is True
    assert len(body["results"]) == 1

    item = body["results"][0]
    assert item["source_title"] == "Example Source"
    assert item["source_url"] == "https://example.com/article"
    assert "content" in item
    assert "metadata" in item


def test_web_search_endpoint_uses_explicit_query(client, mock_web_researcher):
    response = client.post(
        "/research/web-search",
        json={"task": "Adoption of AI in schools", "query": "AI adoption K-12 statistics"},
    )
    assert response.status_code == 200
    assert response.json()["result"]["query"] == "AI adoption K-12 statistics"


def test_web_search_endpoint_rejects_empty_task(client, mock_web_researcher):
    response = client.post("/research/web-search", json={"task": ""})
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


def test_web_search_endpoint_rejects_whitespace_only_task(client, mock_web_researcher):
    response = client.post("/research/web-search", json={"task": "   "})
    assert response.status_code == 422


def test_web_search_endpoint_rejects_whitespace_only_query(client, mock_web_researcher):
    response = client.post(
        "/research/web-search", json={"task": "Some task", "query": "   "}
    )
    assert response.status_code == 422


def test_web_search_endpoint_missing_task_field_returns_422(client, mock_web_researcher):
    response = client.post("/research/web-search", json={})
    assert response.status_code == 422


def test_web_search_endpoint_returns_degraded_result_on_search_failure(client, monkeypatch):
    """
    A search-provider failure should NOT crash the endpoint - it should be
    surfaced as a 200 response with success=False (graceful degradation),
    matching the behavior of the underlying agent function.
    """
    from app.models.research_result import WebResearchResult

    async def _fake_degraded(task, query=None, max_results=None):
        return WebResearchResult(
            task=task,
            query=query or task,
            results=[],
            success=False,
            error="Network error while searching.",
        )

    monkeypatch.setattr("app.api.research.run_web_researcher", _fake_degraded)

    response = client.post("/research/web-search", json={"task": "Some task"})
    assert response.status_code == 200
    body = response.json()["result"]
    assert body["success"] is False
    assert body["results"] == []
    assert "Network error" in body["error"]


def test_web_search_endpoint_config_error_returns_503(client, monkeypatch):
    from app.services.web_search_service import WebSearchConfigError

    async def _raise_config_error(task, query=None, max_results=None):
        raise WebSearchConfigError("TAVILY_API_KEY is not configured.")

    monkeypatch.setattr("app.api.research.run_web_researcher", _raise_config_error)

    response = client.post("/research/web-search", json={"task": "Some task"})
    assert response.status_code == 503


def test_web_search_endpoint_unexpected_error_returns_502(client, monkeypatch):
    async def _raise_generic_error(task, query=None, max_results=None):
        raise ValueError("simulated unexpected failure")

    monkeypatch.setattr("app.api.research.run_web_researcher", _raise_generic_error)

    response = client.post("/research/web-search", json={"task": "Some task"})
    assert response.status_code == 502
