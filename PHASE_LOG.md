# Phase Log

## Phase 1 — App Skeleton & Health Check ✅

**Goal:** Stand up a minimal, production-structured FastAPI service with a
health endpoint.

**Delivered:**
- FastAPI app skeleton (`app/main.py`).
- Environment-based configuration (`app/config.py`) using
  `pydantic-settings`, backed by `.env` (never hardcoded secrets).
- `GET /health` returning `status`, `app_name`, `environment`, and
  `config_warnings`.

**Verified output:**
```json
{
  "status": "ok",
  "app_name": "Autonomous Multi-Agent Research System",
  "environment": "development",
  "config_warnings": []
}
```

---

## Phase 2 — Planner Agent ✅

**Goal:** Given a research topic, produce a structured research plan via an
LLM-backed Planner Agent.

**Delivered:**
- `app/models/research_plan.py` — Pydantic schema for `ResearchPlan`
  (`topic`, `research_questions`, `subtopics`, `research_tasks`,
  `evidence_requirements`, `recommended_source_types`, `priorities`), plus
  request/response wrapper models.
- `app/agents/planner_agent.py` — modular Planner Agent built with the
  **OpenAI Agents SDK** (`Agent` + `Runner`), using `output_type=ResearchPlan`
  so the SDK enforces structured output validated by Pydantic. Reads the
  model name and API key from settings; never hardcodes the key.
- `app/api/research.py` — `POST /research/plan` endpoint:
  - Validates `topic` is present, non-empty/non-whitespace, and within
    `MIN_TOPIC_LENGTH`–`MAX_TOPIC_LENGTH` bounds, with descriptive error
    messages (`422`).
  - Calls the Planner Agent and maps failures to `503` (missing/invalid
    config) or `502` (any other Planner/OpenAI failure), logging each case.
- Logging: structured, timestamped logging configured centrally
  (`app/logging_config.py`) and used across config load, request handling,
  and agent execution.
- Tests (`tests/test_health.py`, `tests/test_planner.py`): 10 tests covering
  `/health`, successful plan generation (Planner Agent mocked — no network
  or API key needed to run the suite), whitespace trimming, all validation
  error cases, and both `503`/`502` failure paths.
- `README.md` and `.env.example` updated for setup, running, and testing
  instructions.

**Explicitly not implemented (future phases):** Web Researcher, Academic
Researcher, News Agent, Fact Checker, Synthesizer, Report Generator, Oracle
AI Database, Vector Search, MCP, ReAct, Human Approval.

**How it was verified:**
- `pytest -v` → 10/10 passing.
- Manually started `uvicorn app.main:app` and exercised:
  - `GET /health` → `200`, matches Phase 1 shape (plus `config_warnings`
    populated when no key is set).
  - `POST /research/plan` with no `OPENAI_API_KEY` configured → `503` with
    a clear message.
  - `POST /research/plan` with empty / whitespace / too-long `topic` →
    `422` with descriptive messages.
  - `GET /docs` → `200`, Swagger UI renders `POST /research/plan`.

**Completion checklist:**
- [x] `/research/plan` accepts `{"topic": "..."}` and returns a `plan` object
      matching the `ResearchPlan` schema.
- [x] Empty/too-short/too-long topics are rejected with clear `422` errors.
- [x] No API key is hardcoded anywhere; missing key fails gracefully (`503`).
- [x] Planner Agent is isolated in its own module (`app/agents/planner_agent.py`).
- [x] Automated tests pass without requiring a real OpenAI API key.
- [x] README and this log are up to date.

---

## Phase 3 — Web Researcher Agent ✅

**Goal:** Given a single research task, search the web and return
structured, sourced results (title, URL, extracted content, and metadata),
independently of the Planner Agent but ready to be looped over a full
`ResearchPlan` in a later phase.

**Delivered:**
- `app/models/research_result.py` — `SourceMetadata`, `WebSearchResultItem`
  (task, query, source_title, source_url, content, metadata), and
  `WebResearchResult` (task, query, results, success, error), plus
  `WebResearchRequest` / `WebResearchResponse` wrapper models. Deliberately
  kept independent of `app.models.research_plan` so this phase doesn't
  require changes to Phase 2's models.
