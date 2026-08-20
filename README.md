# Autonomous Multi-Agent Research & Report Generator

A multi-phase system that will eventually take a research topic, plan it,
research it across multiple agent types, fact-check it, and synthesize it
into a report. This repository currently implements **Phase 1** (service
health), **Phase 2** (Planner Agent), and **Phase 3** (Web Researcher
Agent).

## Status

| Phase | Description                          | Status      |
|-------|---------------------------------------|-------------|
| 1     | App skeleton + `/health`              | ✅ Complete |
| 2     | Planner Agent + `/research/plan`      | ✅ Complete |
| 3     | Web Researcher Agent + `/research/web-search` | ✅ Complete |
| 4+    | Academic Researcher, News Agent, Fact Checker, Synthesizer, Report Generator, Oracle AI DB, Vector Search, MCP, ReAct, Human Approval | ⏳ Not started |

See `PHASE_LOG.md` for a detailed history of what was built in each phase.

## Project structure

```
research_system/
├── app/
│   ├── main.py                 # FastAPI app + router registration
│   ├── config.py               # Env-based settings (pydantic-settings)
│   ├── logging_config.py       # Centralized logging setup
│   ├── models/
│   │   ├── research_plan.py    # ResearchPlan / request / response schemas
│   │   └── research_result.py  # WebResearchResult / request / response schemas
│   ├── agents/
│   │   ├── planner_agent.py    # Planner Agent (OpenAI Agents SDK)
│   │   └── web_researcher.py   # Web Researcher Agent
│   ├── services/
│   │   └── web_search_service.py  # Search provider tool (Tavily API client)
│   └── api/
│       ├── health.py           # GET /health
│       └── research.py         # POST /research/plan, POST /research/web-search
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_planner.py
│   ├── test_web_researcher.py
│   └── test_web_search_service.py
├── .env.example                # Template for local .env (never commit .env)
├── requirements.txt
├── README.md
└── PHASE_LOG.md
```

## Prerequisites

- Python 3.11+
- An OpenAI API key with access to the model configured in `PLANNER_MODEL`
  (default `gpt-4o-mini`) — required for `/research/plan`.
- A [Tavily](https://tavily.com/) API key — required for `/research/web-search`.
  Tavily was chosen because it's purpose-built for LLM/agentic search (it
  returns clean, pre-extracted page content rather than raw HTML), but the
  provider is isolated to a single module (`app/services/web_search_service.py`)
  and can be swapped out later without touching the agent or API layers.

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env and set OPENAI_API_KEY and TAVILY_API_KEY to your real keys
```

API keys are **never** hardcoded anywhere in the codebase. They are read
exclusively from the environment (via `.env` in local development, or real
environment variables in production/CI). `.env` is git-ignored.

## Running the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

- Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Endpoints

### `GET /health`

Returns basic service status.

```json
{
  "status": "ok",
  "app_name": "Autonomous Multi-Agent Research System",
  "environment": "development",
  "config_warnings": []
}
```

`config_warnings` will list issues such as a missing `OPENAI_API_KEY` or
`TAVILY_API_KEY` — the server still starts, but the corresponding agent's
calls will fail until the relevant key is set.

### `POST /research/plan`

Generates a structured research plan for a topic using the Planner Agent.

**Request**

```json
{
  "topic": "Impact of Generative AI on Education"
}
```

**Response** (`200 OK`)

```json
{
  "plan": {
    "topic": "Impact of Generative AI on Education",
    "research_questions": [
      "How is generative AI currently being used in classrooms?",
      "What effects does generative AI have on student learning outcomes?"
    ],
    "subtopics": [
      "Personalized learning",
      "Academic integrity",
      "Teacher workload"
    ],
    "research_tasks": [
      {
        "task": "Collect case studies of AI tutoring tools in K-12 settings",
        "related_subtopic": "Personalized learning"
      }
    ],
    "evidence_requirements": [
      "Peer-reviewed studies on learning outcomes",
      "Survey data from educators and students"
    ],
    "recommended_source_types": [
      "Peer-reviewed education journals",
      "Government/education-ministry reports"
    ],
    "priorities": [
      "Academic integrity",
      "Personalized learning",
      "Teacher workload"
    ]
  }
}
```

**Validation errors** (`422 Unprocessable Entity`)

- Empty or whitespace-only `topic`
- `topic` shorter than `MIN_TOPIC_LENGTH` (default 3 characters)
- `topic` longer than `MAX_TOPIC_LENGTH` (default 300 characters)

**Server-side errors**

- `503 Service Unavailable` — `OPENAI_API_KEY` is not configured.
- `502 Bad Gateway` — the Planner Agent / OpenAI API call failed for any
  other reason (network issue, rate limit, model error, etc.). The response
  `detail` includes the underlying error message.

### `POST /research/web-search`

Runs the **Web Researcher Agent** on a single research task, independent of
the Planner Agent — useful for testing/exercising it on its own. It derives
a search query from `task` (or uses an explicit `query` if provided),
searches the web, and returns structured, sourced results.

**Request**

```json
{
  "task": "Collect case studies of AI tutoring tools in K-12 settings",
  "query": "AI tutoring tools K-12 case studies",
  "max_results": 5
}
```

`query` and `max_results` are both optional — if `query` is omitted, the
`task` text itself is used as the search query.

**Response** (`200 OK`)

```json
{
  "result": {
    "task": "Collect case studies of AI tutoring tools in K-12 settings",
    "query": "AI tutoring tools K-12 case studies",
    "results": [
      {
        "task": "Collect case studies of AI tutoring tools in K-12 settings",
        "query": "AI tutoring tools K-12 case studies",
        "source_title": "Generative AI in K-12 Classrooms",
        "source_url": "https://example.edu/genai-k12",
        "content": "A summary of how generative AI tools are used in schools today.",
        "metadata": {
          "domain": "example.edu",
          "published_date": "2025-03-10",
          "relevance_score": 0.91,
          "raw": {}
        }
      }
    ],
    "success": true,
    "error": null
  }
}
```

**Graceful degradation:** if the search provider call itself fails
(timeout, network error, non-2xx response, unparseable response), the
endpoint still returns `200 OK` with `success: false`, an empty `results`
list, and a human-readable `error` message — a single failed search should
not crash the caller, especially once this agent is looped over every task
in a `ResearchPlan` in a later phase.

**Validation errors** (`422 Unprocessable Entity`)

- Empty or whitespace-only `task`
- Whitespace-only `query` (if provided at all)
- Missing `task` field

**Server-side errors**

- `503 Service Unavailable` — `TAVILY_API_KEY` is not configured. Unlike a
  single search failing, this affects every request identically, so it is
  surfaced explicitly rather than degraded.
- `502 Bad Gateway` — the Web Researcher Agent failed for an unexpected
  reason outside normal search-failure handling.

## Testing the endpoints via `/docs`

1. Start the server: `uvicorn app.main:app --reload`
2. Open `http://127.0.0.1:8000/docs` in a browser.
3. Expand `POST /research/plan`, click **Try it out**.
4. Enter a request body, e.g.:
   ```json
   { "topic": "Impact of Generative AI on Education" }
   ```
