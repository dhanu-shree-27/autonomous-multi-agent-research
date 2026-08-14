# Autonomous Multi-Agent Research & Report Generator

A multi-phase system that will eventually take a research topic, plan it,
research it across multiple agent types, fact-check it, and synthesize it
into a report. This repository currently implements **Phase 1** (service
health) and **Phase 2** (Planner Agent).

## Status

| Phase | Description                          | Status      |
|-------|---------------------------------------|-------------|
| 1     | App skeleton + `/health`              | ✅ Complete |
| 2     | Planner Agent + `/research/plan`      | ✅ Complete |
| 3+    | Web/Academic/News research, Fact Checker, Synthesizer, Report Generator, Oracle AI DB, Vector Search, MCP, ReAct, Human Approval | ⏳ Not started |

See `PHASE_LOG.md` for a detailed history of what was built in each phase.

## Project structure

```
research_system/
├── app/
│   ├── main.py                 # FastAPI app + router registration
│   ├── config.py               # Env-based settings (pydantic-settings)
│   ├── logging_config.py       # Centralized logging setup
│   ├── models/
│   │   └── research_plan.py    # ResearchPlan / request / response schemas
│   ├── agents/
│   │   └── planner_agent.py    # Planner Agent (OpenAI Agents SDK)
│   └── api/
│       ├── health.py           # GET /health
│       └── research.py         # POST /research/plan
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   └── test_planner.py
├── .env.example                # Template for local .env (never commit .env)
├── requirements.txt
├── README.md
└── PHASE_LOG.md
```

## Prerequisites

- Python 3.11+
- An OpenAI API key with access to the model configured in `PLANNER_MODEL`
  (default `gpt-4o-mini`)

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env and set OPENAI_API_KEY to your real key
```

The API key is **never** hardcoded anywhere in the codebase. It is read
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

`config_warnings` will list issues such as a missing `OPENAI_API_KEY` — the
server still starts, but Planner Agent calls will fail until it's set.

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

## Testing the endpoint via `/docs`

1. Start the server: `uvicorn app.main:app --reload`
2. Open `http://127.0.0.1:8000/docs` in a browser.
3. Expand `POST /research/plan`, click **Try it out**.
4. Enter a request body, e.g.:
   ```json
   { "topic": "Impact of Generative AI on Education" }
   ```
5. Click **Execute** and inspect the response body/status code below.

## Running tests

```bash
pytest -v
```

Tests mock the Planner Agent (`app.api.research.run_planner`), so the full
suite runs **without** a real OpenAI API key or network access, and covers:

- `GET /health` returns `200` with the expected shape.
- `POST /research/plan` returns a well-formed `ResearchPlan` on success.
- Topic whitespace is trimmed.
- Empty, whitespace-only, too-short, too-long, and missing `topic` all
  return `422` with a descriptive `detail` message.
- A missing/invalid OpenAI configuration returns `503`.
- An unexpected Planner Agent failure returns `502`.

## Configuration reference (`.env`)

| Variable            | Default                                     | Description                                   |
|----------------------|----------------------------------------------|------------------------------------------------|
| `OPENAI_API_KEY`     | *(empty)*                                    | Required to actually call the Planner Agent.   |
| `PLANNER_MODEL`      | `gpt-4o-mini`                                | Model used by the Planner Agent.               |
| `APP_NAME`           | `Autonomous Multi-Agent Research System`     | Shown in `/health`.                            |
| `ENVIRONMENT`        | `development`                                | Shown in `/health`.                            |
| `MAX_TOPIC_LENGTH`   | `300`                                        | Max characters allowed in `topic`.             |
| `MIN_TOPIC_LENGTH`   | `3`                                          | Min characters required in `topic`.            |
| `LOG_LEVEL`          | `INFO`                                       | Root logger level.                             |

## Out of scope for Phase 2

The following are explicitly **not** implemented yet and belong to later
phases: Web Researcher, Academic Researcher, News Agent, Fact Checker,
Synthesizer, Report Generator, Oracle AI Database, Vector Search, MCP,
ReAct, Human Approval.