- `app/services/web_search_service.py` — the web search *tool*: an async
  `search_web()` function that calls the Tavily search API via `httpx`,
  isolated so the provider (endpoint, auth, response shape) can be swapped
  later without touching the agent or API layers. Raises
  `WebSearchConfigError` when `TAVILY_API_KEY` is missing and
  `WebSearchError` for HTTP errors, timeouts, network errors, or malformed
  responses.
- `app/agents/web_researcher.py` — modular Web Researcher Agent
  (`run_web_researcher`). Derives a search query from the task when none is
  given, calls the search tool, and maps raw hits into structured
  `WebSearchResultItem`s (including best-effort domain extraction and
  provider metadata). Configuration errors propagate to the caller (they
  affect every call identically); search/API failures are caught and
  returned as a `WebResearchResult` with `success=False` and a populated
  `error` field instead of raising — graceful degradation, so a batch of
  tasks in a later phase can continue past individual failures.
- `app/api/research.py` — added `POST /research/web-search`:
  - Validates `task` is present and non-empty/non-whitespace, and that
    `query` (if given) isn't whitespace-only, with descriptive `422`
    errors.
  - Calls the Web Researcher Agent and maps a missing/invalid search
    provider configuration to `503`, and any other unexpected failure to
    `502`. Per-search failures surface as `200 OK` with `success: false`
    (see above), not an HTTP error.
- `app/config.py` — added `tavily_api_key`, `web_search_max_results`,
  `web_search_timeout_seconds`; `/health`'s `config_warnings` now also
  flags a missing `TAVILY_API_KEY`.
- Tests (`tests/test_web_researcher.py`, `tests/test_web_search_service.py`):
  18 new tests covering the agent (success, deriving a query from the
  task, graceful degradation on search failure, config-error propagation),
  the search tool (missing key, success, timeout, HTTP error, malformed
  response), and the endpoint (success, explicit query, all validation
  cases, degraded-but-200 response, `503`, `502`). All mock the search
  provider/HTTP layer, so the suite runs without a real Tavily API key or
  network access.
- `README.md`, `.env.example`, and this log updated for Phase 3 setup,
  endpoint docs, and testing instructions.

**Explicitly not implemented (future phases):** Academic Researcher, News
Agent, Fact Checker, Synthesizer, Report Generator, Oracle AI Database,
Vector Search, MCP, ReAct, Human Approval. The Web Researcher is also not
yet wired up to automatically iterate over every task in a `ResearchPlan` —
by design, so it could be built and verified independently first, per the
requirement to keep it modular for that future connection.

**How it was verified:**
- `pytest -v` → 28/28 passing (10 from Phases 1-2 + 18 new).
- Manually started `uvicorn app.main:app` and exercised:
  - `GET /health` → `200`, `config_warnings` lists `TAVILY_API_KEY` when
    unset.
  - `POST /research/web-search` with no `TAVILY_API_KEY` configured →
    `503` with a clear message.
  - `POST /research/web-search` with empty/whitespace `task` → `422`.
  - `GET /docs` → `200`, Swagger UI renders `POST /research/web-search`
    alongside `POST /research/plan`.

**Completion checklist:**
- [x] `app/agents/web_researcher.py` created.
- [x] `app/models/research_result.py` created with the required fields
      (task, query, source title, source URL, content/summary, metadata).
- [x] Web research service/tool created (`app/services/web_search_service.py`).
- [x] `POST /research/web-search` added for independent testing.
- [x] Implementation kept modular for future Planner Agent integration.
- [x] Search/API failures handled gracefully (no crash; structured
      `success`/`error` fields).
- [x] Fact Checker, Academic Researcher, Report Generator, UI, Oracle
      Vector Search, and other later phases are NOT implemented.
- [x] Tests added for the Web Researcher and its API endpoint.
- [x] README and this log are up to date.
- [x] Existing project structure, coding style, configuration pattern, and
      `.env` approach followed (mirrors `planner_agent.py` / `research.py`
      conventions from Phase 2).

---

## Phase 4 — Not started

Reserved for the next research-producing/validating agents (Academic
Researcher, News Agent, Fact Checker) per the project roadmap. Not
implemented in this change.
