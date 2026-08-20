# Project Structure — What Each Folder/File Is For

```
research-agent-system/
├── app/                        # All application source code lives here
│   ├── __init__.py
│   ├── main.py                 # Application entry point — creates the FastAPI app
│   ├── core/                   # Cross-cutting setup: config, logging (not business logic)
│   │   ├── __init__.py
│   │   ├── config.py           # Loads settings from .env safely (API keys, app settings)
│   │   └── logging_config.py   # Sets up logging so every part of the app logs consistently
│   ├── api/                    # HTTP route definitions (FastAPI routers)
│   │   ├── __init__.py
│   │   └── health.py           # The /health endpoint
│   └── utils/                  # Small reusable helper functions (empty for now, used later)
│       └── __init__.py
├── tests/                      # Automated tests
│   └── test_health.py          # Test that confirms the health endpoint works
├── logs/                       # Log files written at runtime (not committed to git)
│   └── .gitkeep
├── data/                       # Local data storage — will hold SQLite DB from Phase 4 onward
│   └── .gitkeep
├── .env.example                # Template showing which environment variables are needed
├── .env                        # YOUR actual secrets (never committed — see .gitignore)
├── .gitignore                  # Tells git to ignore .env, venv, logs, __pycache__, etc.
├── requirements.txt            # Exact Python packages this project depends on
├── README.md                   # Project overview
├── STRUCTURE.md                # This file
└── PHASE_LOG.md                # What's done in each phase + how to run/test it
```

## Why this structure?

- **`app/` as a package**: keeps all source code separate from config files, tests,
  and data — a standard, examiner-friendly Python project layout.
- **`core/` vs `api/`**: separates *how the app is configured* (settings, logging)
  from *what the app does* (routes/endpoints). This split matters more once agents
  are added in Phase 2 — agent logic will get its own `app/agents/` folder, kept
  separate from the API layer that exposes it to users.
- **`.env` never hardcodes secrets**: your OpenAI API key lives only in `.env`,
  which is excluded from version control. `config.py` reads it at runtime.
- **`logs/` and `data/` are runtime folders**: they hold generated files, not
  source code, so they're kept separate and gitignored (except for `.gitkeep`
  placeholders so the empty folders still exist in git).
- **`tests/` mirrors `app/`**: as you add agents in later phases, you add a
  matching test file — makes it easy to show "yes, this is tested" during
  your viva.
