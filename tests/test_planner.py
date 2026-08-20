import pytest

from app.models.research_plan import ResearchPlan, ResearchTask


def _fake_plan(topic: str) -> ResearchPlan:
    return ResearchPlan(
        topic=topic,
        research_questions=["What is the current state of X?"],
        subtopics=["Adoption", "Challenges"],
        research_tasks=[
            ResearchTask(task="Survey recent adoption statistics", related_subtopic="Adoption"),
        ],
        evidence_requirements=["Quantitative statistics", "Expert commentary"],
        recommended_source_types=["Peer-reviewed journals", "Government reports"],
        priorities=["Adoption", "Challenges"],
    )


@pytest.fixture()
def mock_planner(monkeypatch):
    """Patch run_planner so tests never call the real OpenAI API."""

    async def _fake_run_planner(topic: str) -> ResearchPlan:
        return _fake_plan(topic)

    monkeypatch.setattr("app.api.research.run_planner", _fake_run_planner)


def test_create_plan_success(client, mock_planner):
    response = client.post(
        "/research/plan",
        json={"topic": "Impact of Generative AI on Education"},
    )
    assert response.status_code == 200

    body = response.json()
    plan = body["plan"]
    assert plan["topic"] == "Impact of Generative AI on Education"
    assert len(plan["research_questions"]) >= 1
    assert len(plan["subtopics"]) >= 1
    assert len(plan["research_tasks"]) >= 1
    assert "task" in plan["research_tasks"][0]
    assert "related_subtopic" in plan["research_tasks"][0]
    assert len(plan["evidence_requirements"]) >= 1
    assert len(plan["recommended_source_types"]) >= 1
    assert len(plan["priorities"]) >= 1


def test_create_plan_strips_whitespace(client, mock_planner):
    response = client.post("/research/plan", json={"topic": "  Climate Policy  "})
    assert response.status_code == 200
    assert response.json()["plan"]["topic"] == "Climate Policy"


def test_rejects_empty_topic(client, mock_planner):
    response = client.post("/research/plan", json={"topic": ""})
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


def test_rejects_whitespace_only_topic(client, mock_planner):
    response = client.post("/research/plan", json={"topic": "   "})
    assert response.status_code == 422


def test_rejects_too_short_topic(client, mock_planner):
    response = client.post("/research/plan", json={"topic": "AI"})
    assert response.status_code == 422
    assert "at least" in response.json()["detail"].lower()


def test_rejects_topic_exceeding_max_length(client, mock_planner):
    long_topic = "A" * 500
    response = client.post("/research/plan", json={"topic": long_topic})
    assert response.status_code == 422
    assert "exceed" in response.json()["detail"].lower()


def test_missing_topic_field_returns_422(client, mock_planner):
    response = client.post("/research/plan", json={})
    assert response.status_code == 422


def test_planner_config_error_returns_503(client, monkeypatch):
    async def _raise_runtime_error(topic: str):
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    monkeypatch.setattr("app.api.research.run_planner", _raise_runtime_error)

    response = client.post("/research/plan", json={"topic": "Quantum Computing"})
    assert response.status_code == 503


def test_planner_unexpected_error_returns_502(client, monkeypatch):
    async def _raise_generic_error(topic: str):
        raise ValueError("simulated upstream failure")

    monkeypatch.setattr("app.api.research.run_planner", _raise_generic_error)

    response = client.post("/research/plan", json={"topic": "Quantum Computing"})
    assert response.status_code == 502
