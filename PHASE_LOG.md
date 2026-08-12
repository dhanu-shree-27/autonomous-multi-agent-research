# Phase Log

## Phase 1 — Project Setup ✅ DONE

### What was built
- Clean, modular folder structure (`app/core`, `app/api`, `app/utils`, `tests`)
- Environment variable handling via `.env` (never hardcoded secrets)
- Centralized `Settings` class that validates config at startup
- Centralized logging (console + `logs/app.log`)
- Minimal FastAPI app with a `/health` endpoint
- Global error handler (returns clean JSON instead of crashing or leaking a traceback)
- One automated test file confirming the server + health endpoint work

### Exact commands

**1. Create and activate a virtual environment**
```bash
cd research-agent-system
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

**2. Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**3. Set up environment variables**
```bash
cp .env.example .env
# then open .env and paste your real OpenAI API key into OPENAI_API_KEY=
```

**4. Run the server**
```bash
uvicorn app.main:app --reload
```
Server will start at: `http://127.0.0.1:8000`

### Testing Phase 1

**A. Automated test**
```bash
python -m pytest tests/ -v
```
Expected: `2 passed`

**B. Manual test (server running)**
```bash
curl http://127.0.0.1:8000/health
```
Expected response:
```json
{
  "status": "ok",
  "app_name": "Autonomous Multi-Agent Research System",
  "environment": "development",
  "config_warnings": []
}
```
If `OPENAI_API_KEY` is missing from `.env`, `config_warnings` will list that
problem — but the server still responds with `status: ok` and HTTP 200,
because the server itself is healthy even if a later phase's dependency
isn't configured yet.

**C. Interactive API docs (FastAPI gives you this for free)**
Open in a browser: `http://127.0.0.1:8000/docs`
You should see the `/health` endpoint listed and be able to try it directly
in the browser — useful for demonstrating the working backend in your viva.

### What is working after Phase 1
- Project runs with a single command
- Config is loaded safely from `.env`, with no secrets in code
- Logging writes to both console and `logs/app.log`
- `/health` endpoint confirms the server and config are working
- Unhandled errors return clean JSON instead of crashing the process
- One passing automated test proves the above, not just "it looked fine when I ran it once"

---

## Phase 2 — Multi-Agent Research (NEXT)

Planned work:
- Add `app/agents/` package
- Implement **Planner Agent**: topic → sub-questions, using OpenAI Agents SDK
- Implement **Researcher Agent**: web search tool → claims + source snippets
- Add a `POST /research` endpoint that accepts a topic and runs Planner → Researcher
- Extend logging so every agent call (input/output/tool used) is traceable
- Add tests for Planner and Researcher independently, using mocked LLM responses so tests don't require a live API key

Phase 2 will NOT yet include: Fact Checker, Synthesizer, Report Generator, or the
sufficiency-check loop — those are Phase 3.