5. Click **Execute** and inspect the response body/status code below.
6. Do the same for `POST /research/web-search`, e.g.:
   ```json
   { "task": "Collect case studies of AI tutoring tools in K-12 settings" }
   ```

## Running tests

```bash
pytest -v
```

Tests mock the Planner Agent (`app.api.research.run_planner`), the Web
Researcher Agent (`app.api.research.run_web_researcher`), and the search
service's HTTP calls, so the full suite runs **without** a real OpenAI API
key, Tavily API key, or network access, and covers:

- `GET /health` returns `200` with the expected shape.
- `POST /research/plan` returns a well-formed `ResearchPlan` on success.
- Topic whitespace is trimmed.
- Empty, whitespace-only, too-short, too-long, and missing `topic` all
  return `422` with a descriptive `detail` message.
- A missing/invalid OpenAI configuration returns `503`.
- An unexpected Planner Agent failure returns `502`.
- `run_web_researcher` maps raw search results into structured
  `WebSearchResultItem`s, derives a query from `task` when none is given,
  degrades gracefully (`success=False` + `error`) on search failures
  instead of raising, and propagates configuration errors.
- The low-level `search_web` tool raises on missing API key, HTTP errors,
  timeouts, and malformed provider responses.
- `POST /research/web-search` returns structured results on success, `422`
  on invalid input, `200` with `success: false` on a degraded/failed
  search, `503` on missing Tavily configuration, and `502` on an
  unexpected agent failure.

## Configuration reference (`.env`)

| Variable            | Default                                     | Description                                   |
|----------------------|----------------------------------------------|------------------------------------------------|
| `OPENAI_API_KEY`     | *(empty)*                                    | Required to actually call the Planner Agent.   |
| `PLANNER_MODEL`      | `gpt-4o-mini`                                | Model used by the Planner Agent.               |
| `APP_NAME`           | `Autonomous Multi-Agent Research System`     | Shown in `/health`.                            |
| `ENVIRONMENT`        | `development`                                | Shown in `/health`.                            |
| `MAX_TOPIC_LENGTH`   | `300`                                        | Max characters allowed in `topic`.             |
| `MIN_TOPIC_LENGTH`   | `3`                                          | Min characters required in `topic`.            |
| `TAVILY_API_KEY`     | *(empty)*                                    | Required to actually call the Web Researcher Agent. |
| `WEB_SEARCH_MAX_RESULTS` | `5`                                       | Default number of results returned per search. |
| `WEB_SEARCH_TIMEOUT_SECONDS` | `15`                                  | Timeout for the search provider HTTP call.     |
| `LOG_LEVEL`          | `INFO`                                       | Root logger level.                             |

## Out of scope for Phase 3

The following are explicitly **not** implemented yet and belong to later
phases: Academic Researcher, News Agent, Fact Checker, Synthesizer, Report
Generator, Oracle AI Database, Vector Search, MCP, ReAct, Human Approval.
The Web Researcher Agent is also not yet wired up to automatically consume
a full `ResearchPlan` (looping over every `ResearchTask`) — it currently
runs on one task at a time via `/research/web-search`, by design, so it can
be exercised and tested independently first.
